# prediction_service.py
# (Asegúrate de que tus otras funciones de cálculo, como calculate_exponential_time, calculate_gompertz_time, etc., estén en este archivo o importadas correctamente)

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from math import log, exp
from fastapi.middleware.cors import CORSMiddleware

# Importa las clases de base de datos
from .database import Paciente, Visita, get_db, SessionLocal, Base, engine # Asegúrate de que database.py esté en la misma carpeta
from sqlalchemy.orm import Session

app = FastAPI()

# Configuración de CORS
origins = [
    "http://localhost",
    "http://localhost:8080",
    "http://localhost:5500", # Típico para Live Server de VS Code
    "https://cancer-predictor-ed.onrender.com", # Si ya tienes un frontend desplegado aquí
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Permitir todos los orígenes por ahora para pruebas, luego especificar
    allow_credentials=True,
    allow_methods=["*"], # Permitir todos los métodos (GET, POST, etc.)
    allow_headers=["*"], # Permitir todas las cabeceras
)

# --- MODELOS Pydantic para Request/Response ---

class PatientData(BaseModel):
    identificacion: str
    nombre_paciente: str
    sexo: Optional[str] = None
    edad: Optional[int] = None
    current_visit_date: str # Se asume formato 'YYYY-MM-DD'
    is_first_visit: bool
    initial_tumor_size_cm3: float
    # Campos para visitas subsecuentes (opcionales)
    previous_tumor_size_cm3: Optional[float] = None
    last_visit_date: Optional[str] = None
    # Factores clínicos adicionales (todos opcionales ahora)
    fecha_diagnostico: Optional[str] = None
    dias_tratamiento: Optional[int] = None
    estadio: Optional[str] = None
    grado_histopatologico: Optional[str] = None
    er_pr: Optional[str] = None
    tipo_cancer: Optional[str] = None
    her2: Optional[str] = None
    metastasis: Optional[str] = None

class PredictionRequest(BaseModel):
    model_type: str
    patient_data: PatientData
    doctor_code: str # Nuevo campo para el código del doctor

class PredictionResponse(BaseModel):
    tiempo_estimado: str
    unidad_tiempo: str
    intervalo_confianza: str
    estado_cancer_actual_t: str
    interpretacion_resultado: str
    posibles_tratamientos: str
    descargo_responsabilidad: str
    ecuacion_latex: str
    parametros_usados: dict
    datos_paciente_enviados: dict
    puntos_curva: List[dict] # [{x: tiempo, y: tamaño}]

class DoctorLoginRequest(BaseModel):
    doctor_code: str

class PatientListItem(BaseModel):
    id: int
    identificacion: str
    nombre_paciente: str
    last_visit_date: Optional[str] # Para mostrar en la lista

class PatientHistoryItem(BaseModel):
    fecha_visita: str
    initial_tumor_size_cm3: float
    tiempo_estimado_dias: Optional[float]
    r_calculado: float
    model_type: str

# --- CONSTANTES Y VALORES BIBLIOGRÁFICOS ---
UMBRAL_CRITICO_CM3_DEFAULT = 5.0  # cm³
K_GOMPERTZ_DEFAULT = 20.733  # cm³

# Simulación de un código de doctor. En un sistema real, sería autenticación robusta.
VALID_DOCTOR_CODE = "medico123"

# --- FUNCIONES DE CÁLCULO DE MODELOS ---

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


def calculate_r_bibliografico(patient_data: PatientData) -> float:
    # Esta es una función de EJEMPLO.
    # En un sistema real, esto requeriría una base de datos de investigación
    # y modelos estadísticos complejos para correlacionar factores con 'r'.

    r_base = 0.0035 # Un valor base por defecto para 'r' en días (ej. 0.35% de crecimiento diario)

    # Ajustes basados en factores clínicos (EJEMPLOS SIMPLIFICADOS)
    if patient_data.sexo == "masculino":
        r_base *= 1.1 # Crecimiento ligeramente más rápido para hombres (hipotético)
    
    if patient_data.edad:
        if patient_data.edad < 40:
            r_base *= 1.2 # Más agresivo en jóvenes
        elif patient_data.edad > 70:
            r_base *= 0.8 # Menos agresivo en mayores

    if patient_data.grado_histopatologico == "Grado 3":
        r_base *= 1.5 # Grado alto, más agresivo
    elif patient_data.grado_histopatologico == "Grado 1":
        r_base *= 0.7 # Grado bajo, menos agresivo

    if patient_data.tipo_cancer == "Triple Negativo":
        r_base *= 1.8 # Típicamente más agresivo
    elif patient_data.tipo_cancer == "HER2-positivo":
        r_base *= 1.3
    elif patient_data.tipo_cancer == "ER-positivo":
        r_base *= 0.9 # Típicamente menos agresivo

    if patient_data.metastasis == "si":
        r_base *= 2.0 # Metástasis, muy agresivo

    # Asegurar que r no sea negativo o cero
    return max(0.0001, r_base) # r debe ser positivo


def calculate_r_from_history_gompertz(T_anterior: float, T_actual: float, time_diff_days: float, K: float) -> float:
    # Calcula 'r' usando la fórmula de Gompertz basada en dos puntos históricos.
    if time_diff_days <= 0:
        raise ValueError("El tiempo transcurrido debe ser positivo para calcular 'r'.")
    if K <= 0:
        raise ValueError("K (Capacidad Máxima) debe ser un valor positivo.")
    if T_anterior <= 0 or T_actual <= 0:
        raise ValueError("Los tamaños del tumor deben ser positivos.")
    if T_anterior >= K or T_actual >= K:
        # Esto indica que el tumor ya ha superado o alcanzado K, lo que no es típico
        # para un crecimiento gompertziano ascendente o el modelo se rompe.
        # Podría necesitar un manejo especial o indicar un r muy bajo/cercano a 0.
        raise ValueError("Los tamaños del tumor deben ser menores que K para un cálculo Gompertz válido.")
    
    try:
        ln_T_anterior_K = log(T_anterior / K)
        ln_T_actual_K = log(T_actual / K)

        if ln_T_anterior_K == 0: # Evitar división por cero, aunque esto implicaría T_anterior = K
             raise ValueError("ln(T_anterior/K) es cero, lo que implica T_anterior = K, no válido para cálculo de r.")

        ratio_logs = ln_T_actual_K / ln_T_anterior_K

        # Si el tumor creció, el ratio debe ser menor a 1 (e.g. ln(T_actual/K) es menos negativo que ln(T_anterior/K))
        # Esto se cumple porque T_actual > T_anterior, y ambas T son < K, entonces T/K < 1, ln(T/K) es negativo.
        # Si T_actual > T_anterior, entonces ln(T_actual/K) > ln(T_anterior/K) (ambos negativos),
        # por lo tanto la división de negativos será un valor entre 0 y 1 si T_actual < T_anterior,
        # o un valor > 1 si T_actual > T_anterior (pero ln(T_actual/K) está más cerca de 0).
        # Un crecimiento normal significa que ratio_logs > 0 y si esta entre 0 y 1, el ln siguiente será negativo
        
        # Para que ln(ratio_logs) sea válido, ratio_logs debe ser > 0.
        # Si T_actual > T_anterior (crecimiento), y ambos < K, entonces ln(T_actual/K) es "menos negativo" que ln(T_anterior/K).
        # La división de dos números negativos, donde el numerador es "menos negativo" que el denominador, da un número entre 0 y 1.
        # Ej: -0.5 / -1.0 = 0.5. ln(0.5) es negativo.
        
        exponent_rt = log(ratio_logs) # Esto será negativo si el tumor crece
        
        # r = - (1 / t_diff) * exponent_rt
        r = -exponent_rt / time_diff_days
        
        return max(0.00001, r) # Asegurar que r sea positivo y pequeño si no hay cambio o decrecimiento leve

    except ValueError as e:
        raise ValueError(f"Error calculando r para Gompertz desde el historial: {e}. "
                         "Asegúrese que T_anterior y T_actual sean consistentes con K y el crecimiento.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado en cálculo de r Gompertz: {e}")


def calculate_r_from_history_exponential(T_anterior: float, T_actual: float, time_diff_days: float) -> float:
    # Calcula 'r' usando la fórmula exponencial.
    if time_diff_days <= 0:
        raise ValueError("El tiempo transcurrido debe ser positivo para calcular 'r'.")
    if T_anterior <= 0:
        raise ValueError("El tamaño del tumor anterior debe ser positivo.")
    if T_actual <= 0:
        # El tumor actual no puede ser cero o negativo
        raise ValueError("El tamaño del tumor actual debe ser positivo.")

    # T_actual = T_anterior * exp(r * t_diff_days)
    # T_actual / T_anterior = exp(r * t_diff_days)
    # ln(T_actual / T_anterior) = r * t_diff_days
    # r = ln(T_actual / T_anterior) / t_diff_days
    
    try:
        ratio = T_actual / T_anterior
        if ratio <= 0:
            raise ValueError("La razón T_actual / T_anterior debe ser positiva.")
        
        r = log(ratio) / time_diff_days
        return max(0.00001, r) # Asegurar que r sea positivo
    except ValueError as e:
        raise ValueError(f"Error calculando r para Exponencial desde el historial: {e}. "
                         "Asegúrese que T_anterior y T_actual sean positivos.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado en cálculo de r Exponencial: {e}")

def calculate_exponential_time(T0, r, T_umbral):
    if r <= 0:
        # Manejar caso de r no positivo, ya que log(T_umbral/T0)/r sería indefinido o negativo
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
    
    # Validación clave para Gompertz: T0 < T_umbral < K
    if not (T0 < T_umbral < K):
        return None, f"Para Gompertz, se requiere T_actual ({T0}) < Umbral Crítico ({T_umbral}) < K (Capacidad Máxima ({K}))."

    try:
        ln_T0_K = log(T0 / K)
        ln_Tumbral_K = log(T_umbral / K)

        if ln_T0_K == 0: # Esto significa T0 = K, lo cual haría el denominador cero.
            return None, "El tamaño inicial es igual a la capacidad máxima (K), no hay crecimiento esperado."
        
        inner_log_ratio = ln_Tumbral_K / ln_T0_K
        
        # inner_log_ratio debe ser positivo para tomar el log. Además, si T0 < Tumbral < K,
        # entonces ln(T0/K) y ln(Tumbral/K) serán negativos, y ln(Tumbral/K) será "menos negativo"
        # que ln(T0/K), lo que hace que inner_log_ratio esté entre 0 y 1.
        # Por ejemplo: ln(5/20) = -1.38; ln(3/20) = -1.89; -1.38 / -1.89 = 0.73
        
        if inner_log_ratio <= 0:
             return None, "No se puede calcular el tiempo: el tumor ya es demasiado grande o los parámetros son inconsistentes (inner_log_ratio <= 0)."


        time = - (1 / r) * log(inner_log_ratio)
        
        if time < 0: # El tiempo no puede ser negativo
            return 0, "El umbral crítico ya fue alcanzado o superado, o el modelo indica un decrecimiento inusual."

        return time, None
    except Exception as e:
        return None, str(e)


def generate_growth_curve(model_type, T0, r, K, T_umbral, total_time_days, steps=100):
    points = []
    
    # Calcular un rango de tiempo adecuado para la gráfica
    # Ir un poco más allá del tiempo estimado para ver la tendencia
    max_time = total_time_days * 1.5 if total_time_days > 0 else 100 
    if max_time < 100: # Asegurar que la gráfica tenga un mínimo de tiempo para visualizar
        max_time = 100

    time_step = max_time / steps

    for i in range(steps + 1):
        t = i * time_step
        if model_type == 'exponencial':
            T_at_t = T0 * exp(r * t)
        elif model_type == 'gompertz':
            # Asegúrate que log(T0/K) no sea cero si T0 = K.
            # Esto se previene con las validaciones en calculate_gompertz_time
            if T0 == K: # Evitar division by zero or log(0) if T0 approaches K
                 T_at_t = K
            else:
                T_at_t = K * exp(log(T0 / K) * exp(-r * t))
        else:
            T_at_t = 0 # Valor por defecto o error

        points.append({"x": t, "y": T_at_t})
    return points

# --- ENDPOINTS ---

@app.post("/api/doctor_login")
async def doctor_login(request: DoctorLoginRequest):
    if request.doctor_code == VALID_DOCTOR_CODE:
        return {"message": "Login exitoso", "doctor_logged_in": True}
    raise HTTPException(status_code=401, detail="Código de doctor inválido")

@app.get("/api/patients", response_model=List[PatientListItem])
async def get_patients(doctor_code: str, db: Session = Depends(get_db)):
    if doctor_code != VALID_DOCTOR_CODE:
        raise HTTPException(status_code=401, detail="Código de doctor inválido o no autorizado")
    
    patients = db.query(Paciente).filter(Paciente.doctor_code == doctor_code).all()
    
    result = []
    for p in patients:
        last_visit = db.query(Visita).filter(Visita.paciente_id == p.id).order_by(Visita.fecha_visita.desc()).first()
        result.append(PatientListItem(
            id=p.id,
            identificacion=p.identificacion,
            nombre_paciente=p.nombre_paciente,
            last_visit_date=last_visit.fecha_visita.strftime("%Y-%m-%d") if last_visit else None
        ))
    return result

@app.get("/api/patient_history/{patient_id}", response_model=List[PatientHistoryItem])
async def get_patient_history(patient_id: int, doctor_code: str, db: Session = Depends(get_db)):
    if doctor_code != VALID_DOCTOR_CODE:
        raise HTTPException(status_code=401, detail="Código de doctor inválido o no autorizado")
    
    patient = db.query(Paciente).filter(Paciente.id == patient_id, Paciente.doctor_code == doctor_code).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Paciente no encontrado o no autorizado para este doctor.")
    
    history = []
    for visit in patient.visitas:
        history.append(PatientHistoryItem(
            fecha_visita=visit.fecha_visita.strftime("%Y-%m-%d"),
            initial_tumor_size_cm3=visit.initial_tumor_size_cm3,
            tiempo_estimado_dias=visit.tiempo_estimado_dias,
            r_calculado=visit.r_calculado,
            model_type=visit.model_type
        ))
    return history


@app.post("/api/predict", response_model=PredictionResponse)
async def predict(request: PredictionRequest, db: Session = Depends(get_db)):
    model_type = request.model_type
    patient_data = request.patient_data
    doctor_code = request.doctor_code

    if doctor_code != VALID_DOCTOR_CODE:
        raise HTTPException(status_code=401, detail="Código de doctor inválido o no autorizado.")

    # Preparar datos del paciente para guardar/usar
    identificacion = patient_data.identificacion
    nombre_paciente = patient_data.nombre_paciente
    current_visit_date_dt = datetime.strptime(patient_data.current_visit_date, "%Y-%m-%d")
    
    # 1. Recuperar o crear paciente
    paciente_db = db.query(Paciente).filter(Paciente.identificacion == identificacion, Paciente.doctor_code == doctor_code).first()

    if not paciente_db:
        # Es un paciente nuevo para este doctor
        if not patient_data.is_first_visit:
            raise HTTPException(status_code=400, detail="Este paciente no tiene historial registrado. Debe ser marcado como 'Primera visita'.")
        
        paciente_db = Paciente(
            identificacion=identificacion,
            nombre_paciente=nombre_paciente,
            sexo=patient_data.sexo,
            edad=patient_data.edad,
            doctor_code=doctor_code
        )
        db.add(paciente_db)
        db.flush() # Para que paciente_db.id esté disponible

    # 2. Determinar T0 (initial_tumor_size_cm3) y T_anterior (si aplica)
    T0_calculo = patient_data.initial_tumor_size_cm3 # Este es el tamaño del tumor en la visita actual

    r_calculado = 0.0
    tiempo_estimado = None
    error_message = None
    K_calculado = K_GOMPERTZ_DEFAULT if model_type == 'gompertz' else None # K solo para Gompertz
    t_umbral_critico = UMBRAL_CRITICO_CM3_DEFAULT

    if patient_data.is_first_visit:
        # Calcular 'r' bibliográfico para la primera visita
        r_calculado = calculate_r_bibliografico(patient_data)
    else:
        # Recuperar la última visita para calcular 'r' personalizado
        last_visit = db.query(Visita).filter(Visita.paciente_id == paciente_db.id).order_by(Visita.fecha_visita.desc()).first()
        
        if not last_visit:
            raise HTTPException(status_code=400, detail="No se encontró historial para este paciente. Marque como 'Primera visita'.")
        
        if patient_data.previous_tumor_size_cm3 is None or patient_data.last_visit_date is None:
            raise HTTPException(status_code=400, detail="Para una visita subsecuente, se requieren el tamaño del tumor anterior y la fecha de la última visita.")

        # Verificar consistencia: ¿El historial de DB coincide con lo que el usuario envió?
        # Para simplificar y ahorrar tiempo: asumimos que el usuario envía los datos correctos de la visita anterior.
        # En un sistema real, podríamos usar last_visit.initial_tumor_size_cm3 y last_visit.fecha_visita
        # y validar que sean consistentes con lo que el usuario ingresó, o directamente usarlos.
        
        previous_tumor_size_from_form = patient_data.previous_tumor_size_cm3
        last_visit_date_dt = datetime.strptime(patient_data.last_visit_date, "%Y-%m-%d")
        
        time_diff = (current_visit_date_dt - last_visit_date_dt).days
        if time_diff <= 0:
            raise HTTPException(status_code=400, detail="La fecha de la visita actual debe ser posterior a la fecha de la visita anterior.")

        try:
            if model_type == 'exponencial':
                r_calculado = calculate_r_from_history_exponential(previous_tumor_size_from_form, T0_calculo, time_diff)
            elif model_type == 'gompertz':
                r_calculado = calculate_r_from_history_gompertz(previous_tumor_size_from_form, T0_calculo, time_diff, K_calculado)
            else:
                raise HTTPException(status_code=400, detail="Tipo de modelo no soportado.")
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Error al calcular 'r' desde el historial: {e}")


    # 3. Realizar la predicción
    if model_type == 'exponencial':
        ecuacion_latex = r"T(t) = T_0 \cdot e^{rt}"
        tiempo_estimado, error_message = calculate_exponential_time(T0_calculo, r_calculado, t_umbral_critico)
    elif model_type == 'gompertz':
        ecuacion_latex = r"T(t) = K \cdot \exp\left( \ln\left(\frac{T_0}{K}\right) \cdot \exp(-rt) \right)"
        tiempo_estimado, error_message = calculate_gompertz_time(T0_calculo, r_calculado, K_calculado, t_umbral_critico)
    else:
        raise HTTPException(status_code=400, detail="Tipo de modelo no soportado.")

    if error_message:
        raise HTTPException(status_code=400, detail=error_message)

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
        intervalo_confianza="No disponible", # Placeholder, puedes calcularlo más adelante
        fecha_diagnostico=datetime.strptime(patient_data.fecha_diagnostico, "%Y-%m-%d") if patient_data.fecha_diagnostico else None,
        dias_tratamiento=patient_data.dias_tratamiento,
        estadio=patient_data.estadio,
        grado_histopatologico=patient_data.grado_histopatologico,
        er_pr=patient_data.er_pr,
        tipo_cancer=patient_data.tipo_cancer,
        her2=patient_data.her2,
        metastasis=patient_data.metastasis
    )
    db.add(new_visit)
    db.commit()
    db.refresh(paciente_db) # Refrescar la relación por si se necesita

    # 6. Preparar la respuesta
    unidad_tiempo = "días"
    intervalo_confianza_str = "No disponible (Implementación futura)" # Placeholder
    
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
        <li>**Cirugía:** Lumpectomía (cirugía conservadora de mama) o Mastectomía (extirpación completa de la mama).</li>
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

    return PredictionResponse(
        tiempo_estimado=f"{tiempo_estimado:.2f}",
        unidad_tiempo=unidad_tiempo,
        intervalo_confianza=intervalo_confianza_str,
        estado_cancer_actual_t=current_cancer_stage,
        interpretacion_resultado=interpretacion_resultado,
        posibles_tratamientos=posibles_tratamientos,
        descargo_responsabilidad=disclaimer_text,
        ecuacion_latex=ecuacion_latex,
        parametros_usados={
            "T0_calculo": T0_calculo,
            "r_calculado": r_calculado,
            "K_calculado": K_calculado if model_type == 'gompertz' else "N/A (Modelo Exponencial)",
            "T_umbral_critico": t_umbral_critico,
            "model_type": model_type
        },
        datos_paciente_enviados=patient_data.model_dump(), # Envía todos los datos recibidos
        puntos_curva=puntos_curva
    )