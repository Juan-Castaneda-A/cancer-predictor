// src/types/index.ts

export interface MeasurementInput {
    size_cm3: number;
    measurement_date: string;
    notes?: string;
}

export interface PredictionRequest {
    identification_number: string;
    name?: string;
    date_of_birth?: string;
    new_measurement: {
        size_cm3: number;
        measurement_date: string;
        notes?: string;
    };
    projection_days: number;
}

export interface ModelParams {
    V0?: number;
    r?: number;
    K?: number;
}

export interface ModelFitResult {
    success: boolean;
    params?: Record<string, number>;
    r_squared?: number;
    error?: string;
}

export interface ProjectionPoint {
    day: number;
    size: number;
}

// ESTA ES LA QUE DABA ERROR. Asegúrate de que diga "export interface"
export interface PredictionResponse {
    patient_id: number;
    identification_number: string;
    total_measurements: number;
    interpretation: string;
  
    model_analysis: {
        exponential: ModelFitResult;
        gompertz: ModelFitResult;
        data_points: number;
    };
  
    projections: {
        exponential?: Array<{ day: number; size: number }>;
        gompertz?: Array<{ day: number; size: number }>;
    };

  // --- ESTO ES LO QUE FALTABA ---
    historical_data: Array<{
        day: number;
        size: number;
        id: number;
        date: string;
    }>;
}

