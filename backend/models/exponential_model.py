import math # Cambiado de numpy a math para operaciones escalares simples

def calculate_tumor_size_exponential(T0, r, t):
    """
    Calcula el tamaño del tumor en el tiempo 't' usando el modelo exponencial.
    T(t) = T0 * e^(r*t)
    T0: Tamaño inicial del tumor (cm^3)
    r: Tasa de crecimiento (días^-1)
    t: Tiempo transcurrido (días)
    Retorna: Tamaño del tumor en el tiempo 't' (cm^3)
    """
    return T0 * math.exp(r * t)

def calculate_time_to_threshold_exponential(T_initial, r, T_target): # Renombré T0 a T_initial para claridad
    """
    Calcula el tiempo necesario para que un tumor de tamaño T_initial
    alcance un tamaño T_target usando el modelo exponencial.
    t = (1/r) * ln(T_target / T_initial)

    T_initial: Tamaño inicial del tumor para el cálculo (cm^3).
               Este es el tamaño 'actual' del tumor para el cálculo del tiempo restante.
    r: Tasa de crecimiento (días^-1)
    T_target: Tamaño objetivo/umbral crítico (cm^3)
    Retorna: Tiempo en días para alcanzar T_target.
    Levanta ValueError si los parámetros son inválidos o la meta es inalcanzable.
    """
    if T_initial <= 0 or r <= 0 or T_target <= 0:
        raise ValueError("Parámetros inválidos para cálculo exponencial. Todos deben ser > 0.")
    
    if T_initial >= T_target:
        # Si el tumor ya es igual o más grande que el objetivo, no hay tiempo restante de crecimiento
        return 0.0 
    
    try:
        time = math.log(T_target / T_initial) / r
        return time
    except Exception as e:
        raise ValueError(f"Error al calcular el tiempo para alcanzar el umbral (exponencial): {e}")

def generate_exponential_curve_points(T0_for_graph, r, max_time_points=100, max_time_limit=None):
    """
    Genera puntos para graficar la curva de crecimiento exponencial.
    T0_for_graph: Tamaño inicial del tumor para la gráfica (cm^3).
                  Esto será el 'tamaño inicial' del formulario para 1ra visita,
                  o el 'tamaño actual' para 2da+ visitas.
    r: Tasa de crecimiento (días^-1)
    max_time_points: Número de puntos a generar.
    max_time_limit: Tiempo máximo en días para la curva.
    """
    if T0_for_graph <= 0 or r <= 0:
        return [] # Retornar lista vacía si los parámetros no son válidos para la gráfica

    if max_time_limit is None:
        # Calcular un tiempo razonable para la gráfica, ej. hasta el doble del tiempo a un umbral hipotético
        # o un tiempo fijo si el cálculo es problemático (e.g. r muy pequeño).
        # Usar un umbral de 1000 cm^3 (1 litro) como referencia si no hay T_critical
        hypothetical_T_critical = 1000.0 # cm^3
        try:
            # Estimar un tiempo significativo para ver el crecimiento
            time_to_reach_hypothetical = calculate_time_to_threshold_exponential(T0_for_graph, r, hypothetical_T_critical)
            max_time_limit = time_to_reach_hypothetical * 1.5 # 1.5 veces ese tiempo
            if max_time_limit < 365: # Asegurar que la gráfica dure al menos 1 año
                max_time_limit = 365
        except Exception:
            max_time_limit = 365 * 10 # Fallback: 10 años en días

    times = [i * (max_time_limit / (max_time_points - 1)) for i in range(max_time_points)]
    sizes = [calculate_tumor_size_exponential(T0_for_graph, r, t) for t in times]
    
    # Limitar los tamaños a un valor máximo razonable para evitar números gigantes en la gráfica
    # Un límite de 1000 cm^3 o 10000 cm^3 es más realista que 1e10 para tumores
    MAX_GRAPH_SIZE = 1000.0 # cm^3 (1 litro) para evitar que la curva se dispare demasiado
    sizes = [min(s, MAX_GRAPH_SIZE) for s in sizes]

    return [{"x": float(t), "y": float(s)} for t, s in zip(times, sizes)]

# Puedes añadir una función simple para un intervalo de confianza heurístico si lo necesitas más adelante
def calculate_confidence_interval_exponential(time_estimated):
    # Esto es solo un ejemplo heurístico, NO es un cálculo estadístico riguroso
    # Para un modelo real, necesitarías análisis de sensibilidad o bootstrap
    margin = time_estimated * 0.1 # +/- 10%
    return max(0, time_estimated - margin), time_estimated + margin