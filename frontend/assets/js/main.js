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
// KGroup ya no necesita ser una referencia directa a un input, solo al div que lo contiene (si aún se usa para estilo)
const KGroup = document.getElementById('K-group'); // Se mantiene para ocultar el mensaje si es exponencial
const predictionForm = document.getElementById('predictionForm');
const calculateBtn = document.getElementById('calculate-btn');
const loadingMessage = document.getElementById('loading-message');
const formErrorMessage = document.getElementById('form-error-message');

// Nuevas referencias para los campos de "primera visita"
const isFirstVisitYes = document.getElementById('is_first_visit_yes');
const isFirstVisitNo = document.getElementById('is_first_visit_no');
const subsequentVisitFields = document.getElementById('subsequent-visit-fields');
const rDescription = document.getElementById('r-description'); // Para mostrar/ocultar descripción de 'r', K y umbral

// Nuevas referencias para mostrar los resultados detallados
const tiempoEstimadoSpan = document.getElementById('tiempo-estimado');
const unidadTiempoSpan = document.getElementById('unidad-tiempo');
const intervaloConfianzaSpan = document.getElementById('intervalo-confianza');
const currentCancerStageSpan = document.getElementById('current-cancer-stage'); 
const interpretationText = document.getElementById('interpretation-text');
const possibleTreatmentsText = document.getElementById('possible-treatments-text'); 
const mathFormulaDiv = document.getElementById('math-formula');
const paramsUsedPre = document.getElementById('params-used');
const patientDataSentPre = document.getElementById('patient-data-sent'); 
const disclaimerText = document.getElementById('disclaimer-text'); 

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
    
    // La descripción de r/K/umbral siempre se muestra, ya que los valores son internos
    rDescription.classList.remove('hidden'); 
    
    // El KGroup, que contenía el input K, ahora solo muestra una descripción general
    // Para el modelo exponencial, simplemente el mensaje de K y umbral crítico aplica
    // Para Gompertz, el backend usará K. No hay interacción directa con el input K aquí.

    // Asegurarse de que los campos de visitas subsecuentes estén ocultos al seleccionar el modelo
    // y que los campos de r bibliográfico estén visibles
    isFirstVisitYes.checked = true; // Por defecto a "Sí, es primera visita"
    toggleSubsequentVisitFields();

    showSection('prediction-form-section');
    scrollToSection('prediction-form-section');
}

function toggleSubsequentVisitFields() {
    const isFirstVisit = isFirstVisitYes.checked;
    if (isFirstVisit) {
        subsequentVisitFields.classList.add('hidden');
        // Quitar 'required' para que el formulario se pueda enviar si se cambia de "No" a "Sí"
        document.getElementById('previous_tumor_size_cm3').removeAttribute('required');
        document.getElementById('last_visit_date').removeAttribute('required');
        // Limpiar valores si se ocultan
        document.getElementById('previous_tumor_size_cm3').value = '';
        document.getElementById('last_visit_date').value = '';
    } else {
        subsequentVisitFields.classList.remove('hidden');
        // Hacer 'required' si es visita subsecuente
        document.getElementById('previous_tumor_size_cm3').setAttribute('required', 'true');
        document.getElementById('last_visit_date').setAttribute('required', 'true');
    }
    // Factores adicionales son siempre opcionales, no se tocan sus atributos 'required' aquí
}


function displayResults(data) {
    showSection('results-section');
    scrollToSection('results-section');

    tiempoEstimadoSpan.textContent = data.tiempo_estimado;
    unidadTiempoSpan.textContent = data.unidad_tiempo; 
    intervaloConfianzaSpan.textContent = data.intervalo_confianza;
    currentCancerStageSpan.textContent = data.estado_cancer_actual_t; 

    interpretationText.innerHTML = data.interpretacion_resultado; 
    possibleTreatmentsText.innerHTML = data.posibles_tratamientos; 
    disclaimerText.innerHTML = data.descargo_responsabilidad; 

    // Renderizar la fórmula LaTeX con MathJax
    mathFormulaDiv.textContent = `$$${data.ecuacion_latex}$$`;
    MathJax.typesetPromise([mathFormulaDiv]).then(() => {
        // Callback después de MathJax, si es necesario
    }).catch((err) => console.error('MathJax rendering failed:', err));

    // Mostrar los parámetros usados y los datos del paciente enviados
    paramsUsedPre.textContent = JSON.stringify(data.parametros_usados, null, 2);
    patientDataSentPre.textContent = JSON.stringify(data.datos_paciente_enviados, null, 2);


    // Llamar a la función de renderizado del gráfico de chart_renderer.js
    // El T0 para la gráfica es el "initial_tumor_size_cm3" (tamaño actual)
    renderTumorGrowthChart(data.puntos_curva, data.parametros_usados.T0_calculo, data.parametros_usados.T_umbral_critico, data.tiempo_estimado, data.unidad_tiempo);
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

// Event listeners para los radio buttons de 'is_first_visit'
isFirstVisitYes.addEventListener('change', toggleSubsequentVisitFields);
isFirstVisitNo.addEventListener('change', toggleSubsequentVisitFields);


predictionForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    clearFormError();
    showLoading(true);

    const formData = new FormData(predictionForm);
    const dataToSend = {
        model_type: selectedModel
    };

    // Recoger todos los campos del formulario, algunos con nombres actualizados
    for (const [key, value] of formData.entries()) {
        // Convertir a booleano el is_first_visit
        if (key === 'is_first_visit') {
            dataToSend[key] = (value === 'true');
        } else if (value) { // Solo añadir si hay un valor y no es un campo vacío
            // Asegúrate de que los IDs del HTML coincidan con los esperados en el backend
            // T0 del formulario es 'initial_tumor_size_cm3'
            if (['initial_tumor_size_cm3', 'previous_tumor_size_cm3'].includes(key)) {
                dataToSend[key] = parseFloat(value);
            } else if (['edad', 'dias_tratamiento'].includes(key)) {
                dataToSend[key] = parseInt(value);
            } else {
                dataToSend[key] = value;
            }
        }
    }
    
    // K_value y umbral_critico_cm3 ya no vienen del frontend, el backend los manejará.
    // Asegurarse de que el campo K_value no se envíe si no existe o es irrelevante
    if (dataToSend.hasOwnProperty('K_value')) {
        delete dataToSend.K_value;
    }
    if (dataToSend.hasOwnProperty('umbral_critico_cm3')) {
        delete dataToSend.umbral_critico_cm3;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/predict`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(dataToSend)
        });

        const result = await response.json();

        if (response.ok) {
            displayResults(result);
        } else {
            displayFormError(result.error || 'Error desconocido al calcular la predicción.');
        }
    } catch (error) {
        console.error('Error de conexión:', error);
        displayFormError('No se pudo conectar con el servidor. Asegúrate de que el backend esté ejecutándose y la URL sea correcta.');
    } finally {
        showLoading(false);
    }
});

btnNewPrediction.addEventListener('click', () => {
    predictionForm.reset(); // Limpiar el formulario
    showSection('introduction'); // Volver a la sección de introducción
    scrollToSection('introduction');
    // Reiniciar estado visual del formulario y campos condicionales
    isFirstVisitYes.checked = true; // Restablecer a primera visita por defecto
    toggleSubsequentVisitFields();
    // Restablecer la visibilidad de la descripción de r/K/umbral
    rDescription.classList.remove('hidden'); 
});

// Inicialización: mostrar solo la sección de introducción al cargar la página
document.addEventListener('DOMContentLoaded', () => {
    showSection('introduction');
    // Asegurarse de que los campos de visita subsecuente estén ocultos al cargar la página
    toggleSubsequentVisitFields(); 
    // Asegurarse de que la descripción de r/K/umbral esté visible inicialmente
    rDescription.classList.remove('hidden');
});