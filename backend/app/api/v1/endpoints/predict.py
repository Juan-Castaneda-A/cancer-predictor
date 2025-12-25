from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.db.session import get_session
from app.models import Patient, TumorMeasurement
from app.schemas.prediction import PredictionRequest, PredictionResponse
from app.services.prediction_service import PredictionService

router = APIRouter()

@router.post("/predict", response_model=PredictionResponse)
def generate_prediction(
    request: PredictionRequest, 
    session: Session = Depends(get_session)
):
    # 1. Buscar si el paciente ya existe
    statement = select(Patient).where(Patient.identification_number == request.identification_number)
    patient = session.exec(statement).first()

    # 2. Si no existe, crearlo (Solo si mandaron nombre y fecha nacimiento)
    if not patient:
        if not request.name or not request.date_of_birth:
            raise HTTPException(status_code=400, detail="Paciente nuevo: Se requiere nombre y fecha de nacimiento.")
        
        patient = Patient(
            identification_number=request.identification_number,
            name=request.name,
            date_of_birth=request.date_of_birth
        )
        session.add(patient)
        session.commit()
        session.refresh(patient)

    # 3. Guardar la nueva medición
    new_meas = TumorMeasurement(
        patient_id=patient.id,
        size_cm3=request.new_measurement.size_cm3,
        measurement_date=request.new_measurement.measurement_date,
        notes=request.new_measurement.notes
    )
    session.add(new_meas)
    session.commit()

    # 4. Recuperar TODO el historial clínico para el análisis matemático
    #    (SQLModel carga la relación .measurements automáticamente o vía query)
    statement_history = select(TumorMeasurement).where(TumorMeasurement.patient_id == patient.id)
    history = session.exec(statement_history).all()

    dates = [m.measurement_date for m in history]
    sizes = [m.size_cm3 for m in history]

    # 5. INVOCAR AL CEREBRO MATEMÁTICO (SciPy) 🧠
    service = PredictionService()
    fit_results = service.fit_models(dates, sizes)
    projections = service.predict_future(fit_results, days_ahead=request.projection_days)

    # 6. Generar interpretación automática
    interpretation = "Análisis realizado. "
    if fit_results.get("data_points", 0) < 2:
        interpretation += "Se necesitan más mediciones para una tendencia confiable."
    else:
        r2_exp = fit_results["exponential"].get("r_squared", 0)
        r2_gom = fit_results["gompertz"].get("r_squared", 0)
        
        if r2_gom > r2_exp:
            interpretation += f"El modelo Gompertz se ajusta mejor (R²={r2_gom:.2f})."
        else:
            interpretation += f"El modelo Exponencial se ajusta mejor (R²={r2_exp:.2f})."

    return PredictionResponse(
        patient_id=patient.id,
        identification_number=patient.identification_number,
        total_measurements=len(history),
        model_analysis=fit_results,
        projections=projections,
        interpretation=interpretation
    )