from pydantic import BaseModel, Field, field_validator
from datetime import date
from typing import Optional, List, Dict, Any

# --- LO QUE ENTRA (Request) ---

class MeasurementInput(BaseModel):
    size_cm3: float = Field(..., gt=0, description="Tamaño del tumor en cm3")
    measurement_date: date
    notes: Optional[str] = None

    @field_validator('measurement_date')
    def date_cannot_be_future(cls, v):
        if v > date.today():
            raise ValueError('La fecha de medición no puede estar en el futuro')
        return v

class PredictionRequest(BaseModel):
    identification_number: str = Field(..., min_length=1, max_length=50)
    name: Optional[str] = Field(None, max_length=100)
    date_of_birth: Optional[date] = None
    new_measurement: MeasurementInput
    projection_days: int = Field(365, ge=30, le=1825) # Proyección entre 1 mes y 5 años
    historical_data: List[Dict[str, Any]] = [] # [{'day': 0, 'size': 1.0, 'id': 5}, ...]

    @field_validator('date_of_birth')
    def birth_date_logic(cls, v):
        if v and v > date.today():
            raise ValueError('La fecha de nacimiento no puede ser futura')
        return v

# --- LO QUE SALE (Response) ---

class ModelFitResult(BaseModel):
    success: bool
    params: Optional[Dict[str, float]] = None
    r_squared: Optional[float] = None
    error: Optional[str] = None

# NUEVA CLASE para estructurar bien el análisis
class ModelAnalysisResult(BaseModel):
    exponential: ModelFitResult
    gompertz: ModelFitResult
    data_points: int

class PredictionResponse(BaseModel):
    patient_id: int
    identification_number: str
    total_measurements: int
    
    # CORRECCIÓN AQUÍ: Usamos la clase específica en lugar de Dict[str, ModelFitResult]
    model_analysis: ModelAnalysisResult
    
    projections: Dict[str, List[Dict[str, Any]]] 
    interpretation: str
    historical_data: List[Dict[str, Any]] = []