import math # Cambiado de numpy a math para operaciones escalares simples

def calculate_tumor_size_gompertz(T0, r, K, t):
    """
    Calcula el tamaño del tumor en el tiempo 't' usando el modelo de Gompertz.
    T(t) = K * exp(ln(T0/K) * exp(-r*t))
    T0: Tamaño inicial del tumor (cm^3)
    r: Tasa de crecimiento inicial (días^-1)
    K: Capacidad máxima del tumor (cm^3)
    t: Tiempo transcurrido (días)
    Retorna: Tamaño del tumor en el tiempo 't' (cm^3)
    """
    if K <= 0 or T0 <= 0 or r <= 0:
        # Lanzar error si K, T0, r no son positivos.
        raise ValueError("Parámetros (T0, r, K) deben ser mayores que cero para Gompertz.")
    
    # Manejo de edge cases para logaritmos
    if T0 / K <= 0: # Si T0 es 0 o negativo, log(0) es indefinido.
        return 0.0 # O manejar el error según la política de tu app
    
    try:
        log_T0_K = math.log(T0 / K)
        exponent_inner = log_T0_K * math.exp(-r * t)
        tumor_size = K * math.exp(exponent_inner)
        return tumor_size
    except Exception as e:
        raise ValueError(f"Error en el cálculo del tamaño del tumor (Gompertz): {e}")

def calculate_time_to_threshold_gompertz(T0, r, K, T_critical):
    """
    Calcula el tiempo para alcanzar un tamaño crítico de tumor T_critical
    usando el modelo de Gompertz.
    t = -(1/r) * ln( ln(T_critical/K) / ln(T0/K) )
    """
    if T0 <= 0 or r <= 0 or K <= 0 or T_critical <= 0:
        raise ValueError("Parámetros inválidos para cálculo Gompertz. Todos deben ser > 0.")
    
    # Validaciones específicas de Gompertz para asegurar un cálculo significativo
    if T0 >= K:
        raise ValueError("En el modelo de Gompertz, el tamaño inicial (T0) debe ser menor que la Capacidad Máxima (K) para observar crecimiento.")
    if T_critical >= K:
        raise ValueError("El umbral crítico (T_critical) debe ser menor que la Capacidad Máxima (K) para ser alcanzado por el modelo de Gompertz.")
    if T_critical <= T0:
        # Si el tumor ya es igual o más grande que el objetivo, no hay tiempo restante de crecimiento
        return 0.0

    try:
        num_term = math.log(T_critical / K)
        den_term = math.log(T0 / K)
        
        if den_term == 0: # Esto significa T0 == K, lo cual ya se valida arriba con T0 >= K
            raise ValueError("División por cero: T0 no puede ser igual a K para el cálculo de Gompertz.")
        
        # Validar el argumento del logaritmo exterior
        if num_term / den_term <= 0:
            raise ValueError("Argumento inválido para el logaritmo en Gompertz. Asegúrese que T0 < T_critical < K.")

        log_ratio = math.log(num_term / den_term)
        time = -(1 / r) * log_ratio
        return time
    except ValueError as ve:
        raise ve # Relanzar errores de validación específica
    except Exception as e:
        raise ValueError(f"Error al calcular el tiempo para alcanzar el umbral (Gompertz): {e}")


def generate_gompertz_curve_points(T0_for_graph, r, K, max_time_points=100, max_time_limit=None):
    """
    Genera puntos para graficar la curva de crecimiento de Gompertz.
    T0_for_graph: Tamaño inicial del tumor para la gráfica (cm^3).
    r: Tasa de crecimiento (días^-1)
    K: Capacidad máxima del tumor (cm^3)
    max_time_points: Número de puntos a generar.
    max_time_limit: Tiempo máximo en días para la curva.
    """
    if T0_for_graph <= 0 or r <= 0 or K <= 0:
        return []

    if max_time_limit is None:
        if r > 0 and K > T0_for_graph:
            # Estimar el tiempo para acercarse a K (ej. hasta el 95% de K)
            try:
                # Asegurarse que log(0.95) / log(T0_for_graph / K) sea positivo para el logaritmo exterior
                # Y que log(T0_for_graph / K) sea negativo para un crecimiento normal
                target_ratio_to_K = 0.95 # Tiempo para alcanzar el 95% de K
                
                # Formula de tiempo para alcanzar T_target con Gompertz:
                # t = -(1/r) * ln( ln(T_target/K) / ln(T0/K) )
                
                # Si T0_for_graph es muy cercano a K, o target_ratio_to_K es 1, esto puede fallar.
                # Aseguramos T0_for_graph < K para el cálculo.
                if T0_for_graph >= K: # El tumor ya está en o por encima de K, mostrar meseta o decrecimiento
                    max_time_limit = 365 * 5 # 5 años para ver el comportamiento
                else:
                    # Cálculo para alcanzar un porcentaje de K
                    inner_log_num = math.log(target_ratio_to_K) # log(0.95) es negativo
                    inner_log_den = math.log(T0_for_graph / K) # Será negativo si T0 < K
                    
                    if inner_log_den == 0: # T0 == K
                        time_to_near_K = 365 * 5 # fallback
                    elif inner_log_num / inner_log_den <= 0: # Argumento a log negativo o cero
                         time_to_near_K = 365 * 5 # fallback
                    else:
                        time_to_near_K = -(1 / r) * math.log(inner_log_num / inner_log_den)

                    max_time_limit = time_to_near_K * 1.5 if time_to_near_K > 0 else 365 * 10 # 1.5x ese tiempo o 10 años
                    if max_time_limit < 365: # Asegurar que la gráfica dure al menos 1 año
                        max_time_limit = 365
            except Exception as e:
                print(f"Advertencia: Fallback en cálculo de max_time_limit para Gompertz: {e}")
                max_time_limit = 365 * 10 # Fallback: 10 años en días
        else:
            max_time_limit = 365 * 10 # Fallback: 10 años en días

    times = [i * (max_time_limit / (max_time_points - 1)) for i in range(max_time_points)]
    sizes = [calculate_tumor_size_gompertz(T0_for_graph, r, K, t) for t in times]
    
    # Limitar los tamaños a K o un valor razonable para evitar picos o fallos de visualización
    sizes = [min(s, K * 1.1) if K is not None and K > 0 else s for s in sizes] # No exceder K por mucho

    return [{"x": float(t), "y": float(s)} for t, s in zip(times, sizes)]

# El IC es un heurístico, no necesita cambios aquí.
def calculate_confidence_interval_gompertz(time_estimated):
    margin = time_estimated * 0.15 # +/- 15% (un poco más que exponencial por más complejidad)
    return max(0, time_estimated - margin), time_estimated + margin