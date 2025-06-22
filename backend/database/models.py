from sqlalchemy import create_engine, Column, Integer, String, Date, Numeric, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func # Para las funciones de fecha/hora de la DB
import os

# Base declarativa para tus modelos
Base = declarative_base()

class Patient(Base):
    __tablename__ = 'patients'

    id = Column(Integer, primary_key=True)
    identification_number = Column(String, unique=True, nullable=False) # Cédula/Identificación
    name = Column(String, nullable=False)
    date_of_birth = Column(Date, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relación con las mediciones de tumores
    # 'uselist=True' es el default para One-to-Many
    tumor_measurements = relationship("TumorMeasurement", back_populates="patient",
                                      order_by="TumorMeasurement.measurement_date")

    def __repr__(self):
        return f"<Patient(id={self.id}, name='{self.name}', id_num='{self.identification_number}')>"

class TumorMeasurement(Base):
    __tablename__ = 'tumor_measurements'

    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey('patients.id'), nullable=False)
    size_cm3 = Column(Numeric, nullable=False) # Tamaño del tumor en cm^3
    measurement_date = Column(Date, nullable=False) # Fecha de la medición
    notes = Column(String) # Campo opcional para notas
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relación inversa a Patient
    patient = relationship("Patient", back_populates="tumor_measurements")

    def __repr__(self):
        return f"<TumorMeasurement(id={self.id}, patient_id={self.patient_id}, size={self.size_cm3}, date='{self.measurement_date}')>"

# Configuración de la base de datos
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    # SQLAlchemy 2.0 requiere que el prefijo sea postgresql://
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)

# Crea las tablas en la base de datos (solo si no existen)
def create_tables():
    if DATABASE_URL:
        Base.metadata.create_all(engine)
        print("Tablas creadas o ya existentes en la base de datos.")
    else:
        print("DATABASE_URL no está configurada. No se crearán tablas.")

# Crea una sesión para interactuar con la base de datos
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Función para obtener una sesión de la base de datos (uso en rutas/servicios)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()