from flask import Blueprint, request, jsonify, current_app
from services.prediction_service import PredictionService # Importamos el nuevo manejador
from database.models import db # Importamos la función para obtener la sesión de DB
from datetime import date # Para manejar fechas
from pydantic import ValidationError
from schemas.prediction_schemas import PredictionRequest, OtherFactors

# Asumiremos que prediction_service.py será refactorizado en la Fase 2
# from services.prediction_service import PredictionService # No importamos la función directa, sino la clase

predict_bp = Blueprint('predict', __name__)

@predict_bp.route('/predict', methods=['POST'])
def predict():
    # --- Gestión de la sesión de base de datos ---
    # get_db() es un generador, así que usamos 'next()' para obtener la sesión
    db_session=db.session
    # Instancia PredictionService, pasándole la sesión de DB
    prediction_service = PredictionService(db_session)

    try:
        #1. Validar la solicitud JSON usando pydantic
        #Esto automáticamente convierte y valida los tipos de datos
        #Los errores de validación serán capturados por ValidationError
        #data = request.json
        data=PredictionRequest.model_validate(request.json)

        #2 --- Extracción de datos del request (ahora más complejos) ---
        #Los datos ya están en el formato y tipo correctos
        identification_number = data.identification_number
        current_tumor_size = data.current_tumor_size
        current_measurement_date = data.current_measurement_date
        name = data.name
        date_of_birth = data.date_of_birth
        #T_critical = data.T_critical

        # Los other_factors ahora son una instancia de OtherFactors, no un dict
        # Se convierten a dict antes de pasarlos al servicio
        other_factors = data.other_factors.model_dump() if data.other_factors else {}

        #--- Validaciones básicas (se mejorarán en la Fase 2 con Pydantic/Marshmallow) ---
        #3. Validación específica para pacientes nuevos
        # Pydantic valida los tipos, pero la lógica de "requerido si es nuevo" va aquí
        patient_exists = prediction_service.patient_data_manager.get_patient_by_identification_number(identification_number)
        if not patient_exists:
            if not name or not date_of_birth:
                return jsonify({"error": "Para un paciente nuevo, 'name' y 'date_of_birth' son campos obligatorios."}), 400

        #4. --- Llamada al PredictionService (Toda la lógica principal se mueve aquí) ---
        result = prediction_service.predict(
            identification_number=identification_number,
            current_tumor_size=current_tumor_size,
            current_measurement_date=current_measurement_date,
            patient_name=name, # Se pasa solo si es un nuevo paciente, el servicio lo manejará
            date_of_birth=date_of_birth, # Se pasa solo si es un nuevo paciente, el servicio lo manejará
            #T_critical=T_critical,
            other_factors=other_factors
        )
        
        # El PredictionService ahora devuelve el resultado completo
        return jsonify(result), 200

    except ValidationError as e:
        # Pydantic genera errores detallados
        current_app.logger.warning(f"Validation error: {e.errors()}")
        db_session.rollback()
        return jsonify({"error": "Invalid input data", "details": e.errors()}), 422 # 422 Unprocessable Entity
    except ValueError as ve: 
        # Errores de validación o lógicos desde el servicio (ej. tiempo <= 0)
        current_app.logger.warning(f"Client input/service logic error: {ve}")
        db_session.rollback()
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        current_app.logger.error(f"Server error during prediction: {e}", exc_info=True)
        db_session.rollback()
        return jsonify({"error": "An unexpected server error occurred. Please try again later."}), 500
    finally:
        db_session.close()

