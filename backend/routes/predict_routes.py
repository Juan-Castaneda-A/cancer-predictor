from flask import Blueprint, request, jsonify
from services.prediction_service import get_prediction_data

predict_bp = Blueprint('predict', __name__)

@predict_bp.route('/predict', methods=['POST'])
def predict():
    data = request.json
    
    model_type = data.get('model_type')
    T0 = data.get('T0')
    r = data.get('r')
    K = data.get('K')
    T_critical = data.get('T_critical')
    
    other_factors = {
        'nombre_paciente': data.get('nombre_paciente'),
        'fecha_diagnostico': data.get('fecha_diagnostico'),
        'dias_tratamiento': data.get('dias_tratamiento'),
        'estadio': data.get('estadio'),
        'er_pr': data.get('er_pr'),
        'tipo_cancer': data.get('tipo_cancer'),
        'her2': data.get('her2'),
        'edad': data.get('edad'),
        'metastasis': data.get('metastasis')
    }

    try:
        T0 = float(T0)
        r = float(r)
        T_critical = float(T_critical)
        if K is not None:
            K = float(K)
        
        if other_factors.get('dias_tratamiento'):
            other_factors['dias_tratamiento'] = int(other_factors['dias_tratamiento'])
        if other_factors.get('edad'):
            other_factors['edad'] = int(other_factors['edad'])

    except (ValueError, TypeError) as e:
        return jsonify({"error": f"Error en el formato de los parámetros numéricos: {e}"}), 400

    result, status_code = get_prediction_data(model_type, T0, r, K, T_critical, other_factors)
    return jsonify(result), status_code