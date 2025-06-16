import numpy as np

def calculate_tumor_size_exponential(T0, r, t):
    """
    Calcula el tamaño del tumor en el tiempo 't' usando el modelo exponencial.
    T(t) = T0 * e^(r*t)
    """
    return T0 * np.exp(r * t)

def calculate_time_to_threshold_exponential(T0, r, T_critical):
    """
    Calcula el tiempo para alcanzar un tamaño crítico de tumor T_critical
    usando el modelo exponencial.
    t = (1/r) * ln(T_critical / T0)
    """
    if T0 <= 0 or r <= 0 or T_critical <= T0:
        raise ValueError("Parámetros inválidos para cálculo exponencial. T0, r deben ser > 0 y T_critical > T0.")
    
    time = (1 / r) * np.log(T_critical / T0)
    return time

def generate_exponential_curve_points(T0, r, max_time_points=100, max_time_limit=None):
    """
    Genera puntos para graficar la curva de crecimiento exponencial.
    max_time_limit: Si se proporciona, el tiempo máximo para la curva. Si no, se calcula un límite razonable.
    """
    if max_time_limit is None:
        # Calcula un tiempo razonable, ej. hasta el doble del tiempo a un umbral hipotético o 10 años
        try:
            time_to_double = np.log(2) / r if r > 0 else 0
            max_time_limit = time_to_double * 5 if time_to_double > 0 else 365 * 10 # 5 veces el tiempo para duplicarse o 10 años
        except Exception:
            max_time_limit = 365 * 10 # Fallback: 10 años en días

    times = np.linspace(0, max_time_limit, max_time_points)
    sizes = calculate_tumor_size_exponential(T0, r, times)
    
    # Limitar los tamaños a un valor máximo razonable para evitar números gigantes en la gráfica
    sizes[sizes > 1e10] = 1e10 

    return [{"x": float(t), "y": float(s)} for t, s in zip(times, sizes)]

# Puedes añadir una función simple para un intervalo de confianza heurístico si lo necesitas más adelante
def calculate_confidence_interval_exponential(time_estimated):
    # Esto es solo un ejemplo heurístico, NO es un cálculo estadístico riguroso
    # Para un modelo real, necesitarías análisis de sensibilidad o bootstrap
    margin = time_estimated * 0.1 # +/- 10%
    return max(0, time_estimated - margin), time_estimated + margin