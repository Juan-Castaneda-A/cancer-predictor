from flask import Blueprint, request, jsonify, current_app
from services.patient_data_manager import PatientDataManager # Importamos el nuevo manejador
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
    patient_data_manager = PatientDataManager(db_session)

    try:
        data = request.json

        # --- Extracción de datos del request (ahora más complejos) ---
        identification_number = data.get('identification_number')
        current_tumor_size = data.get('current_tumor_size')
        current_measurement_date_str = data.get('current_measurement_date')

        # Campos opcionales (incluyendo los que ya tenías y los nuevos)
        name = data.get('name') # Necesario si es un paciente nuevo
        date_of_birth_str = data.get('date_of_birth') # Necesario si es un paciente nuevo
        T_critical = data.get('T_critical') # Sigue siendo una entrada del usuario

        # Otros factores opcionales que mencionaste
        other_factors = {
            'tipo_cancer': data.get('tipo_cancer'),
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
            if T_critical is not None:
                T_critical = float(T_critical)
            else:
                # Establece un valor por defecto si no se proporciona T_critical
                # Puedes hacer esto más sofisticado en la Fase 2
                T_critical = 10.0 # Valor por defecto arbitrario
        except (ValueError, TypeError) as e:
            return jsonify({"error": f"Invalid format for numerical parameters or date: {e}"}), 400

        # --- Lógica de Manejo de Pacientes (Nueva) ---
        patient = patient_data_manager.get_patient_by_identification_number(identification_number)
        
        patient_info = {} # Diccionario para almacenar la información del paciente para la respuesta

        if not patient:
            # --- Es un paciente nuevo ---
            if not all([name, date_of_birth_str]):
                return jsonify({"error": "New patient requires name and date_of_birth."}), 400
            
            try:
                date_of_birth = date.fromisoformat(date_of_birth_str)
            except ValueError:
                return jsonify({"error": "Invalid date format for date_of_birth."}), 400

            new_patient = patient_data_manager.create_patient(
                identification_number=identification_number,
                name=name,
                date_of_birth=date_of_birth,
                initial_tumor_size=current_tumor_size,
                measurement_date=current_measurement_date
            )
            message = f"Nuevo paciente '{new_patient.name}' registrado con su primera medición."
            
            # Prepara la info del paciente para la respuesta
            patient_info = {
                "id": new_patient.id,
                "identification_number": new_patient.identification_number,
                "name": new_patient.name,
                "date_of_birth": new_patient.date_of_birth.isoformat(),
                "last_tumor_size": new_patient.last_measurement.size_cm3,
                "last_measurement_date": new_patient.last_measurement.measurement_date.isoformat(),
                "is_new_patient": True
            }

            # En un paciente nuevo, T0 para la predicción es el current_tumor_size
            T0_for_prediction = current_tumor_size
            last_measurement_date = current_measurement_date

        else:
            # --- Es un paciente existente ---
            # Guardar la nueva medición inmediatamente
            new_measurement = patient_data_manager.add_tumor_measurement(
                patient_id=patient.id,
                tumor_size=current_tumor_size,
                measurement_date=current_measurement_date
            )
            message = f"Nueva medición de tumor ({new_measurement.size_cm3} cm³) para paciente '{patient.name}' añadida."

            # Recuperar la medida ANTERIOR a la recién agregada para calcular 'r' empírica
            # Esto asume que la `tumor_measurements` relación en el modelo Patient
            # está ordenada y que `patient.last_measurement` ya está cargada
            # con la medida más reciente ANTES de añadir la nueva.
            # O, para ser más seguro, obtenemos todas las medidas y las ordenamos.
            all_measurements = patient_data_manager.get_all_tumor_measurements_for_patient(patient.id)
            
            T0_for_prediction = None # Este será el T_anterior si hay dos medidas
            last_measurement_date = None

            if len(all_measurements) >= 2:
                # La penúltima medida es la "anterior" a la que acabamos de guardar
                previous_measurement = all_measurements[-2] 
                T0_for_prediction = previous_measurement.size_cm3
                last_measurement_date = previous_measurement.measurement_date
            elif len(all_measurements) == 1:
                # Si solo hay una medida (la que acabamos de añadir), se considera el T0 inicial
                T0_for_prediction = all_measurements[0].size_cm3
                last_measurement_date = all_measurements[0].measurement_date

            # Prepara la info del paciente para la respuesta
            patient_info = {
                "id": patient.id,
                "identification_number": patient.identification_number,
                "name": patient.name,
                "date_of_birth": patient.date_of_birth.isoformat(),
                "last_tumor_size": current_tumor_size, # La última que se acaba de registrar
                "last_measurement_date": current_measurement_date.isoformat(),
                "is_new_patient": False
            }
            if T0_for_prediction is not None and T0_for_prediction != current_tumor_size:
                patient_info["previous_tumor_size"] = T0_for_prediction
                patient_info["previous_measurement_date"] = last_measurement_date.isoformat()


        # --- Placeholder para la Lógica de Predicción ---
        # En la Fase 2, aquí es donde llamaríamos a PredictionService
        # con T0_for_prediction, current_tumor_size, last_measurement_date, current_measurement_date,
        # T_critical, y other_factors.
        # Por ahora, solo devolvemos una confirmación de la operación de DB.
        
        response_data = {
            "status": "success",
            "message": message,
            "patient_data_processed": patient_info,
            "T_critical_used": T_critical,
            "current_tumor_size_for_next_step": current_tumor_size, # El T0 para las funciones de modelo
            "current_measurement_date_for_next_step": current_measurement_date.isoformat()
        }
        if T0_for_prediction:
             response_data["T0_for_r_calculation"] = T0_for_prediction
             response_data["date_T0_for_r_calculation"] = last_measurement_date.isoformat()

        return jsonify(response_data), 200

    except Exception as e:
        db_session.rollback() # En caso de error, deshaz los cambios en la DB
        current_app.logger.error(f"Error in predict route: {e}") # Usa el logger de Flask
        return jsonify({"error": str(e)}), 500
    finally:
        db_session.close() # ¡Crucial! Asegúrate de cerrar la sesión de la base de datos