import { useState } from "react";
import api from "@/api/axios";
import { PredictionForm } from "@/components/PredictionForm";
import { PredictionResults } from "@/components/PredictionResults";
import type { PredictionResponse, PredictionRequest } from "@/types"; // Importante el 'type'
import { Toaster } from "@/components/ui/sonner";
import { Activity } from "lucide-react";
import { MeasurementHistory } from "@/components/MeasurementHistory";
import { toast } from "sonner"; // Feedback visual importante

function App() {
  const [data, setData] = useState<PredictionResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handlePredict = async (formData: any) => {
    setLoading(true);
    setError(null);
    setData(null);

    try {
      // --- AQUÍ ESTABA EL ERROR ---
      // Faltaba enviar date_of_birth al backend
      const requestBody: PredictionRequest = {
        identification_number: formData.identification_number,
        name: formData.name || undefined,

        // ¡ESTA LÍNEA FALTABA!:
        date_of_birth: formData.date_of_birth || undefined,

        new_measurement: {
          size_cm3: formData.size_cm3,
          measurement_date: formData.measurement_date,
        },
        projection_days: 365
      };

      const response = await api.post<PredictionResponse>("/predict", requestBody);
      setData(response.data);

    } catch (err: any) {
      console.error(err);
      // Extraemos el mensaje de error exacto del backend
      setError(
        err.response?.data?.detail || "Error al conectar con el servidor de IA."
      );
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteMeasurement = async (id: number) => {
    if (!confirm("¿Estás seguro de eliminar esta medición? Esto recalculará el modelo.")) return;

    try {
      await api.delete(`/predict/measurements/${id}`); // Ajusta la URL según tu backend
      toast.success("Medición eliminada correctamente");
      // Aquí deberías recargar los datos o limpiar el estado
      setData(null);
    } catch (error) {
      toast.error("Error al eliminar la medición");
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 font-sans pb-10">
      <header className="bg-white border-b border-slate-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="bg-blue-600 p-2 rounded-lg">
              <Activity className="h-6 w-6 text-white" />
            </div>
            <h1 className="text-xl font-bold text-slate-800">Cancer Predictor AI <span className="text-xs bg-slate-100 text-slate-500 px-2 py-1 rounded ml-2">v2.0 SciPy</span></h1>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          <div className="lg:col-span-4 space-y-6">
            <div className="sticky top-24">
              <h2 className="text-lg font-semibold mb-4">Ingreso de Datos Clínicos</h2>
              <PredictionForm onSubmit={handlePredict} isLoading={loading} />
              {error && (
                <div className="mt-4 p-4 bg-red-50 text-red-700 rounded-md border border-red-200 shadow-sm animate-in fade-in slide-in-from-top-2">
                  <strong>Error:</strong> {error}
                </div>
              )}
            </div>
          </div>

          <div className="lg:col-span-8">
            {data ? (
              <>
                <PredictionResults data={data} />

                {/* NUEVA TABLA DE HISTORIAL */}
                <MeasurementHistory
                  measurements={data.historical_data}
                  onDelete={handleDeleteMeasurement}
                />
              </>
            ) : (
              <div className="h-full min-h-[400px] flex flex-col items-center justify-center text-slate-400 border-2 border-dashed border-slate-300 rounded-xl bg-slate-50/50">
                <Activity className="h-16 w-16 mb-4 opacity-20" />
                <p className="text-lg font-medium">Esperando datos del paciente...</p>
                <p className="text-sm">Ingrese una medición para generar el modelo matemático.</p>
              </div>
            )}
          </div>
        </div>
      </main>
      <Toaster />
    </div>
  );
}

export default App;