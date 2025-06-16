import numpy as np

def calculate_tumor_size_gompertz(T0, r, K, t):
    """
    Calcula el tamaño del tumor en el tiempo 't' usando el modelo de Gompertz.
    T(t) = K * exp(ln(T0/K) * exp(-r*t))
    """
    if K <= 0 or T0 <= 0:
        raise ValueError("K y T0 deben ser mayores que cero para Gompertz.")
    
    # Asegurarse de que T0 < K para un crecimiento sigmoidal esperado
    if T0 >= K:
        # Manejar caso donde el tumor inicial es mayor o igual a la capacidad máxima
        # Podrías devolver K, o indicar que ya está en su límite
        # Para simplificar, podríamos simplemente devolver K si T0 >= K para el tiempo 0
        # O lanzar un error si T0 > K y esperamos un crecimiento
        if T0 > K:
             # Si T0 es mayor que K, el modelo predice decrecimiento hacia K
             # Pero para una predicción de 'tiempo a umbral crítico' esto puede ser problemático
             pass # El cálculo a continuación debería manejarlo, pero es una edge case
             
    log_T0_K = np.log(T0 / K)
    exponent = log_T0_K * np.exp(-r * t)
    return K * np.exp(exponent)

def calculate_time_to_threshold_gompertz(T0, r, K, T_critical):
    """
    Calcula el tiempo para alcanzar un tamaño crítico de tumor T_critical
    usando el modelo de Gompertz.
    t = -(1/r) * ln( ln(T_critical/K) / ln(T0/K) )
    """
    if T0 <= 0 or r <= 0 or K <= 0 or T_critical <= 0:
        raise ValueError("Parámetros inválidos para cálculo Gompertz. Todos deben ser > 0.")
    if T0 >= K:
        raise ValueError("T0 debe ser menor que K para un crecimiento significativo en Gompertz.")
    if T_critical >= K:
        raise ValueError("T_critical debe ser menor que K para poder ser alcanzado en Gompertz.")
    if T_critical <= T0:
        raise ValueError("T_critical debe ser mayor que T0 para calcular el tiempo de crecimiento.")

    num_term = np.log(T_critical / K)
    den_term = np.log(T0 / K)
    
    if den_term == 0: # Evitar división por cero si T0 == K
        raise ValueError("T0 no puede ser igual a K para el cálculo de Gompertz.")

    try:
        log_ratio = np.log(num_term / den_term)
        time = -(1 / r) * log_ratio
        return time
    except ValueError:
        # Esto ocurre si num_term / den_term es negativo o cero (ej. T_critical/K es inválido)
        raise ValueError("No se puede calcular el tiempo para Gompertz con estos parámetros. "
                         "Asegúrese que T0 < T_critical < K.")


def generate_gompertz_curve_points(T0, r, K, max_time_points=100, max_time_limit=None):
    """
    Genera puntos para graficar la curva de crecimiento de Gompertz.
    """
    if max_time_limit is None:
        # Calcular un tiempo razonable para la curva
        # Podría ser el tiempo para alcanzar el 95% de K o un valor fijo
        if r > 0 and K > T0:
            # Estimar el tiempo para acercarse a K (ej. hasta el 95% de K)
            try:
                time_to_near_K = -np.log(np.log(0.95) / np.log(T0 / K)) / r
                max_time_limit = time_to_near_K * 1.5 if time_to_near_K > 0 else 365 * 15 # 1.5 veces ese tiempo o 15 años
            except Exception:
                 max_time_limit = 365 * 15 # Fallback: 15 años en días
        else:
            max_time_limit = 365 * 15 # Fallback: 15 años en días


    times = np.linspace(0, max_time_limit, max_time_points)
    sizes = calculate_tumor_size_gompertz(T0, r, K, times)
    
    return [{"x": float(t), "y": float(s)} for t, s in zip(times, sizes)]

# Puedes añadir una función simple para un intervalo de confianza heurístico si lo necesitas más adelante
def calculate_confidence_interval_gompertz(time_estimated):
    # Esto es solo un ejemplo heurístico, NO es un cálculo estadístico riguroso
    margin = time_estimated * 0.15 # +/- 15% (un poco más que exponencial por más complejidad)
    return max(0, time_estimated - margin), time_estimated + margin