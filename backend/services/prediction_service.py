from datetime import date
from typing import Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
import math # Para ln (logaritmo natural)
import numpy as np # Para los intervalos de confianza o cualquier otra operación numérica

from services.patient_data_manager import PatientDataManager
from config import CANCER_PARAMETERS, CANCER_STAGE_THRESHOLDS_CM3, AGE_THRESHOLDS

# --- Importaciones de tus modelos existentes ---
from models import exponential_model, gompertz_model

class PredictionService:
    def __init__(self,db_session:Session):
        self.patient_data_manager = PatientDataManager(db_session)
    
    def _calculate_age(self,dob:date) -> int:
        """Calcula la edad a partir de la fecha de nacimiento."""
        today=date.today()
        return today.year - dob.year - ((today.month,today.day) < (dob.month, dob.day))
    
    def _determine_simplified_cancer_stage(self, tumor_size_cm3:float) -> str:
        """
        Determina una etapa simplificada del cáncer basada úncamente en el tamaño del tumor.
        ¡ADVERTENCIA!: Esto es una gran simplificación y no reemplaza la estadificación clínica
        """
        for stage, thresholds in CANCER_STAGE_THRESHOLDS_CM3.items():
            if "max_size" in thresholds and tumor_size_cm3 <= thresholds["max_size"]:
                return stage
            if "min_size" in thresholds and tumor_size_cm3 > thresholds["min_size"]:
                #Maneja el caso de Etapa IV con min_size, asegurando que se aplique si el tamaño es mayor.
                if stage == "Etapa IV" and tumor_size_cm3 > thresholds["min_size"]:
                    return stage
                elif stage != "Etapa IV": #Para otras etapas, solo aplica si es menor o igual al max_size
                    continue
        return "Desconocida" #Si el tamaño no cae en ningún umbral
    
    def _get_bibliographic_parameters(self, patient_data: Dict[str,Any]) -> Dict[str,float]:
        """
        Selecciona la r y K bibliográficas más apropiadas basadas en los factores del paciente.
        """
        cancer_type = patient_data.get('tipo_cancer','Cáncer de Mama') #Asume Cáncer de Mama si no se especifica
        #Validar si el tipo de cáncer existe en nuestros parámetros
        if cancer_type not in CANCER_PARAMETERS:
            #Puedes levantar un error o usar un default genérico
            raise ValueError(f"Tipo de cáncer '{cancer_type}' no soportado en los parámetros bibliográficos.")
        
        #Obtener los parámetros base por defecto para el tipo de cáncer
        r_per_day = CANCER_PARAMETERS[cancer_type]["default"]["r_per_day"]
        K_cm3 = CANCER_PARAMETERS[cancer_type]["default"]["K_cm3"]

        #Aplicar ajustes basados en subtipo molecular
        subtype = patient_data.get('subtipo_molecular')
        if subtype and subtype in CANCER_PARAMETERS[cancer_type]["Subtipo Molecular"]:
            r_per_day = CANCER_PARAMETERS[cancer_type]["Subtipo Molecular"][subtype]["r_per_day"]
        
        #Aplicar ajustes basados en grado hispatológico
        histological_grade = patient_data.get('grado_histopatologico')
        if histological_grade and histological_grade in CANCER_PARAMETERS[cancer_type]["Grado Histopatológico"]:
            r_per_day = CANCER_PARAMETERS[cancer_type]["Grado Histopatológico"][histological_grade]["r_per_day"]

        #Aplicar ajustes basados en la edad
        age = patient_data.get('age') #Asume que la edad ya fue calculada y añadida aquí
        if age is not None:
            if age <= AGE_THRESHOLDS["Joven"]:
                r_per_day *= CANCER_PARAMETERS[cancer_type]["Edad del Paciente"]["Joven"]["r_per_day_factor"]
            elif age >= AGE_THRESHOLDS["Mayor"]:
                r_per_day *= CANCER_PARAMETERS[cancer_type]["Edad del Paciente"]["Mayor"]["r_per_day_factor"]
        
        # --- Lógica de ajuste adicional que tenías en tu 'get_prediction_data' ---
        #En vez de usar estadio de other_factors (de la versión 1), se mapeará de 'simplified_cancer_stage'
        simplified_stage = patient_data.get('simplified_cancer_stage')
        if simplified_stage == 'Etapa IV': #Asumiendo cáncer de etapa IV es más agresivo
            r_per_day *= 1.2
        
        #Ajuste por metástasis
        metastasis = patient_data.get('metastasis')
        if metastasis == 'Si': #Utiliza 'si' para el valor del factor
            r_per_day *= 1.3
        
        #Ajuste por ER/PR (receptor de estrógeno/progesterona)
        er_pr = patient_data.get('er_pr')
        if er_pr == 'Positivo': #Utilizado 'positivo' para el valor del factor
            r_per_day *= 0.8 #Menor agresividad

        #Ajuste por HER2
        her2 = patient_data.get('her2')
        if her2 == 'Positivo': #Utiliza 'Positivo' para el valor del factor
            r_per_day *= 1.1 #Mayor agresividad
        
        return {"r": r_per_day, "K": K_cm3}
    
    def _calculate_empirical_r(self, T_anterior: float, T_actual: float, time_diff_days: float) -> float:
        """
        Calcula la tasa de crecimiento "r" empírica para el modelo exponencial entre dos mediciones.
        Retorna un valor negativo si el tumor disminuye.
        """
        T_anterior = float(T_anterior)
        T_actual = float(T_actual)
        time_diff_days = float(time_diff_days)  # Conversión crítica
        if time_diff_days <= 0:
            raise ValueError("El tiempo de diferencia tiene que ser positivo para calcular el 'r' empírico.")
        if T_anterior <= 0 or T_actual <= 0:
            raise ValueError("Los tamaños de los tumores deben ser positivos para el cálculo del 'r' empírico.")
        
        #Para evitar log(0) o log de número negativo si hay regresión o valores muy pequeños
        #Si T_actual es 0, significa que el tumor desapareció, lo cual no es una regresión total
        #Si T_actual es menor que T_anterior (regresión), ln(T_actual/T_anterior) será negativo.
        if T_actual == 0: #Consideramos regresión total
            return -1.0 #Un valor representativo de regresión fuerte. Ajustar según necesidad.
        
        return math.log(T_actual/T_anterior)/time_diff_days

    def predict(self, identification_number: str, current_tumor_size: float,
                current_measurement_date: date, patient_name: Optional[str]=None,
                date_of_birth: Optional[date]=None,T_critical: float = 10.0,
                other_factors: Dict[str,Any] = None) -> Dict[str,Any]:
        if other_factors is None:
            other_factors={}

        patient = self.patient_data_manager.get_patient_by_identification_number(identification_number)
        patient_info = {} #Información del paciente para la respuesta
        #Inicializamos los parámetros que se usarán para la predicción
        T0_for_models = current_tumor_size #El tamaño actual del tumor para la proyección
        r_final = None
        K_final = None
        prediction_status = "ok"
        interpretive_notes = ""

        # --- Lógica de gestión de pacientes y obtención del historial ---
        if not patient:
            #Nuevo paciente: crea el registro
            if not patient_name or not date_of_birth:
                raise ValueError("El nuevo paciente requiere nombre y fecha de nacimiento.")

            patient = self.patient_data_manager.create_patient(
                identification_number=identification_number,
                name=patient_name,
                date_of_birth=date_of_birth,
                initial_tumor_size=current_tumor_size,
                measurement_date=current_measurement_date
            ) 
            patient_info['is_new_patient'] = True
        else:
            #Paciente existente: añade nueva medición
            self.patient_data_manager.add_tumor_measurement(
                patient_id = patient.id,
                tumor_size=current_tumor_size,
                measurement_date=current_measurement_date
            )
            patient_info['is_new_patient'] = False
        
        #Cargar todos los datos del paciente y sus mediciones para determinar la 'r'
        #Esto asegura que siempre trabajemos con el historial completo y ordenado
        all_measurements = self.patient_data_manager.get_all_tumor_measurements_for_patient(patient.id)

        # --- Preparar datos del paciente para la lógica de selección de parámetros ---
        patient_info['id'] = patient.id
        patient_info['identification_number'] = patient.identification_number
        patient_info['name'] = patient.name
        patient_info['date_of_birth'] = patient.date_of_birth.isoformat()
        patient_info['age'] = self._calculate_age(patient.date_of_birth)
        patient_info['current_tumor_size'] = current_tumor_size
        patient_info['current_measurement_date'] = current_measurement_date.isoformat()
        patient_info.update(other_factors) # Añade los factores opcionales (tipo_cancer, er_pr, etc.)

        # Determinar etapa simplificada (basado en el tamaño actual)
        simplified_stage = self._determine_simplified_cancer_stage(current_tumor_size)
        patient_info['simplified_cancer_stage'] = simplified_stage

        # Pasar la etapa simplificada a other_factors para _get_bibliographic_parameters si es necesario
        other_factors['simplified_cancer_stage'] = simplified_stage

        # Obtener r y K bibliográficas
        bibliographic_params = self._get_bibliographic_parameters(patient_info) # Pasamos patient_info que tiene todos los datos
        r_bibliographic = bibliographic_params["r"]
        K_bibliographic = bibliographic_params["K"]

        # --- Cálculo y Priorización de 'r' (Empírica vs. Bibliográfica) ---
        r_empirical = None
        if len(all_measurements) >= 2:
            #Aseguramos que la penúltima medición es anterior a la última
            previous_measurement = all_measurements[-2]
            T_anterior = previous_measurement.size_cm3
            date_anterior = previous_measurement.measurement_date

            time_diff_days = (current_measurement_date - date_anterior).days

            patient_info["previous_tumor_size"] = T_anterior
            patient_info["previous_measurement_date"] = date_anterior.isoformat()
            patient_info["time_diff_days_for_r_calc"] = time_diff_days

            if time_diff_days > 0 and T_anterior > 0:
                try:
                    r_empirical = self._calculate_empirical_r(T_anterior, current_tumor_size, time_diff_days)
                    patient_info["r_empirical_calculated"] = r_empirical
                except ValueError as ve:
                    patient_info["r_empirical_calc_error"] = str(ve)
                    interpretive_notes += "No se pudo calcular 'r' empírica debido a datos inválidos (ej. tiempo <= 0 o tamaño <= 0)."
            else:
                interpretive_notes += "No se pudo calcular 'r' empírica debido a una diferencia de tiempo no positiva o tamaño anterior inválido."
        else:
            interpretive_notes += "No hay suficientes mediciones previas para calcular 'r' empírica. Se utilizará la 'r' bibliográfica."
        
        #Determinar la 'r' final a usar: priorizar empírica si es válida y positiva
        if r_empirical is not None:
            if r_empirical < 0:
                prediction_status = "tumor_regressing"
                interpretive_notes += f"¡El tumor está disminuyendo! Tasa de cambio empírica: {r_empirical:.4f} (por día). No se realizarán predicciones de tiempo a umbral."
                r_final = r_empirical # Aún necesitamos este valor para la información de la curva si la mostramos
            else:
                r_final = r_empirical
                interpretive_notes += f"Utilizando tasa de crecimiento empírica (r={r_final:.4f} por día). "
        else:
            r_final = r_bibliographic
            interpretive_notes += f"Utilizando tasa de crecimiento bibliográfica (r={r_final:.4f} por día) debido a la falta de datos empíricos o un cálculo inválido. "

        K_final = K_bibliographic #Por ahora, K siempre es bibliográfica

        # ---Lógica de Predicción de Modelos (de tu antigua get_prediction_data) ---
        model_results = {}

        # Define las fórmulas LaTeX para cada modelo
        formula_exp = r"T(t) = T_0 \cdot e^{rt}"
        formula_gompertz = r"T(t) = K \cdot \exp\left( \ln\left(\frac{T_0}{K}\right) \cdot \exp(-rt) \right)"

        #Si el tumor está regresando, no calculamos tiempo a umbral positivo
        if prediction_status == "tumor_regressing":
            # Aún podemos generar una curva si queremos visualizar la regresión,
            # pero el 'tiempo_estimado' no será relevante para un umbral creciente.
            # Podemos poner 0 o null y ajustar el frontend para manejarlo.
            # Modelo Exponencial para regresión
            try:
                curve_exp = exponential_model.generate_exponential_curve_points(T0_for_models, r_final, max_time_limit=365*2) # Ejemplo: 2 años
                model_results["exponential"] = {
                    "prediction_days": None,
                    "unit": "días",
                    "confidence_interval": [None, None],
                    "curve_data": curve_exp,
                    "formula": formula_exp,
                    "status": prediction_status,
                    "notes": "El tumor está en regresión, no se calcula tiempo a umbral de crecimiento positivo."
                }
            except Exception as e:
                model_results["exponential"] = {"error": f"Error generando curva exponencial para regresión: {e}", "status": "error"}

            # Modelo Gompertz para regresión (puede que no sea adecuado)
            model_results["gompertz"] = {
                "prediction_days": None,
                "unit": "días",
                "confidence_interval": [None, None],
                "curve_data": [], # Generalmente no se aplica para regresión sin K < T0
                "formula": formula_gompertz,
                "status": prediction_status,
                "notes": "El tumor está en regresión. El modelo de Gompertz puede no ser aplicable o no se calcula para este escenario."
            }
        else: # Si el tumor NO está regresando (r_final >= 0)
            # --- Modelo Exponencial ---
            try:
                time_exp = exponential_model.calculate_time_to_threshold_exponential(T0_for_models, r_final, T_critical)
                curve_exp = exponential_model.generate_exponential_curve_points(T0_for_models, r_final, max_time_limit=time_exp * 2 if time_exp else 365*5)
                lower_exp, upper_exp = exponential_model.calculate_confidence_interval_exponential(time_exp)

                time_unit_exp = "días"
                if time_exp is not None and time_exp > 365:
                    time_exp /= 365.25
                    lower_exp /= 365.25
                    upper_exp /= 365.25
                    time_unit_exp = "años"

                model_results["exponential"] = {
                    "prediction_days": round(time_exp, 2) if time_exp is not None else None,
                    "unit": time_unit_exp,
                    "confidence_interval": [round(lower_exp, 2) if lower_exp is not None else None, round(upper_exp, 2) if upper_exp is not None else None],
                    "curve_data": curve_exp,
                    "formula": formula_exp,
                    "status": "ok"
                }
            except ValueError as ve:
                model_results["exponential"] = {"error": str(ve), "status": "error"}
            except Exception as e:
                model_results["exponential"] = {"error": f"Error inesperado en modelo exponencial: {e}", "status": "error"}

            # --- Modelo de Gompertz ---
            try:
                if not (T0_for_models < T_critical < K_final):
                    raise ValueError(f"Para Gompertz, se requiere T0 ({T0_for_models:.2f}) < Umbral Crítico ({T_critical:.2f}) < K ({K_final:.2f}).")

                time_gompertz = gompertz_model.calculate_time_to_threshold_gompertz(T0_for_models, r_final, K_final, T_critical)
                curve_gompertz = gompertz_model.generate_gompertz_curve_points(T0_for_models, r_final, K_final, max_time_limit=time_gompertz * 1.5 if time_gompertz else 365*5)
                lower_gompertz, upper_gompertz = gompertz_model.calculate_confidence_interval_gompertz(time_gompertz)

                time_unit_gompertz = "días"
                if time_gompertz is not None and time_gompertz > 365:
                    time_gompertz /= 365.25
                    lower_gompertz /= 365.25
                    upper_gompertz /= 365.25
                    time_unit_gompertz = "años"

                model_results["gompertz"] = {
                    "prediction_days": round(time_gompertz, 2) if time_gompertz is not None else None,
                    "unit": time_unit_gompertz,
                    "confidence_interval": [round(lower_gompertz, 2) if lower_gompertz is not None else None, round(upper_gompertz, 2) if upper_gompertz is not None else None],
                    "curve_data": curve_gompertz,
                    "formula": formula_gompertz,
                    "status": "ok"
                }
            except ValueError as ve:
                model_results["gompertz"] = {"error": str(ve), "status": "error"}
            except Exception as e:
                model_results["gompertz"] = {"error": f"Error inesperado en modelo Gompertz: {e}", "status": "error"}

        #--- Construcción de la respuesta final ---
        response_data = {
            "status": prediction_status, # "ok", "tumor_regressing"
            "message": interpretive_notes, # Mensajes para el usuario (información sobre r, regresión, etc.)
            "patient_info": patient_info, # Detalles del paciente, edad, etapa simplificada, etc.
            "parameters_used_for_prediction": {
                "T0_for_models": T0_for_models,
                "r_final": r_final,
                "K_final": K_final,
                "T_critical": T_critical,
                "r_bibliographic_value": r_bibliographic, # Añadir para transparencia
                "K_bibliographic_value": K_bibliographic, # Añadir para transparencia
                "r_empirical_calculated": patient_info.get("r_empirical_calculated") # Re-incluir si existe
            },
            "model_results": model_results # Contiene los resultados de ambos modelos
        }
        return response_data
    
#tipo