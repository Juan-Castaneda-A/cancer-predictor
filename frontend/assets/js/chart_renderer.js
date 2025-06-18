// frontend/assets/js/chart_renderer.js

let tumorGrowthChartInstance = null; // Para guardar la instancia del gráfico

function renderTumorGrowthChart(curvePoints, T0, T_critical) {
    const ctx = document.getElementById('tumorGrowthChart').getContext('2d');

    const labels = curvePoints.map(p => p.x.toFixed(0)); // Tiempo en el eje X
    const dataPoints = curvePoints.map(p => p.y); // Tamaño del tumor en el eje Y

    // Líneas horizontales para T0 y T_critical
    const initialTumorLine = Array(labels.length).fill(T0);
    const criticalThresholdLine = Array(labels.length).fill(T_critical);

    // Si ya existe una instancia de gráfico, destrúyela para crear una nueva
    if (tumorGrowthChartInstance) {
        tumorGrowthChartInstance.destroy();
    }

<<<<<<< HEAD
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

=======
>>>>>>> parent of a831574 (fase2)
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
                label: 'Tamaño Inicial',
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
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    title: {
                        display: true,
<<<<<<< HEAD
                        text: `Tiempo (días)` 
                    },
                    beginAtZero: true,
                    // Asegurarse de que el eje X abarque hasta el tiempo estimado + un margen
                    max: Math.max(curvePoints[curvePoints.length - 1].x, estimatedTime * 1.1) 
=======
                        text: 'Tiempo (días)'
                    }
>>>>>>> parent of a831574 (fase2)
                },
                y: {
                    title: {
                        display: true,
                        text: 'Tamaño del Tumor (cm³)'
                    },
                    beginAtZero: true,
                    // Asegurarse de que el eje Y muestre hasta el umbral crítico o un poco más
                    suggestedMax: Math.max(T_critical * 1.2, T0 * 2) 
                }
            },
            plugins: {
                tooltip: {
                    mode: 'index',
                    intersect: false
                },
                legend: {
                    display: true,
                    position: 'top'
                }
            }
        }
    });
}