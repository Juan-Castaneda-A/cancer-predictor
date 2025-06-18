// frontend/assets/js/chart_renderer.js

let tumorGrowthChartInstance = null; // Para guardar la instancia del gráfico

function renderTumorGrowthChart(curvePoints, T0_for_graph, T_critical, estimatedTime, timeUnit) {
    const ctx = document.getElementById('tumorGrowthChart').getContext('2d');

    const labels = curvePoints.map(p => p.x.toFixed(0)); // Tiempo en el eje X
    const dataPoints = curvePoints.map(p => p.y); // Tamaño del tumor en el eje Y

    // Líneas horizontales para T0 y T_critical
    const initialTumorLine = Array(labels.length).fill(T0_for_graph);
    const criticalThresholdLine = Array(labels.length).fill(T_critical);

    // Si ya existe una instancia de gráfico, destrúyela para crear una nueva
    if (tumorGrowthChartInstance) {
        tumorGrowthChartInstance.destroy();
    }

    // Calcular el punto en el eje X para el tiempo estimado
    // No necesitamos findIndex, solo el punto final del tiempo estimado

    let estimatedTimeValue = estimatedTime;
    if (timeUnit === "años") {
    estimatedTimeValue = estimatedTime * 365.25; // ✅ Convertir a días
}

    let estimatedTimePoint = [];
    if (estimatedTime > 0) { // Solo añadir si hay un tiempo estimado válido
        estimatedTimePoint = [{
            x: estimatedTimeValue, // Usar el valor exacto del tiempo estimado
            y: T_critical // Debe estar en el umbral crítico en ese tiempo
        }];
    }

    tumorGrowthChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Tamaño del Tumor (cm³)',
                data: dataPoints,
                borderColor: '#007bff', // Color principal de la curva
                backgroundColor: 'rgba(0, 123, 255, 0.1)',
                borderWidth: 2,
                pointRadius: 0, // No mostrar puntos individuales
                fill: false,
                tension: 0.1
            },
            {
                label: 'Tamaño Actual', 
                data: initialTumorLine,
                borderColor: 'rgba(255, 193, 7, 0.7)', // Amarillo
                borderDash: [5, 5],
                borderWidth: 1,
                pointRadius: 0,
                fill: false
            },
            {
                label: 'Umbral Crítico',
                data: criticalThresholdLine,
                borderColor: 'rgba(220, 53, 69, 0.7)', // Rojo
                borderDash: [5, 5],
                borderWidth: 1,
                pointRadius: 0,
                fill: false
            },
            // Nuevo dataset para el punto de tiempo estimado, solo si existe
            ...(estimatedTimePoint.length > 0 ? [{
                label: `Tiempo Estimado (${estimatedTime.toFixed(2)} ${timeUnit})`,
                data: estimatedTimePoint,
                borderColor: '#28a745', // Verde para el punto de predicción
                backgroundColor: '#28a745',
                borderWidth: 3,
                pointRadius: 8, // Hacer el punto visible
                pointStyle: 'circle',
                pointBackgroundColor: '#28a745',
                pointBorderColor: '#fff',
                pointBorderWidth: 2,
                fill: false,
                showLine: false // No conectar este punto con una línea
            }] : [])
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    title: {
                        display: true,
                        text: `Tiempo (días)` 
                    },
                    beginAtZero: true,
                    // Asegurarse de que el eje X abarque hasta el tiempo estimado + un margen
                    max: Math.max(curvePoints[curvePoints.length - 1].x, estimatedTime * 1.1) 
                },
                y: {
                    title: {
                        display: true,
                        text: 'Tamaño del Tumor (cm³)'
                    },
                    beginAtZero: true,
                    // Asegurarse de que el eje Y muestre hasta el umbral crítico o un poco más
                    suggestedMax: Math.max(T_critical * 1.2, T0_for_graph * 2, dataPoints.length > 0 ? Math.max(...dataPoints) * 1.1 : 0) 
                }
            },
            plugins: {
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    callbacks: {
                        title: function(context) {
                            return `Tiempo: ${context[0].label} ${timeUnit}`;
                        },
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
                },
                legend: {
                    display: true,
                    position: 'top'
                }
            }
        }
    });
}