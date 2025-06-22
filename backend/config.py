class Config:
    FRONTEND_URL = "https://cancer-frontend.onrender.com"
    # Puerto del backend
    FLASK_RUN_PORT = 5000
    # Desactivar modo debug en producción
    DEBUG = True
    TESTING = False

# NOTA: Los valores a continuación son representativos de los rangos y medianas proporcionados.
# Para una aplicación de producción, sería ideal consultar con expertos clínicos para los valores exactos
# que se consideren más apropiados como defaults o bases para el cálculo.

CANCER_PARAMETERS = {
    "Cáncer de Mama": { # Agrupamos por tipo de cáncer principal
        "default": { # Valores base si no hay factores específicos
            "r_per_day": 0.0042,  # Mediana global de 164 días de duplicación (ln(2)/164)
            "K_cm3": 20.0       # Valor representativo, e.g., Tv2 del estudio k4
        },
        "Subtipo Molecular": {
            "Triple Negativo": {"r_per_day": 0.0067},
            "HER2-positivo": {"r_per_day": 0.0043},
            "ER-positivo": {"r_per_day": 0.0029},
            "No-luminal": {"r_per_day": 0.0039},
            "Luminal": {"r_per_day": 0.0014}
        },
        "Grado Histopatológico": {
            "Grado 1": {"r_per_day": 0.0022},
            "Grado 2": {"r_per_day": 0.0024},
            "Grado 3": {"r_per_day": 0.0036}
        },
        # Rangos de edad simplificados (pueden ser más detallados si se desea)
        "Edad del Paciente": {
            "Joven": {"r_per_day_factor": 1.1}, # Tasa ligeramente más alta para menores de 50-60
            "Mayor": {"r_per_day_factor": 0.9}  # Tasa ligeramente más baja para mayores de 50-60
        },
        "Otros Factores Opcionales": {
            # Aquí podrías añadir ajustes para metástasis, etc.
            # Por ejemplo, la metástasis podría implicar un 'r' más agresivo.
            "Metástasis: Si": {"r_per_day_factor": 1.2}, # Ejemplo de factor de ajuste
            "Metástasis: No": {"r_per_day_factor": 1.0},
            "Metástasis: Desconocido": {"r_per_day_factor": 1.0},
        }
    }
}

# Definición de umbrales para la etapa del cáncer simplificada (SOLO POR TAMAÑO)
# IMPORTANTE: Esto es una EXTREMA SIMPLIFICACIÓN para fines del ejercicio.
# La estadificación AJCC es mucho más compleja e incluye N (ganglios) y M (metástasis).
# SE DEBE MOSTRAR UNA ADVERTENCIA CLARA AL USUARIO sobre esta simplificación.
CANCER_STAGE_THRESHOLDS_CM3 = {
    "Etapa I": {"max_size": 2.0},  # <= 2 cm
    "Etapa II": {"max_size": 5.0}, # > 2 cm y <= 5 cm
    "Etapa III": {"max_size": 10.0},# > 5 cm y <= 10 cm (arbitrario para demo)
    "Etapa IV": {"min_size": 10.0}  # > 10 cm (arbitrario para demo)
}

# Umbrales de edad para aplicar factores de r
AGE_THRESHOLDS = {
    "Joven": 50, # Edad <= 50
    "Mayor": 51  # Edad >= 51
}