from flask import Blueprint, request, jsonify, current_app
from services.prediction_service import PredictionService # Importamos el nuevo manejador
from database.models import get_db # Importamos la función para obtener la sesión de DB
from datetime import date # Para manejar fechas

# Asumiremos que prediction_service.py será refactorizado en la Fase 2
# from services.prediction_service import PredictionService # No importamos la función directa, sino la clase

predict_bp = Blueprint('predict', __name__)

@predict_bp.route('/predict', methods=['POST'])
def predict():
    # --- Gestión de la sesión de base de datos ---
    # get_db() es un generador, así que usamos 'next()' para obtener la sesión
    db_session = next(get_db())
    # Instancia PredictionService, pasándole la sesión de DB
    prediction_service = PredictionService(db_session)

    try:
        data = request.json

        # --- Extracción de datos del request (ahora más complejos) ---
        identification_number = data.get('identification_number')
        current_tumor_size = data.get('current_tumor_size')
        current_measurement_date_str = data.get('current_measurement_date')

        # Campos opcionales (incluyendo los que ya tenías y los nuevos)
        name = data.get('name') # Necesario si es un paciente nuevo
        date_of_birth_str = data.get('date_of_birth') # Necesario si es un paciente nuevo
        # Umbral crítico (ahora opcional en input, con default en service)
        T_critical = data.get('T_critical') 

        # Otros factores opcionales que se pasan al servicio
        # Asegúrate de que estos nombres de clave coincidan con los usados en _get_bibliographic_parameters
        other_factors = {
            'tipo_cancer': data.get('tipo_cancer'),
            'subtipo_molecular': data.get('subtipo_molecular'), # <-- Asegúrate que tu frontend envía esto
            'grado_histopatologico': data.get('grado_histopatologico'), # <-- Asegúrate que tu frontend envía esto
            'er_pr': data.get('er_pr'),
            'her2': data.get('her2'),
            'metastasis': data.get('metastasis')
            # 'dias_tratamiento' y 'estadio' eliminados/manejados diferente
            # 'edad' se calculará de date_of_birth
        }

        # --- Validaciones básicas (se mejorarán en la Fase 2 con Pydantic/Marshmallow) ---
        if not all([identification_number, current_tumor_size, current_measurement_date_str]):
            return jsonify({"error": "Missing required fields: identification_number, current_tumor_size, current_measurement_date."}), 400

        try:
            current_tumor_size = float(current_tumor_size)
            current_measurement_date = date.fromisoformat(current_measurement_date_str)
            if T_critical is not None: # Solo convertir si viene en el request
                T_critical = float(T_critical)
        except (ValueError, TypeError) as e:
            return jsonify({"error": f"Invalid format for numerical parameters or date: {e}"}), 400

        # Convertir fecha de nacimiento si está presente para nuevo paciente
        date_of_birth = None
        if date_of_birth_str:
            try:
                date_of_birth = date.fromisoformat(date_of_birth_str)
            except ValueError:
                return jsonify({"error": "Invalid date format for date_of_birth."}), 400

        # --- Llamada al PredictionService (Toda la lógica principal se mueve aquí) ---
        result = prediction_service.predict(
            identification_number=identification_number,
            current_tumor_size=current_tumor_size,
            current_measurement_date=current_measurement_date,
            patient_name=name, # Se pasa solo si es un nuevo paciente, el servicio lo manejará
            date_of_birth=date_of_birth, # Se pasa solo si es un nuevo paciente, el servicio lo manejará
            T_critical=T_critical,
            other_factors=other_factors
        )
        
        # El PredictionService ahora devuelve el resultado completo
        return jsonify(result), 200

    except ValueError as ve: # Errores de validación o lógicos desde el servicio
        current_app.logger.warning(f"Client input error: {ve}")
        db_session.rollback()
        return jsonify({"error": str(ve)}), 400
    except Exception as e: # Cualquier otro error inesperado
        current_app.logger.error(f"Server error during prediction: {e}", exc_info=True)
        db_session.rollback() # Asegura rollback en cualquier error
        return jsonify({"error": "An unexpected server error occurred."}), 500
    finally:
        db_session.close() # Asegúrate de cerrar la sesión de la base de datos