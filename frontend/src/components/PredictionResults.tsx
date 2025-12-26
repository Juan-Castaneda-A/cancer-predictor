import type { PredictionResponse } from "@/types";
import { TumorGrowthChart } from "./charts/TumorGrowthChart";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Activity, TrendingUp, AlertCircle, Printer, Download } from "lucide-react";
import { Button } from "@/components/ui/button";

interface ResultsProps {
  data: PredictionResponse;
}

export function PredictionResults({ data }: ResultsProps) {
  const handlePrint = () => {
    window.print();
  };
  const expR2 = data.model_analysis.exponential.r_squared ?? 0;
  const gomR2 = data.model_analysis.gompertz.r_squared ?? 0;
  const betterModel = gomR2 > expR2 ? "Gompertz" : "Exponencial";

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">

      {/* --- NUEVO ENCABEZADO DE RESULTADOS --- */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-white p-4 rounded-lg border border-slate-200 shadow-sm print:hidden">
        <div>
          <h2 className="text-2xl font-bold text-slate-900">Reporte de Proyección</h2>
          <p className="text-slate-500 text-sm">
            ID Paciente: <span className="font-mono font-medium text-slate-700">{data.identification_number}</span>
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={handlePrint}>
            <Printer className="mr-2 h-4 w-4" /> Imprimir / PDF
          </Button>
        </div>
      </div>

      {/* 1. Interpretación Principal */}
      <div className="bg-blue-50 border-l-4 border-blue-500 p-4 rounded-md text-blue-900 shadow-sm">
        <div className="flex items-center">
          <AlertCircle className="w-5 h-5 mr-2" />
          <span className="font-bold text-lg">Interpretación del Modelo</span>
        </div>
        <p className="mt-2 text-md">{data.interpretation}</p>
      </div>

      {/* 2. Tarjetas de Métricas (KPIs) */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Mejor Ajuste</CardTitle>
            <TrendingUp className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{betterModel}</div>
            <p className="text-xs text-muted-foreground">Basado en R²</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Precisión (R²)</CardTitle>
            <Activity className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{(Math.max(expR2, gomR2) * 100).toFixed(1)}%</div>
            <p className="text-xs text-muted-foreground">Confianza estadística</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Mediciones</CardTitle>
            <Activity className="h-4 w-4 text-orange-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data.total_measurements}</div>
            <p className="text-xs text-muted-foreground">Puntos históricos</p>
          </CardContent>
        </Card>
      </div>

      {/* 3. Gráfica de Nivo */}
      <TumorGrowthChart data={data} />
    </div>
  );
}