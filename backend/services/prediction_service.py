from models import exponential_model, gompertz_model
import math
from datetime import datetime

# --- Valores Bibliográficos (tomados de tus tablas, ajusta según tu decisión de valores por defecto) ---
# Puedes refinar estos diccionarios para incluir los rangos y la lógica de selección.

# Ejemplo de estructura para Tasa de Crecimiento (r) en días^-1
# Asumo que las keys son strings que coinciden con los inputs del formulario.
BIBLIOGRAPHIC_R_VALUES = {
    "General_Media": 0.0042, # Mediana global de 164 días Td
    "General_Rango_Alto": 0.015, # Corresponde a Td 46 días (crecimiento rápido)
    "General_Rango_Bajo": 0.00084, # Corresponde a Td 825 días (crecimiento lento)
    "Subtipo": {
        "Triple Negativo": 0.0067,
        "HER2-positivo": 0.0043,
        "ER-positivo": 0.0029,
        "No-luminal": 0.0039,
        "Luminal": 0.0014
    },
    "Grado": {
        "Grado 1": 0.0022,
        "Grado 2": 0.0024,
        "Grado 3": 0.0036
    },
    "Edad": {
        "40-60": 0.0041, # Mediana para inicio a los 40
        "60+": 0.0033 # Mediana para inicio a los 60
    }
}

# Valor por defecto de r si no se puede determinar por los factores (ej. "General_Media")
DEFAULT_R_BIBLIOGRAFICO = BIBLIOGRAPHIC_R_VALUES["General_Media"]

# Ejemplo de K para Gompertz (cm^3)
# Usaremos un valor en el rango de modelos matemáticos (0.08 a 11 cm^3)
DEFAULT_K_GOMPERTZ = 5.0 # cm^3. Ajusta este valor si deseas otro dentro del rango.

# Umbral Crítico por defecto (cm^3) para el cálculo del tiempo de vida.
# Como la profesora lo dio de ejemplo, podemos mantener 15 cm^3 o usar algo como 
# el límite superior de los 'volúmenes tumorales observados' de tu tabla.
# Por ejemplo, podemos usar el Tv2 (T=5cm de diámetro) que es 20.733 cm^3
DEFAULT_UMBRAL_CRITICO = 20.733 # cm^3, basado en T=5cm de tu tabla K4 (Tv2)

# --- Funciones Auxiliares ---

def get_bibliographic_r(age=None, grade=None, subtype=None):
    """
    Selecciona un valor de 'r' bibliográfico de las tablas basado en factores.
    Prioridad: Grado > Subtipo > Edad > General.
    """
    if grade and grade in BIBLIOGRAPHIC_R_VALUES["Grado"]:
        return BIBLIOGRAPHIC_R_VALUES["Grado"][grade]
    if subtype and subtype in BIBLIOGRAPHIC_R_VALUES["Subtipo"]:
        return BIBLIOGRAPHIC_R_VALUES["Subtipo"][subtype]
    if age is not None:
        # Lógica simple para edad, puedes expandirla con rangos más específicos
        try:
            age_int = int(age)
            if age_int <= 60:
                return BIBLIOGRAPHIC_R_VALUES["Edad"]["40-60"]
            else:
                return BIBLIOGRAPHIC_R_VALUES["Edad"]["60+"]
        except (ValueError, TypeError):
            pass # Si la edad no es válida, se ignora

    return DEFAULT_R_BIBLIOGRAFICO # Valor por defecto si no se encuentran factores específicos

def calculate_r_from_historical_data(previous_size_cm3, current_size_cm3, time_elapsed_days):
    """
    Calcula la tasa de crecimiento 'r' basada en dos mediciones de tumor.
    previous_size_cm3: Tamaño del tumor en la cita anterior (cm^3)
    current_size_cm3: Tamaño del tumor en la cita actual (cm^3)
    time_elapsed_days: Días transcurridos entre la cita anterior y la actual
    Retorna: Tasa de crecimiento 'r' (días^-1)
    """
    if previous_size_cm3 <= 0 or current_size_cm3 <= 0 or time_elapsed_days <= 0:
        raise ValueError("Datos históricos inválidos: tamaños deben ser > 0 y tiempo transcurrido > 0.")
    
    try:
        r = math.log(current_size_cm3 / previous_size_cm3) / time_elapsed_days
        return r
    except Exception as e:
        raise ValueError(f"Error al recalcular 'r' con datos históricos: {e}")

def determine_cancer_stage_by_size(tumor_size_cm3):
    """
    Determina la etapa 'T' del cáncer de mama según el tamaño del tumor (AJCC simplified).
    Este es un mapeo directo para T1, T2, T3 basado en los diámetros aproximados a volumen.
    T1: <= 2 cm de diámetro (aprox. <= 4.18 cm^3 si es esfera)
    T2: > 2 cm y <= 5 cm de diámetro (aprox. > 4.18 cm^3 y <= 65.4 cm^3)
    T3: > 5 cm de diámetro (aprox. > 65.4 cm^3)
    T4: Cualquier tamaño con extensión a pared torácica/piel (no se puede determinar solo por volumen)
    Retorna: Etapa T (T1, T2, T3) o "Desconocido"
    """
    if tumor_size_cm3 is None or tumor_size_cm3 <= 0:
        return "Desconocido"
    
    # Conversiones aproximadas de diámetro a volumen (asumiendo esfera para simplificar)
    # 2 cm diámetro -> (4/3)*pi*(1)^3 = 4.18 cm^3
    # 5 cm diámetro -> (4/3)*pi*(2.5)^3 = 65.4 cm^3
    
    # Los umbrales de tu tabla K4 (2.056 cm3 para T=2cm, 20.733 cm3 para T=5cm)
    # son más precisos para volumen. Usemos esos.
    if tumor_size_cm3 <= 2.056: # T1: <= 2cm de diámetro
        return "T1"
    elif tumor_size_cm3 <= 20.733: # T2: > 2cm y <= 5cm de diámetro
        return "T2"
    elif tumor_size_cm3 > 20.733: # T3: > 5cm de diámetro
        return "T3"
    else:
        return "Desconocido" # Para casos fuera de rango o T4 (que no es solo por tamaño)


def get_prediction_data(patient_data):
    """
    Orquesta el cálculo de la predicción y genera los puntos de la curva.
    patient_data: Diccionario con todos los datos del formulario (incluye is_first_visit,
                  previous_tumor_size, time_since_previous_visit_days, etc.)
    """
    model_type = patient_data.get('model_type')
    initial_tumor_size_form = patient_data.get('initial_tumor_size_cm3') # Tamaño ingresado en el formulario
    
    # El 'initial_tumor_size' del formulario es el T0 de la primera visita,
    # y el tamaño actual para las visitas subsecuentes.
    # El T0 para la gráfica siempre será el tamaño del tumor en el momento del cálculo.
    T0_for_current_prediction = initial_tumor_size_form 
    
    # Umbral crítico
    T_critical = patient_data.get('umbral_critico_cm3')
    if T_critical is None: T_critical = DEFAULT_UMBRAL_CRITICO
    
    # Capacidad máxima K (solo para Gompertz)
    K_value = patient_data.get('K_value')
    if model_type == 'gompertz' and K_value is None:
        K_value = DEFAULT_K_GOMPERTZ

    # Determinar si es primera visita o subsecuente
    is_first_visit = patient_data.get('is_first_visit', True) # Asume True si no se especifica

    r_value = None
    
    try:
        # Convertir a float y manejar None para los principales parámetros
        initial_tumor_size_form = float(initial_tumor_size_form)
        T_critical = float(T_critical)
        if K_value is not None: K_value = float(K_value)

        # --- Lógica para determinar 'r' ---
        if is_first_visit:
            # Obtener r bibliográfico basado en factores adicionales
            r_value = get_bibliographic_r(
                age=patient_data.get('edad'),
                grade=patient_data.get('grado_histopatologico'), # 'Grado 1', 'Grado 2', 'Grado 3'
                subtype=patient_data.get('tipo_cancer')          # 'Triple Negativo', 'HER2-positivo', etc.
            )
            if r_value is None: # Fallback si get_bibliographic_r no encuentra coincidencia
                r_value = DEFAULT_R_BIBLIOGRAFICO
            
        else:
            # Recalcular 'r' con datos históricos
            previous_tumor_size = patient_data.get('previous_tumor_size_cm3')
            # Las fechas vienen como strings, calcular diferencia en días
            last_visit_date_str = patient_data.get('last_visit_date') # 'YYYY-MM-DD'
            current_visit_date_str = patient_data.get('current_visit_date') # 'YYYY-MM-DD'
            
            if previous_tumor_size is None or last_visit_date_str is None or current_visit_date_str is None:
                raise ValueError("Para visitas subsecuentes, se requieren el tamaño del tumor anterior, la fecha de la última visita y la fecha actual.")
            
            previous_tumor_size = float(previous_tumor_size)
            
            # Calcular tiempo transcurrido en días
            last_visit_date = datetime.strptime(last_visit_date_str, '%Y-%m-%d')
            current_visit_date = datetime.strptime(current_visit_date_str, '%Y-%m-%d')
            time_elapsed_days = (current_visit_date - last_visit_date).days
            
            if time_elapsed_days <= 0:
                raise ValueError("El tiempo transcurrido entre visitas debe ser positivo para recalcular 'r'.")
            
            # Importante: El T0 para el cálculo de 'r' es el tamaño anterior, y T(t) es el tamaño actual.
            # La fórmula es r = ln(T_actual / T_anterior) / tiempo_transcurrido
            r_value = calculate_r_from_historical_data(previous_tumor_size, initial_tumor_size_form, time_elapsed_days)
            
            if r_value is None: # Fallback si el cálculo falla
                r_value = DEFAULT_R_BIBLIOGRAFICO 

        # --- Validaciones finales de parámetros antes de los modelos ---
        if not (initial_tumor_size_form > 0 and r_value > 0 and T_critical > 0):
             raise ValueError("Parámetros (Tamaño inicial/actual, r, Umbral Crítico) deben ser positivos.")
        
        # --- Llamada a los Modelos y Generación de Curvas ---
        time_estimated = None
        curve_points = []
        model_equation_latex = ""
        
        if model_type == "exponencial":
            time_estimated = exponential_model.calculate_time_to_threshold_exponential(
                T_initial=T0_for_current_prediction, # El tamaño actual del tumor para el cálculo de tiempo restante
                r=r_value,
                T_target=T_critical
            )
            # Para la gráfica, el T0 es el tamaño actual del tumor
            curve_points = exponential_model.generate_exponential_curve_points(
                T0_for_graph=T0_for_current_prediction,
                r=r_value,
                max_time_limit=time_estimated * 1.5 if time_estimated > 0 else 365*2 # Extender un poco más allá
            )
            lower_bound, upper_bound = exponential_model.calculate_confidence_interval_exponential(time_estimated)
            model_equation_latex = r"T(t) = T_0 \cdot e^{rt}"
            
        elif model_type == "gompertz":
            if K_value is None or K_value <= 0:
                raise ValueError("K (Capacidad Máxima) es requerido y debe ser positivo para el modelo de Gompertz.")
            
            # Validaciones específicas de Gompertz
            if not (T0_for_current_prediction < T_critical < K_value):
                raise ValueError("Para Gompertz, se requiere T_actual < Umbral Crítico < K (Capacidad Máxima).")

            time_estimated = gompertz_model.calculate_time_to_threshold_gompertz(
                T0=T0_for_current_prediction, # Tamaño actual del tumor
                r=r_value,
                K=K_value,
                T_critical=T_critical
            )
            # Para la gráfica, el T0 es el tamaño actual del tumor
            curve_points = gompertz_model.generate_gompertz_curve_points(
                T0_for_graph=T0_for_current_prediction,
                r=r_value,
                K=K_value,
                max_time_limit=time_estimated * 1.5 if time_estimated > 0 else 365*2 # Extender un poco más allá
            )
            lower_bound, upper_bound = gompertz_model.calculate_confidence_interval_gompertz(time_estimated)
            model_equation_latex = r"T(t) = K \cdot \exp\left( \ln\left(\frac{T_0}{K}\right) \cdot \exp(-rt) \right)"
            
        else:
            raise ValueError("Tipo de modelo no reconocido.")

        # --- Determinación de Etapa y Otras Salidas ---
        current_cancer_stage_t = determine_cancer_stage_by_size(T0_for_current_prediction) # Etapa basada en el tamaño actual
        
        # Unidades de tiempo
        time_unit = "días"
        if time_estimated is not None and time_estimated > 365:
            time_estimated /= 365.25
            if lower_bound is not None: lower_bound /= 365.25
            if upper_bound is not None: upper_bound /= 365.25
            time_unit = "años"
        
        # Redondear para presentación
        if time_estimated is not None: time_estimated = round(time_estimated, 2)
        if lower_bound is not None: lower_bound = round(lower_bound, 2)
        if upper_bound is not None: upper_bound = round(upper_bound, 2)
        if r_value is not None: r_value = round(r_value, 5) # Más precisión para r
        if K_value is not None: K_value = round(K_value, 2)

        # --- Interpretación y Tratamientos ---
        # Estos son placeholders, deberás expandirlos con lógica más rica y bibliografía
        interpretation = "Este modelo proporciona una estimación de crecimiento tumoral basada en los parámetros actuales. Es crucial recordar que es una simplificación y no considera todas las complejidades biológicas ni la respuesta a tratamientos."
        
        possible_treatments = "Los tratamientos pueden incluir cirugía, quimioterapia, radioterapia, terapia hormonal o terapia dirigida, dependiendo de la etapa, tipo de tumor, estado de receptores (ER/PR/HER2) y metástasis. Consulte siempre a un especialista."
        if current_cancer_stage_t == "T1":
            interpretation += " El tumor es pequeño y tiene un pronóstico generalmente favorable."
            possible_treatments = "Cirugía y/o radioterapia. Consideración de quimioterapia/terapia hormonal según factores adicionales."
        elif current_cancer_stage_t == "T2":
            interpretation += " El tumor es de tamaño intermedio."
            possible_treatments = "Cirugía, radioterapia, quimioterapia y/o terapia hormonal/dirigida."
        elif current_cancer_stage_t == "T3":
            interpretation += " El tumor es más grande."
            possible_treatments = "Quimioterapia neoadyuvante (antes de cirugía), cirugía, radioterapia y terapias adyuvantes."
        elif patient_data.get('metastasis') == 'si':
             interpretation += " Se ha detectado metástasis, indicando una enfermedad más avanzada."
             possible_treatments = "El tratamiento se enfoca en controlar la enfermedad sistémica, incluyendo quimioterapia, terapia hormonal, terapia dirigida o inmunoterapia."


        # --- Retornar Resultados ---
        return {
            "tiempo_estimado": time_estimated,
            "unidad_tiempo": time_unit,
            "intervalo_confianza": f"[{lower_bound} - {upper_bound}]" if lower_bound is not None else "N/A",
            "puntos_curva": curve_points,
            "modelo_usado": model_type,
            "ecuacion_latex": model_equation_latex,
            "parametros_usados": {
                "T0_calculo": initial_tumor_size_form, # Este es el 'T0' para el cálculo de tiempo
                "r_valor": r_value,
                "K_valor": K_value if model_type == "gompertz" else None,
                "T_umbral_critico": T_critical,
                "tipo_visita": "Primera" if is_first_visit else "Subsecuente"
            },
            "datos_paciente_enviados": { # Incluir los datos completos enviados para referencia
                "nombre": patient_data.get('nombre_paciente'),
                "id": patient_data.get('identificacion'),
                "sexo": patient_data.get('sexo'),
                "edad": patient_data.get('edad'),
                "fecha_diagnostico": patient_data.get('fecha_diagnostico'),
                "current_visit_date": patient_data.get('current_visit_date'),
                "is_first_visit": is_first_visit,
                "previous_tumor_size_cm3": patient_data.get('previous_tumor_size_cm3'),
                "last_visit_date": patient_data.get('last_visit_date'),
                "dias_tratamiento": patient_data.get('dias_tratamiento'),
                "estadio": patient_data.get('estadio'),
                "er_pr": patient_data.get('er_pr'),
                "tipo_cancer": patient_data.get('tipo_cancer'),
                "her2": patient_data.get('her2'),
                "metastasis": patient_data.get('metastasis')
            },
            "estado_cancer_actual_t": current_cancer_stage_t,
            "interpretacion_resultado": interpretation,
            "posibles_tratamientos": possible_treatments,
            "descargo_responsabilidad": "Este sistema es una herramienta educativa y de apoyo a la decisión, y no debe interpretarse como consejo médico profesional. Las predicciones son estimaciones basadas en modelos matemáticos simplificados y parámetros bibliográficos, y no consideran la complejidad individual de cada caso."
        }, 200

    except ValueError as e:
        return {"error": str(e)}, 400
    except Exception as e:
        return {"error": f"Error interno del servidor al procesar la predicción: {e}"}, 500