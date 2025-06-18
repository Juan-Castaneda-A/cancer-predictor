from flask import Blueprint, request, jsonify
from services.prediction_service import get_prediction_data

predict_bp = Blueprint('predict', __name__)

@predict_bp.route('/predict', methods=['POST'])
def predict():
    data = request.json
    
    if not data:
        return jsonify({"error": "No se proporcionaron datos."}), 400
    
    # El servicio de predicción manejará toda la lógica de validación,
    # conversión de tipos y selección de parámetros.
    result, status_code = get_prediction_data(data) # Pasa todo el diccionario de datos
    
    return jsonify(result), status_code