import { ResponsiveLine } from "@nivo/line";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { PredictionResponse } from "@/types";

interface ChartProps {
  data: PredictionResponse;
}

export function TumorGrowthChart({ data }: ChartProps) {
  // 1. Transformar datos de tu API al formato que Nivo entiende
  const nivoData = [];

  if (data.projections.exponential) {
    nivoData.push({
      id: "Exponencial",
      data: data.projections.exponential.map((p) => ({ x: p.day, y: p.size })),
    });
  }

  if (data.projections.gompertz) {
    nivoData.push({
      id: "Gompertz",
      data: data.projections.gompertz.map((p) => ({ x: p.day, y: p.size })),
    });
  }

  return (
    <Card className="col-span-2 shadow-lg h-[500px]"> {/* Altura fija importante para gráficos */}
      <CardHeader>
        <CardTitle>Proyección de Crecimiento (365 días)</CardTitle>
      </CardHeader>
      <CardContent className="h-[400px] w-full">
        <ResponsiveLine
          data={nivoData}
          margin={{ top: 20, right: 110, bottom: 50, left: 60 }}
          xScale={{ type: "linear", min: 0, max: "auto" }} // Eje X lineal (días)
          yScale={{ type: "linear", min: 0, max: "auto", stacked: false, reverse: false }}
          axisBottom={{
            tickSize: 5,
            tickPadding: 5,
            tickRotation: 0,
            legend: "Días desde hoy",
            legendOffset: 36,
            legendPosition: "middle",
          }}
          axisLeft={{
            tickSize: 5,
            tickPadding: 5,
            tickRotation: 0,
            legend: "Tamaño (cm³)",
            legendOffset: -40,
            legendPosition: "middle",
          }}
          colors={{ scheme: "category10" }} // Colores automáticos bonitos
          pointSize={4}
          pointColor={{ theme: "background" }}
          pointBorderWidth={2}
          pointBorderColor={{ from: "serieColor" }}
          pointLabelYOffset={-12}
          useMesh={true} // Habilita tooltips interactivos al pasar el mouse
          enableGridX={false}
          curve="monotoneX" // Suaviza las líneas
          legends={[
            {
              anchor: "bottom-right",
              direction: "column",
              justify: false,
              translateX: 100,
              translateY: 0,
              itemsSpacing: 0,
              itemDirection: "left-to-right",
              itemWidth: 80,
              itemHeight: 20,
              itemOpacity: 0.75,
              symbolSize: 12,
              symbolShape: "circle",
              symbolBorderColor: "rgba(0, 0, 0, .5)",
              effects: [
                {
                  on: "hover",
                  style: {
                    itemBackground: "rgba(0, 0, 0, .03)",
                    itemOpacity: 1,
                  },
                },
              ],
            },
          ]}
        />
      </CardContent>
    </Card>
  );
}