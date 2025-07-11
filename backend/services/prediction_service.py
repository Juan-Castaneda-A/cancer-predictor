from datetime import date
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
import math
import numpy as np

from services.patient_data_manager import PatientDataManager
from config import CANCER_PARAMETERS, CANCER_STAGE_THRESHOLDS_CM3, AGE_THRESHOLDS
from models import exponential_model, gompertz_model

class PredictionService:
    def __init__(self,db_session:Session):
        self.patient_data_manager = PatientDataManager(db_session)
    
    def _calculate_age(self,dob:date) -> int:
        today=date.today()
        return today.year - dob.year - ((today.month,today.day) < (dob.month, dob.day))
    
    def _determine_simplified_cancer_stage(self, tumor_size_cm3:float) -> str:
        for stage, thresholds in CANCER_STAGE_THRESHOLDS_CM3.items():
            if "max_size" in thresholds and tumor_size_cm3 <= thresholds["max_size"]:
                return stage
            if "min_size" in thresholds and tumor_size_cm3 > thresholds["min_size"]:
                if stage == "Etapa IV" and tumor_size_cm3 > thresholds["min_size"]:
                    return stage
                elif stage != "Etapa IV":
                    continue
        return "Desconocida"
    
    def _get_bibliographic_parameters(self, patient_data: Dict[str,Any]) -> Dict[str,float]:
        cancer_type = patient_data.get('tipo_cancer','Cáncer de Mama')
        if cancer_type not in CANCER_PARAMETERS:
            raise ValueError(f"Tipo de cáncer '{cancer_type}' no soportado en los parámetros bibliográficos.")
        
        r_per_day = CANCER_PARAMETERS[cancer_type]["default"]["r_per_day"]
        K_cm3 = CANCER_PARAMETERS[cancer_type]["default"]["K_cm3"]

        subtype = patient_data.get('subtipo_molecular')
        if subtype and subtype in CANCER_PARAMETERS[cancer_type]["Subtipo Molecular"]:
            r_per_day = CANCER_PARAMETERS[cancer_type]["Subtipo Molecular"][subtype]["r_per_day"]
        
        histological_grade = patient_data.get('grado_histopatologico')
        if histological_grade and histological_grade in CANCER_PARAMETERS[cancer_type]["Grado Histopatológico"]:
            r_per_day = CANCER_PARAMETERS[cancer_type]["Grado Histopatológico"][histological_grade]["r_per_day"]

        age = patient_data.get('age')
        if age is not None:
            if age <= AGE_THRESHOLDS["Joven"]:
                r_per_day *= CANCER_PARAMETERS[cancer_type]["Edad del Paciente"]["Joven"]["r_per_day_factor"]
            elif age >= AGE_THRESHOLDS["Mayor"]:
                r_per_day *= CANCER_PARAMETERS[cancer_type]["Edad del Paciente"]["Mayor"]["r_per_day_factor"]
        
        simplified_stage = patient_data.get('simplified_cancer_stage')
        if simplified_stage == 'Etapa IV':
            r_per_day *= 1.2
        
        metastasis = patient_data.get('metastasis')
        if metastasis == 'Si':
            r_per_day *= 1.3
        
        er_pr = patient_data.get('er_pr')
        if er_pr == 'Positivo':
            r_per_day *= 0.8

        her2 = patient_data.get('her2')
        if her2 == 'Positivo':
            r_per_day *= 1.1
        
        return {"r": r_per_day, "K": K_cm3}
    
    def _calculate_empirical_r_exponential(self, T_anterior: float, T_actual: float, time_diff_days: float) -> Optional[float]:
        if time_diff_days <= 0 or T_anterior <= 0 or T_actual <= 0:
            return None
        if T_actual == T_anterior:
            return 0.0
        return math.log(T_actual/T_anterior) / time_diff_days

    def _calculate_empirical_r_gompertz(self, T_anterior: float, T_actual: float, time_diff_days: float, K: float) -> Optional[float]:
        if time_diff_days <= 0 or T_anterior <= 0 or T_actual <= 0 or T_anterior >= K or T_actual >= K:
            return None
        if T_actual == T_anterior:
            return 0.0
        try:
            log_term_actual = math.log(T_actual / K)
            log_term_anterior = math.log(T_anterior / K)
            if log_term_anterior == 0: return None
            ratio = log_term_actual / log_term_anterior
            if ratio <= 0: return None
            inner_log = math.log(ratio)
            r = - (1 / time_diff_days) * inner_log
            return r
        except (ValueError, ZeroDivisionError):
            return None

    def predict(self, identification_number: str, current_tumor_size: float,
                current_measurement_date: date, patient_name: Optional[str]=None,
                date_of_birth: Optional[date]=None,
                other_factors: Dict[str,Any] = None) -> Dict[str,Any]:
        
        if other_factors is None: other_factors={}

        patient = self.patient_data_manager.get_patient_by_identification_number(identification_number)
        
        if not patient:
            if not patient_name or not date_of_birth:
                raise ValueError("El nuevo paciente requiere nombre y fecha de nacimiento.")
            patient = self.patient_data_manager.create_patient(
                identification_number=identification_number, name=patient_name,
                date_of_birth=date_of_birth, initial_tumor_size=current_tumor_size,
                measurement_date=current_measurement_date
            )
        else:
            self.patient_data_manager.add_tumor_measurement(
                patient_id=patient.id, tumor_size=current_tumor_size,
                measurement_date=current_measurement_date
            )
        
        all_measurements = self.patient_data_manager.get_all_tumor_measurements_for_patient(patient.id)

        patient_info = {
            'id': patient.id, 'identification_number': patient.identification_number, 'name': patient.name,
            'date_of_birth': patient.date_of_birth.isoformat(), 'age': self._calculate_age(patient.date_of_birth),
            'current_tumor_size': current_tumor_size, 'current_measurement_date': current_measurement_date.isoformat(),
            **other_factors
        }
        
        simplified_stage = self._determine_simplified_cancer_stage(current_tumor_size)
        patient_info['simplified_cancer_stage'] = simplified_stage
        other_factors['simplified_cancer_stage'] = simplified_stage

        bibliographic_params = self._get_bibliographic_parameters(patient_info)
        r_bibliographic = bibliographic_params["r"]
        K_final = bibliographic_params["K"]
        
        if current_tumor_size >= K_final:
            raise ValueError(f"El tamaño actual del tumor ({current_tumor_size} cm³) es mayor o igual a la capacidad de carga del modelo (K = {K_final:.2f} cm³).")

        r_empirical_exp, r_empirical_gom = None, None
        interpretive_notes = ""
        prediction_status = "ok"

        if len(all_measurements) >= 2:
            previous_measurement = all_measurements[-2]
            T_anterior, date_anterior = previous_measurement.size_cm3, previous_measurement.measurement_date
            time_diff_days = (current_measurement_date - date_anterior).days

            if time_diff_days > 0:
                r_empirical_exp = self._calculate_empirical_r_exponential(T_anterior, current_tumor_size, time_diff_days)
                r_empirical_gom = self._calculate_empirical_r_gompertz(T_anterior, current_tumor_size, time_diff_days, K_final)

        patient_info.update({
            "r_empirical_exp_calculated": r_empirical_exp,
            "r_empirical_gom_calculated": r_empirical_gom
        })

        r_final_exp, r_final_gom = r_bibliographic, r_bibliographic

        if r_empirical_exp is not None and r_empirical_exp < 0:
            prediction_status = "tumor_regressing"
            r_final_exp = r_final_gom = r_empirical_exp
            interpretive_notes = f"¡El tumor está disminuyendo! Se usará la tasa empírica ({r_empirical_exp:.4f})."
        else:
            if r_empirical_exp is not None:
                r_final_exp = r_empirical_exp
                interpretive_notes += "Exponencial: Usando 'r' empírica. "
            else:
                interpretive_notes += "Exponencial: Usando 'r' bibliográfica. "
            if r_empirical_gom is not None:
                r_final_gom = r_empirical_gom
                interpretive_notes += "Gompertz: Usando 'r' empírica."
            else:
                interpretive_notes += "Gompertz: Usando 'r' bibliográfica."

        model_results = {}
        T0_for_models = current_tumor_size
        T_critical_exponential, T_critical_gompertz = K_final, K_final * 0.99

        if prediction_status == "tumor_regressing":
            try:
                model_results["exponential"] = {
                    "prediction_days": None, "unit": "días", "confidence_interval": [None, None], "status": "tumor_regressing",
                    "curve_data": exponential_model.generate_exponential_curve_points(T0_for_models, r_final_exp),
                    "notes": "El tumor está en regresión. No se calcula tiempo a umbral."
                }
            except Exception as e:
                model_results["exponential"] = {"error": f"Error generando curva de regresión: {e}"}
            model_results["gompertz"] = {
                "prediction_days": None, "unit": "días", "confidence_interval": [None, None], "status": "tumor_regressing",
                "curve_data": [], "notes": "El modelo de Gompertz no es aplicable para regresión."
            }
        else:
            try:
                time_exp = exponential_model.calculate_time_to_threshold_exponential(T0_for_models, r_final_exp, T_critical_exponential)
                lower, upper = exponential_model.calculate_confidence_interval_exponential(time_exp)
                unit = "días"
                if time_exp > 365:
                    time_exp, lower, upper, unit = time_exp/365.25, lower/365.25, upper/365.25, "años"
                model_results["exponential"] = {
                    "prediction_days": round(time_exp, 2), "unit": unit, "confidence_interval": [round(lower, 2), round(upper, 2)],
                    "curve_data": exponential_model.generate_exponential_curve_points(T0_for_models, r_final_exp, max_time_limit=time_exp * (365.25 if unit == "años" else 1) * 1.5),
                    "status": "ok"
                }
            except Exception as e:
                model_results["exponential"] = {"error": f"Error en modelo exponencial: {e}", "status": "error"}

            try:
                time_gompertz = gompertz_model.calculate_time_to_threshold_gompertz(T0_for_models, r_final_gom, K_final, T_critical_gompertz)
                lower, upper = gompertz_model.calculate_confidence_interval_gompertz(time_gompertz)
                unit = "días"
                if time_gompertz > 365:
                    time_gompertz, lower, upper, unit = time_gompertz/365.25, lower/365.25, upper/365.25, "años"
                model_results["gompertz"] = {
                    "prediction_days": round(time_gompertz, 2), "unit": unit, "confidence_interval": [round(lower, 2), round(upper, 2)],
                    "curve_data": gompertz_model.generate_gompertz_curve_points(T0_for_models, r_final_gom, K_final, max_time_limit=time_gompertz * (365.25 if unit == "años" else 1) * 1.5),
                    "status": "ok"
                }
            except Exception as e:
                model_results["gompertz"] = {"error": f"Error en modelo Gompertz: {e}", "status": "error"}

        for model in ["exponential", "gompertz"]:
            if model_results.get(model):
                model_results[model]["formula"] = formula_exp if model == "exponential" else formula_gompertz
        
        return {
            "status": prediction_status, "message": interpretive_notes, "patient_info": patient_info,
            "parameters_used_for_prediction": {
                "T0_for_models": T0_for_models, "K_final": K_final, "r_bibliographic_value": r_bibliographic,
                "r_final_exp_used": r_final_exp, "r_final_gom_used": r_final_gom,
                "T_critical_exponential_used": T_critical_exponential, "T_critical_gompertz_used": T_critical_gompertz
            },
            "model_results": model_results
        }