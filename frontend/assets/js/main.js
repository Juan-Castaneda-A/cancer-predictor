// frontend/assets/js/main.js

const API_BASE_URL = 'https://cancer-predictor-ed.onrender.com/api'; // Asegúrate que esta URL coincida con tu backend

// Referencias a elementos del DOM
const introductionSection = document.getElementById('introduction');
const predictionFormSection = document.getElementById('prediction-form-section');
const resultsSection = document.getElementById('results-section');
const aboutSection = document.getElementById('about-section');

const btnExponential = document.getElementById('btnExponential');
const btnGompertz = document.getElementById('btnGompertz');
const btnCalibrate = document.getElementById('btnCalibrate'); // Deshabilitado por ahora

const modelNameSpan = document.getElementById('model-name');
const KGroup = document.getElementById('K-group');
const predictionForm = document.getElementById('predictionForm');
const calculateBtn = document.getElementById('calculate-btn');
const loadingMessage = document.getElementById('loading-message');
const formErrorMessage = document.getElementById('form-error-message');

const tiempoEstimadoSpan = document.getElementById('tiempo-estimado');
const unidadTiempoSpan = document.getElementById('unidad-tiempo');
const intervaloConfianzaSpan = document.getElementById('intervalo-confianza');
const interpretationText = document.getElementById('interpretation-text');
const mathFormulaDiv = document.getElementById('math-formula');
const paramsUsedPre = document.getElementById('params-used');

const btnNewPrediction = document.getElementById('btnNewPrediction');
const btnExportPdf = document.getElementById('btnExportPdf'); // Deshabilitado por ahora

let selectedModel = ''; // Para guardar el modelo seleccionado globalmente

// --- Funciones de control de UI ---
function showSection(sectionId) {
    introductionSection.classList.add('hidden');
    predictionFormSection.classList.add('hidden');
    resultsSection.classList.add('hidden');
    aboutSection.classList.add('hidden'); // Ocultar también la sección "Acerca de" por defecto

    document.getElementById(sectionId).classList.remove('hidden');
}

function scrollToSection(sectionId) {
    const section = document.getElementById(sectionId);
    if (section) {
        section.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
}

function updateFormForModel(model) {
    selectedModel = model;
    modelNameSpan.textContent = model === 'exponencial' ? 'Exponencial' : 'Gompertz';
    if (model === 'exponencial') {
        KGroup.classList.add('hidden');
        document.getElementById('K').removeAttribute('required');
    } else { // Gompertz
        KGroup.classList.remove('hidden');
        document.getElementById('K').setAttribute('required', 'true');
    }
    showSection('prediction-form-section');
    scrollToSection('prediction-form-section');
}

function displayResults(data) {
    showSection('results-section');
    scrollToSection('results-section');

    tiempoEstimadoSpan.textContent = data.tiempo_estimado;
    unidadTiempoSpan.textContent = data.unidad;
    intervaloConfianzaSpan.textContent = data.intervalo_confianza;
    paramsUsedPre.textContent = JSON.stringify(data.parametros_usados, null, 2);

    interpretationText.innerHTML = `Utilizando el **Modelo ${data.modelo_usado.charAt(0).toUpperCase() + data.modelo_usado.slice(1)}** con los parámetros proporcionados, el tamaño del tumor se estima que alcanzará el umbral crítico de **${data.parametros_usados.T_critical} cm³** en aproximadamente **${data.tiempo_estimado} ${data.unidad}**.`;

    // Renderizar la fórmula LaTeX con MathJax
    mathFormulaDiv.textContent = `$$${data.ecuacion_latex}$$`;
    MathJax.typesetPromise([mathFormulaDiv]).then(() => {
        // Callback después de MathJax, si es necesario
    }).catch((err) => console.error('MathJax rendering failed:', err));


    // Llamar a la función de renderizado del gráfico de chart_renderer.js
    renderTumorGrowthChart(data.puntos_curva, data.parametros_usados.T0, data.parametros_usados.T_critical);
}

function showLoading(show) {
    loadingMessage.classList.toggle('hidden', !show);
    calculateBtn.disabled = show;
}

function displayFormError(message) {
    formErrorMessage.textContent = message;
    formErrorMessage.classList.remove('hidden');
}

function clearFormError() {
    formErrorMessage.classList.add('hidden');
    formErrorMessage.textContent = '';
}

// --- Event Listeners ---
btnExponential.addEventListener('click', () => updateFormForModel('exponencial'));
btnGompertz.addEventListener('click', () => updateFormForModel('gompertz'));

predictionForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    clearFormError();
    showLoading(true);

    const formData = new FormData(predictionForm);
    const data = {
        model_type: selectedModel
    };

    // Recoger todos los campos del formulario
    for (const [key, value] of formData.entries()) {
        if (value) { // Solo añadir si hay un valor
            if (['T0', 'r', 'K', 'T_critical'].includes(key)) {
                data[key] = parseFloat(value);
            } else if (['dias_tratamiento', 'edad'].includes(key)) {
                data[key] = parseInt(value);
            } else {
                data[key] = value;
            }
        }
    }

    // Asegurarse de que K sea null si es exponencial y no fue llenado
    if (selectedModel === 'exponencial' && !data.K) {
        data.K = null;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/predict`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (response.ok) {
            displayResults(result);
        } else {
            displayFormError(result.error || 'Error desconocido al calcular la predicción.');
        }
    } catch (error) {
        console.error('Error de conexión:', error);
        displayFormError('No se pudo conectar con el servidor. Asegúrate de que el backend esté ejecutándose.');
    } finally {
        showLoading(false);
    }
});

btnNewPrediction.addEventListener('click', () => {
    predictionForm.reset(); // Limpiar el formulario
    showSection('introduction'); // Volver a la sección de introducción
    scrollToSection('introduction');
    // Reiniciar estado visual del formulario si es necesario
    KGroup.classList.add('hidden'); 
});

// Inicialización: mostrar solo la sección de introducción al cargar la página
document.addEventListener('DOMContentLoaded', () => {
    showSection('introduction');
});