from sqlalchemy.orm import Session
from database.models import Patient, TumorMeasurement
from datetime import date # Para manejar fechas

class PatientDataManager:
    def __init__(self, db: Session):
        self.db = db

    def get_patient_by_identification_number(self, identification_number: str):
        """
        Busca un paciente por su número de identificación y carga su última medición de tumor.
        """
        patient = self.db.query(Patient).filter(Patient.identification_number == identification_number).first()
        if patient:
            # Ordena las mediciones por fecha descendente y toma la primera (más reciente)
            patient.last_measurement = self.db.query(TumorMeasurement)\
                                            .filter(TumorMeasurement.patient_id == patient.id)\
                                            .order_by(TumorMeasurement.measurement_date.desc())\
                                            .first()
        return patient

    def create_patient(self, identification_number: str, name: str, date_of_birth: date,
                       initial_tumor_size: float, measurement_date: date):
        """
        Crea un nuevo paciente y su primera medición de tumor.
        """
        new_patient = Patient(
            identification_number=identification_number,
            name=name,
            date_of_birth=date_of_birth
        )
        self.db.add(new_patient)
        self.db.flush() # Para que new_patient.id esté disponible

        initial_measurement = TumorMeasurement(
            patient_id=new_patient.id,
            size_cm3=initial_tumor_size,
            measurement_date=measurement_date
        )
        self.db.add(initial_measurement)
        self.db.commit()
        self.db.refresh(new_patient) # Refresca el paciente para incluir la medición si es necesario
        new_patient.last_measurement = initial_measurement # Para que esté disponible inmediatamente
        return new_patient

    def add_tumor_measurement(self, patient_id: int, tumor_size: float, measurement_date: date):
        """
        Añade una nueva medición de tumor a un paciente existente.
        """
        new_measurement = TumorMeasurement(
            patient_id=patient_id,
            size_cm3=tumor_size,
            measurement_date=measurement_date
        )
        self.db.add(new_measurement)
        self.db.commit()
        self.db.refresh(new_measurement)
        return new_measurement

    def get_all_tumor_measurements_for_patient(self, patient_id: int):
        """
        Obtiene todas las mediciones de tumor para un paciente, ordenadas por fecha.
        """
        return self.db.query(TumorMeasurement)\
                   .filter(TumorMeasurement.patient_id == patient_id)\
                   .order_by(TumorMeasurement.measurement_date.asc())\
                   .all()

    # Puedes añadir más métodos si los necesitas, como actualizar datos de paciente, etc.