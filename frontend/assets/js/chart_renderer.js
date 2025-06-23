// frontend/assets/js/chart_renderer.js

let tumorGrowthChartInstance = null; // Mantener una referencia a la instancia del gráfico

/**
 * Renderiza o actualiza el gráfico de crecimiento tumoral con Chart.js.
 * Ahora acepta los datos de ambos modelos (Exponencial y Gompertz)
 * y los parámetros necesarios para las líneas de referencia.
 * @param {Array<Array<number>>} exponentialCurveData - Array de [días, tamaño] para el modelo exponencial.
 * @param {Array<Array<number>>} gompertzCurveData - Array de [días, tamaño] para el modelo de Gompertz.
 * @param {number} T0_value - Tamaño inicial del tumor para la línea base.
 * @param {number} T_critical_value - Umbral crítico del tumor para la línea de referencia.
 */
function renderTumorGrowthChart(exponentialCurveData, gompertzCurveData, T0_value, T_critical_value) {
    const ctx = document.getElementById('tumorGrowthChart').getContext('2d');

    // Destruir la instancia anterior del gráfico si existe
    if (tumorGrowthChartInstance) {
        tumorGrowthChartInstance.destroy();
    }

    const datasets = [];

    // Datos para el modelo Exponencial
    if (exponentialCurveData && exponentialCurveData.length > 0) {
        datasets.push({
            label: 'Modelo Exponencial',
            data: exponentialCurveData.map(point => ({ x: point.x, y: point.y })),
            borderColor: 'rgb(75, 192, 192)',
            borderWidth: 2,
            fill: false,
            pointRadius: 0 // No mostrar puntos individuales
        });
    }

    // Datos para el modelo Gompertz
    if (gompertzCurveData && gompertzCurveData.length > 0) {
        datasets.push({
            label: 'Modelo Gompertz',
            data: gompertzCurveData.map(point => ({ x: point.x, y: point.y })),
            borderColor: 'rgb(255, 99, 132)',
            borderWidth: 2,
            fill: false,
            pointRadius: 0 // No mostrar puntos individuales
        });
    }

    // Añadir línea para el Tamaño Inicial (T0)
    datasets.push({
        label: 'Tamaño Inicial (T0)',
        data: [{ x: 0, y: T0_value }], // Sólo un punto para la etiqueta
        borderColor: 'rgb(54, 162, 235)',
        borderWidth: 2,
        borderDash: [5, 5],
        fill: false,
        pointRadius: 5,
        pointBackgroundColor: 'rgb(54, 162, 235)',
        type: 'scatter' // Usar tipo scatter para que no intente dibujar una línea entre T0 y T_critical
    });

    // Añadir línea para el Umbral Crítico (T_critical)
    // Se extiende horizontalmente a través de todo el rango X del gráfico
    const maxDays = Math.max(
        ...(exponentialCurveData || []).map(point => point[0]),
        ...(gompertzCurveData || []).map(point => point[0]),
        100 // Un valor mínimo para que la línea se vea si las curvas son cortas
    );

    datasets.push({
        label: 'Umbral Crítico',
        data: [{ x: 0, y: T_critical_value }, { x: maxDays, y: T_critical_value }],
        borderColor: 'rgb(255, 159, 64)',
        borderWidth: 2,
        borderDash: [5, 5],
        fill: false,
        pointRadius: 0
    });

    tumorGrowthChartInstance = new Chart(ctx, {
        type: 'line', // Tipo de gráfico principal
        data: {
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false, // Permite que el gráfico ajuste su tamaño al contenedor
            scales: {
                x: {
                    type: 'linear',
                    position: 'bottom',
                    title: {
                        display: true,
                        text: 'Días desde la Medición Actual'
                    },
                    min: 0 // Asegura que el eje X empiece en 0
                },
                y: {
                    title: {
                        display: true,
                        text: 'Tamaño del Tumor (cm³)'
                    },
                    min: 0 // Asegura que el eje Y empiece en 0
                }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            let label = context.dataset.label || '';
                            if (label) {
                                label += ': ';
                            }
                            if (context.parsed.y !== null) {
                                label += context.parsed.y.toFixed(2) + ' cm³';
                            }
                            return label;
                        }
                    }
                }
            }
        }
    });
}