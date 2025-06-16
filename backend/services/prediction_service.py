from backend.models import exponential_model, gompertz_model
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
    except ValueError as e:
        return {"error": str(e)}, 400
    except Exception as e:
        return {"error": "Error interno del servidor al calcular la predicción: " + str(e)}, 500
