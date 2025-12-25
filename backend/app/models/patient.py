from typing import List, Optional
from datetime import date
from sqlmodel import SQLModel, Field, Relationship

# Esto evita referencias circulares al importar
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .measurement import TumorMeasurement

class PatientBase(SQLModel):
    """Propiedades base compartidas (para creación y lectura)"""
    identification_number: str = Field(index=True, unique=True, max_length=50)
    name: str = Field(max_length=100)
    date_of_birth: date

class Patient(PatientBase, table=True):
    """Tabla de Base de Datos real"""
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Relación: Un paciente tiene muchas mediciones
    measurements: List["TumorMeasurement"] = Relationship(back_populates="patient")

class PatientCreate(PatientBase):
    """Modelo para recibir datos al crear (sin ID)"""
    pass