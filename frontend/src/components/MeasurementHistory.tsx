import { Trash2, Calendar, Activity } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

interface Measurement {
  day: number; // Día relativo (0, 60, etc)
  size: number;
  date?: string; // Fecha real si la tienes disponible en el objeto
  id?: number;   // ID real de la base de datos
}

interface HistoryProps {
  measurements: Measurement[]; // Ajustaremos esto según lo que devuelve tu API
  onDelete: (id: number) => void;
}

export function MeasurementHistory({ measurements, onDelete }: HistoryProps) {
  if (!measurements || measurements.length === 0) return null;

  return (
    <Card className="mt-6 shadow-sm border-slate-200">
      <CardHeader className="pb-3 border-b border-slate-100">
        <CardTitle className="text-lg font-semibold flex items-center gap-2">
          <Activity className="h-5 w-5 text-blue-600" />
          Historial de Mediciones
        </CardTitle>
      </CardHeader>
      <CardContent className="p-0">
        <Table>
          <TableHeader className="bg-slate-50">
            <TableRow>
              <TableHead className="w-[100px]"># Medición</TableHead>
              <TableHead>Fecha Relativa</TableHead>
              <TableHead>Volumen (cm³)</TableHead>
              <TableHead className="text-right">Acciones</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {measurements.map((m, index) => (
              <TableRow key={index}>
                <TableCell className="font-medium">
                  <Badge variant="outline" className="bg-slate-100">
                    {index + 1}
                  </Badge>
                </TableCell>
                <TableCell className="text-slate-600">
                  <div className="flex items-center gap-2">
                    <Calendar className="h-4 w-4 text-slate-400" />
                    Día {Math.round(m.day)}
                  </div>
                </TableCell>
                <TableCell className="font-bold text-slate-800">
                  {m.size.toFixed(2)} cm³
                </TableCell>
                <TableCell className="text-right">
                  {/* Solo mostramos borrar si tenemos ID (asumiendo que viene del backend) */}
                  <Button
                    variant="ghost"
                    size="sm"
                    className="text-red-500 hover:text-red-700 hover:bg-red-50"
                    onClick={() => onDelete(m.id || 0)} 
                    // Nota: Necesitamos asegurar que el backend devuelva el ID de la medición
                    // Por ahora es visual, luego conectamos la lógica
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}