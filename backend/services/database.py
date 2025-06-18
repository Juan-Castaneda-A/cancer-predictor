# database.py
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

# Define el motor de la base de datos SQLite por defecto.
# En Render, usaremos una variable de entorno DATABASE_URL para PostgreSQL.
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://cancer_mama_user:tNPnmF157Oht5CxbLr6LiH4s9p4VBG9R@dpg-d19h65ripnbc73ekptc0-a.oregon-postgres.render.com/cancer_mama")

engine = create_engine(DATABASE_URL)
Base = declarative_base()

# Define el modelo de la tabla Paciente
class Paciente(Base):
    __tablename__ = "pacientes"

    id = Column(Integer, primary_key=True, index=True)
    doctor_code = Column(String, index=True) # Para asociar pacientes a un doctor simulado
    identificacion = Column(String, unique=True, index=True, nullable=False)
    nombre_paciente = Column(String, nullable=False)
    sexo = Column(String)
    edad = Column(Integer)

    visitas = relationship("Visita", back_populates="paciente", order_by="Visita.fecha_visita")

    def __repr__(self):
        return f"<Paciente(id={self.id}, identificacion='{self.identificacion}', nombre='{self.nombre_paciente}')>"

# Define el modelo de la tabla Visita
class Visita(Base):
    __tablename__ = "visitas"

    id = Column(Integer, primary_key=True, index=True)
    paciente_id = Column(Integer, ForeignKey("pacientes.id"))
    fecha_visita = Column(DateTime, default=datetime.utcnow)
    initial_tumor_size_cm3 = Column(Float)
    r_calculado = Column(Float)
    K_calculado = Column(Float)
    T_umbral_critico = Column(Float)
    model_type = Column(String)
    tiempo_estimado_dias = Column(Float)
    intervalo_confianza = Column(String)
    fecha_diagnostico = Column(DateTime, nullable=True)
    dias_tratamiento = Column(Integer, nullable=True)
    estadio = Column(String, nullable=True)
    grado_histopatologico = Column(String, nullable=True)
    er_pr = Column(String, nullable=True)
    tipo_cancer = Column(String, nullable=True)
    her2 = Column(String, nullable=True)
    metastasis = Column(String, nullable=True)
    
    paciente = relationship("Paciente", back_populates="visitas")

    def __repr__(self):
        return f"<Visita(id={self.id}, paciente_id={self.paciente_id}, fecha='{self.fecha_visita}', tumor_size={self.initial_tumor_size_cm3})>"

# Crea todas las tablas en la base de datos (solo si no existen)
# Esto es útil para el primer despliegue o en desarrollo local
Base.metadata.create_all(engine)

# Crea una sesión para interactuar con la base de datos
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Función de utilidad para obtener una sesión de DB
def get_db():
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()