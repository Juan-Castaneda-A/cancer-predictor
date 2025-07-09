from datetime import date
from typing import Optional, Literal
from pydantic import BaseModel, Field, PositiveFloat, NonNegativeFloat

# Definimos los tipos de cáncer y subtipos esperados para validación
CancerType = Literal["Cáncer de Mama"]
SubtypeMammary = Literal["Triple Negativo", "HER2-positivo", "ER-positivo", "No-luminal", "Luminal"]
GradeType = Literal["Grado 1", "Grado 2", "Grado 3"]
ErPrStatus = Literal["Positivo", "Negativo", "Desconocido"]
Her2Status = Literal["Positivo", "Negativo", "Desconocido"]
MetastasisStatus = Literal["Si", "No", "Desconocido"]


class OtherFactors(BaseModel):
    """
    Esquema para factores adicionales que influyen en la predicción.
    Todos son opcionales y tienen validación de tipo y valor.
    """
    tipo_cancer: Optional[CancerType] = Field(
        default="Cáncer de Mama", # Valor por defecto si no se especifica
        description="Tipo principal de cáncer."
    )
    subtipo_molecular: Optional[SubtypeMammary] = Field(
        None, description="Subtipo molecular del cáncer (ej. Triple Negativo)."
    )
    grado_histopatologico: Optional[GradeType] = Field(
        None, description="Grado histopatológico del tumor."
    )
    er_pr: Optional[ErPrStatus] = Field(
        None, description="Estado de los receptores de estrógeno y progesterona."
    )
    her2: Optional[Her2Status] = Field(
        None, description="Estado del receptor HER2."
    )
    metastasis: Optional[MetastasisStatus] = Field(
        None, description="Presencia de metástasis (Si/No/Desconocido)."
    )

class PredictionRequest(BaseModel):
    """
    Esquema para la solicitud de predicción de tumor.
    Define los campos esperados, sus tipos y validaciones básicas.
    """
    identification_number: str = Field(..., min_length=1, max_length=50, description="Número de identificación único del paciente.")
    current_tumor_size: PositiveFloat = Field(..., description="Tamaño actual del tumor en cm³.")
    current_measurement_date: date = Field(..., description="Fecha de la medición actual del tumor (YYYY-MM-DD).")

    # Campos opcionales para nuevos pacientes
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Nombre completo del paciente (requerido para nuevos pacientes).")
    date_of_birth: Optional[date] = Field(None, description="Fecha de nacimiento del paciente (YYYY-MM-DD, requerido para nuevos pacientes).")

    # Umbral crítico
    #T_critical: PositiveFloat = Field(10.0, description="Umbral crítico de tamaño del tumor en cm³ para la predicción.")

    # Otros factores usando el esquema anidado
    other_factors: Optional[OtherFactors] = Field(default_factory=OtherFactors, description="Factores adicionales del paciente para refinar los parámetros del modelo.")

