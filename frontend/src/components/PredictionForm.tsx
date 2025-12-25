import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { Loader2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
  FormDescription, // Importado por si acaso, pero usaremos <p> para el texto suelto
} from "@/components/ui/form";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

// 1. Esquema de Validación
const formSchema = z.object({
  identification_number: z.string().min(1, "El ID es obligatorio"),
  name: z.string().optional(),
  date_of_birth: z.string().optional(),
  // z.coerce.number() convierte el string del input a número automáticamente
  size_cm3: z.coerce.number().min(0.01, "El tamaño debe ser mayor a 0"),
  measurement_date: z.string().min(1, "La fecha es obligatoria"),
});

// 2. Tipo inferido
type FormValues = z.infer<typeof formSchema>;

interface PredictionFormProps {
  onSubmit: (values: FormValues) => void;
  isLoading: boolean;
}

export function PredictionForm({ onSubmit, isLoading }: PredictionFormProps) {
  // 3. Inicialización del formulario
  const form = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      identification_number: "",
      name: "",
      date_of_birth: "",
      size_cm3: 0,
      measurement_date: new Date().toISOString().split('T')[0],
    },
  });

  return (
    <Card className="w-full max-w-md shadow-lg border-t-4 border-t-blue-600">
      <CardHeader>
        <CardTitle className="text-2xl font-bold text-slate-800">Nueva Medición</CardTitle>
        <CardDescription>
          Ingrese los datos del paciente para calcular la proyección matemática.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-5">
            
            {/* Campo ID */}
            <FormField
              control={form.control}
              name="identification_number"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>ID del Paciente</FormLabel>
                  <FormControl>
                    <Input placeholder="Ej: P-00123" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* Fila: Nombre y Fecha de Nacimiento */}
            <div className="grid grid-cols-2 gap-4">
                <FormField
                  control={form.control}
                  name="name"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Nombre</FormLabel>
                      <FormControl>
                        <Input placeholder="Opcional" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="date_of_birth"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Nacimiento</FormLabel>
                      <FormControl>
                        <Input type="date" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
            </div>
            
            {/* CORRECCIÓN AQUÍ: Usamos un <p> normal en lugar de <FormDescription> suelto */}
            <p className="text-[0.8rem] text-muted-foreground text-center -mt-2 mb-2">
                * Nombre y Nacimiento solo requeridos para pacientes nuevos.
            </p>

            {/* Fila: Tamaño y Fecha Medición */}
            <div className="grid grid-cols-2 gap-4 pt-2 border-t border-slate-100">
                <FormField
                control={form.control}
                name="size_cm3"
                render={({ field }) => (
                    <FormItem>
                    <FormLabel>Tamaño Tumor (cm³)</FormLabel>
                    <FormControl>
                        <Input type="number" step="0.01" {...field} />
                    </FormControl>
                    <FormMessage />
                    </FormItem>
                )}
                />

                <FormField
                control={form.control}
                name="measurement_date"
                render={({ field }) => (
                    <FormItem>
                    <FormLabel>Fecha Medición</FormLabel>
                    <FormControl>
                        <Input type="date" {...field} />
                    </FormControl>
                    <FormMessage />
                    </FormItem>
                )}
                />
            </div>

            <Button type="submit" className="w-full text-lg bg-blue-600 hover:bg-blue-700 mt-4" disabled={isLoading}>
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Calculando...
                </>
              ) : (
                "Calcular Proyección"
              )}
            </Button>
          </form>
        </Form>
      </CardContent>
    </Card>
  );
}