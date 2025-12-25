from typing import Optional
from datetime import date
from sqlmodel import SQLModel, Field, Relationship

# Evitar referencia circular
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .patient import Patient

class TumorMeasurementBase(SQLModel):
    size_cm3: float
    measurement_date: date
    notes: Optional[str] = None

class TumorMeasurement(TumorMeasurementBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Clave foránea: Conecta con la tabla 'patient'
    patient_id: int = Field(foreign_key="patient.id")
    
    # Relación inversa: Permite acceder a .patient desde la medición
    patient: Optional["Patient"] = Relationship(back_populates="measurements")

class TumorMeasurementCreate(TumorMeasurementBase):
    pass