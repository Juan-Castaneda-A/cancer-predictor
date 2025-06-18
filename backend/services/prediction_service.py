<<<<<<< HEAD
# prediction_service.py (Este archivo será tu Blueprint)
from flask import Blueprint, request, jsonify, abort
from datetime import datetime
from math import log, exp
from sqlalchemy.orm import Session
from .database import Paciente, Visita, get_db # Importa get_db como un generador

# Define el Blueprint
# Es importante que el nombre del Blueprint sea único, por ejemplo 'predict_bp'
predict_bp = Blueprint('predict_bp', __name__)

# --- CONSTANTES Y VALORES BIBLIOGRÁFICOS ---
UMBRAL_CRITICO_CM3_DEFAULT = 5.0  # cm³
K_GOMPERTZ_DEFAULT = 20.733  # cm³

# Simulación de un código de doctor.
VALID_DOCTOR_CODE = "medico123"

# --- FUNCIONES DE CÁLCULO DE MODELOS ---
# Mantén todas tus funciones de cálculo aquí o impórtalas si están en otro archivo.
# Asegúrate de que los tipos de datos en los parámetros de entrada sean compatibles
# con los datos que Flask extrae del JSON (Python nativo, no Pydantic).

def determine_cancer_stage(tumor_size_cm3: float) -> str:
    # Esta es una simplificación muy gruesa. Los estadios T son complejos.
    if tumor_size_cm3 <= 1.0: # T1a
        return "Etapa T1a (<= 1 cm³)"
    elif 1.0 < tumor_size_cm3 <= 2.0: # T1b
        return "Etapa T1b (> 1 cm³ a 2 cm³)"
    elif 2.0 < tumor_size_cm3 <= 3.0: # T1c o T2
        return "Etapa T1c/T2 (> 2 cm³ a 3 cm³)"
    elif 3.0 < tumor_size_cm3 <= 5.0: # T2
        return "Etapa T2 (> 3 cm³ a 5 cm³)"
    elif tumor_size_cm3 > 5.0: # T3
        return "Etapa T3 (> 5 cm³)"
    return "No clasificable"

def calculate_r_bibliografico(patient_data: dict) -> float: # patient_data ahora es un dict
    r_base = 0.0035

    if patient_data.get("sexo") == "masculino":
        r_base *= 1.1
    
    edad = patient_data.get("edad")
    if edad is not None:
        if edad < 40:
            r_base *= 1.2
        elif edad > 70:
            r_base *= 0.8

    if patient_data.get("grado_histopatologico") == "Grado 3":
        r_base *= 1.5
    elif patient_data.get("grado_histopatologico") == "Grado 1":
        r_base *= 0.7

    if patient_data.get("tipo_cancer") == "Triple Negativo":
        r_base *= 1.8
    elif patient_data.get("tipo_cancer") == "HER2-positivo":
        r_base *= 1.3
    elif patient_data.get("tipo_cancer") == "ER-positivo":
        r_base *= 0.9

    if patient_data.get("metastasis") == "si":
        r_base *= 2.0

    return max(0.0001, r_base)


def calculate_r_from_history_gompertz(T_anterior: float, T_actual: float, time_diff_days: float, K: float) -> float:
    if time_diff_days <= 0:
        raise ValueError("El tiempo transcurrido debe ser positivo para calcular 'r'.")
    if K <= 0:
        raise ValueError("K (Capacidad Máxima) debe ser un valor positivo.")
    if T_anterior <= 0 or T_actual <= 0:
        raise ValueError("Los tamaños del tumor deben ser positivos.")
    if T_anterior >= K or T_actual >= K:
        raise ValueError("Los tamaños del tumor deben ser menores que K para un cálculo Gompertz válido.")
    
    try:
        ln_T_anterior_K = log(T_anterior / K)
        ln_T_actual_K = log(T_actual / K)

        if ln_T_anterior_K == 0:
             raise ValueError("ln(T_anterior/K) es cero, lo que implica T_anterior = K, no válido para cálculo de r.")

        ratio_logs = ln_T_actual_K / ln_T_anterior_K
        
        exponent_rt = log(ratio_logs)
        
        r = -exponent_rt / time_diff_days
        
        return max(0.00001, r)

=======
from models import exponential_model, gompertz_model
import numpy as np

def get_prediction_data(model_type, T0, r, K, T_critical, other_factors):
    """
    Orquesta el cálculo de la predicción y genera los puntos de la curva.
    'other_factors' es un diccionario con 'edad', 'estadio', etc.
    """
    time_estimated = None
    curve_points = []
    lower_bound = None
    upper_bound = None
    model_equation_latex = "" # Para mostrar la ecuación en el frontend

    try:
        # Asumiendo una influencia heurística simple de otros factores en 'r' o 'K'
        # Esto es un placeholder para una lógica más compleja
        adjusted_r = float(r)
        adjusted_K = float(K) if K is not None else None # K puede ser None para exponencial

        if other_factors.get('estadio') == 'IV':
            adjusted_r *= 1.2 # Asumiendo cáncer en etapa IV es más agresivo
        if other_factors.get('metastasis') == 'si':
            adjusted_r *= 1.3 # Mayor agresividad
        if other_factors.get('er_pr') == 'positivo':
            adjusted_r *= 0.8 # Menor agresividad si es positivo y sin metástasis
        if other_factors.get('her2') == 'positivo':
            adjusted_r *= 1.1 # Mayor agresividad si es positivo (puede requerir tratamientos específicos)
        if other_factors.get('edad') and int(other_factors['edad']) > 70:
            adjusted_r *= 0.9 # Podría ser un crecimiento más lento en pacientes mayores

        # Validación básica para evitar cálculos con valores no válidos
        if not (isinstance(T0, (int, float)) and T0 > 0 and
                isinstance(adjusted_r, (int, float)) and adjusted_r > 0 and
                isinstance(T_critical, (int, float)) and T_critical > 0):
            raise ValueError("Parámetros numéricos básicos (T0, r, T_critical) inválidos o no positivos.")


        if model_type == "exponencial":
            time_estimated = exponential_model.calculate_time_to_threshold_exponential(T0, adjusted_r, T_critical)
            curve_points = exponential_model.generate_exponential_curve_points(T0, adjusted_r, max_time_limit=time_estimated * 2)
            lower_bound, upper_bound = exponential_model.calculate_confidence_interval_exponential(time_estimated)
            model_equation_latex = r"T(t) = T_0 \cdot e^{rt}"
            
        elif model_type == "gompertz":
            if adjusted_K is None or not (isinstance(adjusted_K, (int, float)) and adjusted_K > 0):
                raise ValueError("K (Capacidad Máxima) es requerido y debe ser positivo para el modelo de Gompertz.")
            
            # Asegurarse que T0 < T_critical < K para el cálculo de Gompertz sea significativo
            if not (T0 < T_critical < adjusted_K):
                raise ValueError("Para el modelo de Gompertz, se requiere T0 < Umbral Crítico < K (Capacidad Máxima).")

            time_estimated = gompertz_model.calculate_time_to_threshold_gompertz(T0, adjusted_r, adjusted_K, T_critical)
            curve_points = gompertz_model.generate_gompertz_curve_points(T0, adjusted_r, adjusted_K, max_time_limit=time_estimated * 1.5)
            lower_bound, upper_bound = gompertz_model.calculate_confidence_interval_gompertz(time_estimated)
            model_equation_latex = r"T(t) = K \cdot \exp\left( \ln\left(\frac{T_0}{K}\right) \cdot \exp(-rt) \right)"
            
        else:
            raise ValueError("Tipo de modelo no reconocido.")

        # Convertir el tiempo estimado a años si es un valor significativo en días
        # Asumiendo que el cálculo de tiempo_estimated se da en días
        time_unit = "días"
        if time_estimated > 365:
            time_estimated /= 365.25
            lower_bound /= 365.25
            upper_bound /= 365.25
            time_unit = "años"
        
        # Redondear resultados
        time_estimated = round(time_estimated, 2)
        lower_bound = round(lower_bound, 2)
        upper_bound = round(upper_bound, 2)

        return {
            "tiempo_estimado": time_estimated,
            "unidad": time_unit,
            "intervalo_confianza": f"[{lower_bound} - {upper_bound}]",
            "puntos_curva": curve_points,
            "modelo_usado": model_type,
            "ecuacion_latex": model_equation_latex,
            "parametros_usados": {
                "T0": T0,
                "r": adjusted_r,
                "K": adjusted_K,
                "T_critical": T_critical,
                **other_factors # Incluir los otros factores para referencia
            }
        }, 200
>>>>>>> parent of a831574 (fase2)
    except ValueError as e:
        raise ValueError(f"Error calculando r para Gompertz desde el historial: {e}. "
                         "Asegúrese que T_anterior y T_actual sean consistentes con K y el crecimiento.")
    except Exception as e:
<<<<<<< HEAD
        raise Exception(f"Error inesperado en cálculo de r Gompertz: {e}")


def calculate_r_from_history_exponential(T_anterior: float, T_actual: float, time_diff_days: float) -> float:
    if time_diff_days <= 0:
        raise ValueError("El tiempo transcurrido debe ser positivo para calcular 'r'.")
    if T_anterior <= 0:
        raise ValueError("El tamaño del tumor anterior debe ser positivo.")
    if T_actual <= 0:
        raise ValueError("El tamaño del tumor actual debe ser positivo.")
    
    try:
        ratio = T_actual / T_anterior
        if ratio <= 0:
            raise ValueError("La razón T_actual / T_anterior debe ser positiva.")
        
        r = log(ratio) / time_diff_days
        return max(0.00001, r)
    except ValueError as e:
        raise ValueError(f"Error calculando r para Exponencial desde el historial: {e}. "
                         "Asegúrese que T_anterior y T_actual sean positivos.")
    except Exception as e:
        raise Exception(f"Error inesperado en cálculo de r Exponencial: {e}")


def calculate_exponential_time(T0, r, T_umbral):
    if r <= 0:
        return None, "La tasa de crecimiento 'r' debe ser positiva para predecir un tiempo de crecimiento."
    if T0 <= 0:
        return None, "El tamaño inicial del tumor (T0) debe ser positivo."
    if T_umbral <= T0:
        return 0, "El umbral crítico ya fue alcanzado o superado (o es igual al tamaño actual)."
    try:
        time = log(T_umbral / T0) / r
        return time, None
    except Exception as e:
        return None, str(e)

def calculate_gompertz_time(T0, r, K, T_umbral):
    if r <= 0:
        return None, "La tasa de crecimiento 'r' debe ser positiva para predecir un tiempo de crecimiento."
    if K <= 0:
        return None, "La capacidad máxima del tumor (K) debe ser positiva."
    if T0 <= 0:
        return None, "El tamaño inicial del tumor (T0) debe ser positivo."
    if T_umbral <= T0:
        return 0, "El umbral crítico ya fue alcanzado o superado (o es igual al tamaño actual)."
    
    if not (T0 < T_umbral < K):
        return None, f"Para Gompertz, se requiere T_actual ({T0}) < Umbral Crítico ({T_umbral}) < K (Capacidad Máxima ({K}))."

    try:
        ln_T0_K = log(T0 / K)
        ln_Tumbral_K = log(T_umbral / K)

        if ln_T0_K == 0:
            return None, "El tamaño inicial es igual a la capacidad máxima (K), no hay crecimiento esperado."
        
        inner_log_ratio = ln_Tumbral_K / ln_T0_K
        
        if inner_log_ratio <= 0:
             return None, "No se puede calcular el tiempo: el tumor ya es demasiado grande o los parámetros son inconsistentes (inner_log_ratio <= 0)."

        time = - (1 / r) * log(inner_log_ratio)
        
        if time < 0:
            return 0, "El umbral crítico ya fue alcanzado o superado, o el modelo indica un decrecimiento inusual."

        return time, None
    except Exception as e:
        return None, str(e)


def generate_growth_curve(model_type, T0, r, K, T_umbral, total_time_days, steps=100):
    points = []
    
    max_time = total_time_days * 1.5 if total_time_days > 0 else 100 
    if max_time < 100:
        max_time = 100

    time_step = max_time / steps

    for i in range(steps + 1):
        t = i * time_step
        if model_type == 'exponencial':
            T_at_t = T0 * exp(r * t)
        elif model_type == 'gompertz':
            if T0 == K:
                 T_at_t = K
            else:
                T_at_t = K * exp(log(T0 / K) * exp(-r * t))
        else:
            T_at_t = 0

        points.append({"x": t, "y": T_at_t})
    return points

# --- ENDPOINTS ---

@predict_bp.route("/doctor_login", methods=["POST"])
def doctor_login():
    data = request.get_json()
    doctor_code = data.get("doctor_code")

    if doctor_code == VALID_DOCTOR_CODE:
        return jsonify({"message": "Login exitoso", "doctor_logged_in": True})
    abort(401, description="Código de doctor inválido") # Usar abort para HTTP errors

@predict_bp.route("/patients", methods=["GET"])
def get_patients():
    doctor_code = request.args.get("doctor_code") # Obtener de query param
    
    if doctor_code != VALID_DOCTOR_CODE:
        abort(401, description="Código de doctor inválido o no autorizado")
    
    # Usa 'with' para asegurar que la sesión de la base de datos se cierre automáticamente
    with next(get_db()) as db: # get_db ahora es un generador
        patients = db.query(Paciente).filter(Paciente.doctor_code == doctor_code).all()
        
        result = []
        for p in patients:
            last_visit = db.query(Visita).filter(Visita.paciente_id == p.id).order_by(Visita.fecha_visita.desc()).first()
            result.append({
                "id": p.id,
                "identificacion": p.identificacion,
                "nombre_paciente": p.nombre_paciente,
                "last_visit_date": last_visit.fecha_visita.strftime("%Y-%m-%d") if last_visit else None
            })
    return jsonify(result)

@predict_bp.route("/patient_history/<int:patient_id>", methods=["GET"])
def get_patient_history(patient_id: int):
    doctor_code = request.args.get("doctor_code") # Obtener de query param
    
    if doctor_code != VALID_DOCTOR_CODE:
        abort(401, description="Código de doctor inválido o no autorizado")
    
    with next(get_db()) as db:
        patient = db.query(Paciente).filter(Paciente.id == patient_id, Paciente.doctor_code == doctor_code).first()
        if not patient:
            abort(404, description="Paciente no encontrado o no autorizado para este doctor.")
        
        history = []
        for visit in patient.visitas:
            history.append({
                "fecha_visita": visit.fecha_visita.strftime("%Y-%m-%d"),
                "initial_tumor_size_cm3": visit.initial_tumor_size_cm3,
                "tiempo_estimado_dias": visit.tiempo_estimado_dias,
                "r_calculado": visit.r_calculado,
                "model_type": visit.model_type
            })
    return jsonify(history)


@predict_bp.route("/predict", methods=["POST"])
def predict():
    data = request.get_json()
    
    model_type = data.get("model_type")
    patient_data = data.get("patient_data")
    doctor_code = data.get("doctor_code")

    if doctor_code != VALID_DOCTOR_CODE:
        abort(401, description="Código de doctor inválido o no autorizado.")

    # Preparar datos del paciente para guardar/usar
    identificacion = patient_data.get("identificacion")
    nombre_paciente = patient_data.get("nombre_paciente")
    current_visit_date_dt = datetime.strptime(patient_data.get("current_visit_date"), "%Y-%m-%d")
    is_first_visit = patient_data.get("is_first_visit", False) # Default a False si no viene

    with next(get_db()) as db: # Obtener la sesión de la DB
        # 1. Recuperar o crear paciente
        paciente_db = db.query(Paciente).filter(Paciente.identificacion == identificacion, Paciente.doctor_code == doctor_code).first()

        if not paciente_db:
            if not is_first_visit:
                abort(400, description="Este paciente no tiene historial registrado. Debe ser marcado como 'Primera visita'.")
            
            paciente_db = Paciente(
                identificacion=identificacion,
                nombre_paciente=nombre_paciente,
                sexo=patient_data.get("sexo"),
                edad=patient_data.get("edad"),
                doctor_code=doctor_code
            )
            db.add(paciente_db)
            db.flush() # Para que paciente_db.id esté disponible antes de commit

        # 2. Determinar T0 (initial_tumor_size_cm3) y T_anterior (si aplica)
        T0_calculo = patient_data.get("initial_tumor_size_cm3")

        r_calculado = 0.0
        tiempo_estimado = None
        error_message = None
        K_calculado = K_GOMPERTZ_DEFAULT if model_type == 'gompertz' else None # K solo para Gompertz
        t_umbral_critico = UMBRAL_CRITICO_CM3_DEFAULT

        if is_first_visit:
            r_calculado = calculate_r_bibliografico(patient_data)
        else:
            last_visit = db.query(Visita).filter(Visita.paciente_id == paciente_db.id).order_by(Visita.fecha_visita.desc()).first()
            
            if not last_visit:
                abort(400, description="No se encontró historial para este paciente. Marque como 'Primera visita'.")
            
            previous_tumor_size_from_form = patient_data.get("previous_tumor_size_cm3")
            last_visit_date_str = patient_data.get("last_visit_date")

            if previous_tumor_size_from_form is None or last_visit_date_str is None:
                abort(400, description="Para una visita subsecuente, se requieren el tamaño del tumor anterior y la fecha de la última visita.")

            last_visit_date_dt = datetime.strptime(last_visit_date_str, "%Y-%m-%d")
            
            time_diff = (current_visit_date_dt - last_visit_date_dt).days
            if time_diff <= 0:
                abort(400, description="La fecha de la visita actual debe ser posterior a la fecha de la visita anterior.")

            try:
                if model_type == 'exponencial':
                    r_calculado = calculate_r_from_history_exponential(previous_tumor_size_from_form, T0_calculo, time_diff)
                elif model_type == 'gompertz':
                    r_calculado = calculate_r_from_history_gompertz(previous_tumor_size_from_form, T0_calculo, time_diff, K_calculado)
                else:
                    abort(400, description="Tipo de modelo no soportado.")
            except ValueError as e:
                abort(400, description=f"Error al calcular 'r' desde el historial: {e}")
            except Exception as e:
                abort(500, description=f"Error inesperado al calcular 'r': {e}")


        # 3. Realizar la predicción
        if model_type == 'exponencial':
            ecuacion_latex = r"T(t) = T_0 \cdot e^{rt}"
            tiempo_estimado, error_message = calculate_exponential_time(T0_calculo, r_calculado, t_umbral_critico)
        elif model_type == 'gompertz':
            ecuacion_latex = r"T(t) = K \cdot \exp\left( \ln\left(\frac{T_0}{K}\right) \cdot \exp(-rt) \right)"
            tiempo_estimado, error_message = calculate_gompertz_time(T0_calculo, r_calculado, K_calculado, t_umbral_critico)
        else:
            abort(400, description="Tipo de modelo no soportado.")

        if error_message:
            abort(400, description=error_message)

        # 4. Generar curva de crecimiento
        puntos_curva = generate_growth_curve(model_type, T0_calculo, r_calculado, K_calculado, t_umbral_critico, tiempo_estimado)

        # 5. Guardar la visita actual en la base de datos
        new_visit = Visita(
            paciente_id=paciente_db.id,
            fecha_visita=current_visit_date_dt,
            initial_tumor_size_cm3=T0_calculo,
            r_calculado=r_calculado,
            K_calculado=K_calculado,
            T_umbral_critico=t_umbral_critico,
            model_type=model_type,
            tiempo_estimado_dias=tiempo_estimado,
            intervalo_confianza="No disponible", # Placeholder
            fecha_diagnostico=datetime.strptime(patient_data.get("fecha_diagnostico"), "%Y-%m-%d") if patient_data.get("fecha_diagnostico") else None,
            dias_tratamiento=patient_data.get("dias_tratamiento"),
            estadio=patient_data.get("estadio"),
            grado_histopatologico=patient_data.get("grado_histopatologico"),
            er_pr=patient_data.get("er_pr"),
            tipo_cancer=patient_data.get("tipo_cancer"),
            her2=patient_data.get("her2"),
            metastasis=patient_data.get("metastasis")
        )
        db.add(new_visit)
        db.commit() # Realiza el commit para guardar el paciente y la visita
        db.refresh(paciente_db) # Refrescar la relación por si se necesita


    # 6. Preparar la respuesta
    unidad_tiempo = "días"
    intervalo_confianza_str = "No disponible (Implementación futura)"
    
    current_cancer_stage = determine_cancer_stage(T0_calculo)

    interpretacion_resultado = f"""
    Basado en el modelo **{model_type.capitalize()}** y los parámetros calculados (Tasa de crecimiento `r` = {r_calculado:.4f} por día),
    se estima que el tumor alcanzará el umbral crítico de {t_umbral_critico:.2f} cm³ en aproximadamente **{tiempo_estimado:.2f} {unidad_tiempo}**.
    <br><br>
    Este cálculo asume que el tumor continuará creciendo de acuerdo con las dinámicas del modelo seleccionado y que no habrá intervenciones que alteren significativamente su crecimiento.
    En el modelo Gompertz, la tasa de crecimiento disminuye a medida que el tumor se acerca a su capacidad máxima de {K_calculado:.2f} cm³.
    """ if model_type == 'gompertz' else f"""
    Basado en el modelo **{model_type.capitalize()}** y los parámetros calculados (Tasa de crecimiento `r` = {r_calculado:.4f} por día),
    se estima que el tumor alcanzará el umbral crítico de {t_umbral_critico:.2f} cm³ en aproximadamente **{tiempo_estimado:.2f} {unidad_tiempo}**.
    <br><br>
    Este cálculo asume que el tumor continuará creciendo de forma exponencial, con una tasa de crecimiento constante.
    """

    posibles_tratamientos = """
    **Importante:** Esta sección es solo para fines educativos generales y no reemplaza el consejo médico.
    El tratamiento del cáncer de mama es individualizado y depende de múltiples factores como el estadio, subtipo molecular, estado de receptores (ER/PR, HER2), historial médico y preferencias del paciente.
    Las opciones comunes pueden incluir:
    <ul>
        <li>**Cirugía:** Lumpectomía (cirugía conservadora de mama) o Mastectomía (extirpación completa de mama).</li>
        <li>**Radioterapia:** Uso de radiación para destruir células cancerosas.</li>
        <li>**Quimioterapia:** Medicamentos para matar células cancerosas en todo el cuerpo.</li>
        <li>**Terapia Hormonal:** Para cánceres con receptores hormonales positivos (ER+/PR+), bloquea hormonas que alimentan el crecimiento del tumor.</li>
        <li>**Terapia Dirigida:** Fármacos que atacan características específicas de las células cancerosas (ej., terapia anti-HER2).</li>
        <li>**Inmunoterapia:** Ayuda al sistema inmune del cuerpo a combatir el cáncer.</li>
    </ul>
    """
    
    disclaimer_text = """
    **¡ADVERTENCIA MÉDICA IMPORTANTE!**
    Esta herramienta es un **proyecto educativo y de investigación** diseñado para ilustrar la aplicación de modelos matemáticos (ecuaciones diferenciales) al crecimiento tumoral.
    <br><br>
    **NO DEBE UTILIZARSE PARA EL DIAGNÓSTICO, PRONÓSTICO O TRATAMIENTO DE NINGUNA CONDICIÓN MÉDICA.**
    <br><br>
    Las predicciones generadas por este software son **simulaciones teóricas** basadas en parámetros simplificados y no tienen en cuenta la complejidad biológica real del cáncer, la respuesta individual al tratamiento, las comorbilidades del paciente, ni otros factores clínicos cruciales.
    <br><br>
    La información proporcionada **NO SUSTITUYE LA EVALUACIÓN, DIAGNÓSTICO O CONSEJO DE UN PROFESIONAL DE LA SALUD CUALIFICADO.** Siempre consulte a un médico oncólogo o especialista para cualquier decisión relacionada con su salud. El uso de esta herramienta es bajo su propia responsabilidad.
    """

    return jsonify({
        "tiempo_estimado": f"{tiempo_estimado:.2f}",
        "unidad_tiempo": unidad_tiempo,
        "intervalo_confianza": intervalo_confianza_str,
        "estado_cancer_actual_t": current_cancer_stage,
        "interpretacion_resultado": interpretacion_resultado,
        "posibles_tratamientos": posibles_tratamientos,
        "descargo_responsabilidad": disclaimer_text,
        "ecuacion_latex": ecuacion_latex,
        "parametros_usados": {
            "T0_calculo": T0_calculo,
            "r_calculado": r_calculado,
            "K_calculado": K_calculado if model_type == 'gompertz' else "N/A (Modelo Exponencial)",
            "T_umbral_critico": t_umbral_critico,
            "model_type": model_type
        },
        "datos_paciente_enviados": patient_data,
        "puntos_curva": puntos_curva
    })
=======
        return {"error": "Error interno del servidor al calcular la predicción: " + str(e)}, 500
>>>>>>> parent of a831574 (fase2)
