const API_BASE_URL = 'https://cancer-predictor-ed.onrender.com/api'; //backend

// Referencias a elementos del DOM
const introductionSection = document.getElementById('introduction');
const predictionFormSection = document.getElementById('prediction-form-section');
const resultsSection = document.getElementById('results-section');
const btnStartPrediction = document.getElementById('btnStartPrediction');
const predictionForm = document.getElementById('predictionForm');
const calculateBtn = document.getElementById('calculate-btn');
const loadingMessage = document.getElementById('loading-message');
const formErrorMessage = document.getElementById('form-error-message');
const btnNewPrediction = document.getElementById('btnNewPrediction');

// Referencias a campos del formulario
const identificationNumberInput = document.getElementById('identification_number');
const patientNameInput = document.getElementById('patient_name');
const dateOfBirthInput = document.getElementById('date_of_birth');
const currentTumorSizeInput = document.getElementById('current_tumor_size');
const currentMeasurementDateInput = document.getElementById('current_measurement_date');
const tipoCancerSelect = document.getElementById('tipo_cancer');
const subtipoMolecularSelect = document.getElementById('subtipo_molecular');
const gradoHistopatologicoSelect = document.getElementById('grado_histopatologico');
const erPrSelect = document.getElementById('er_pr');
const her2Select = document.getElementById('her2');
const metastasisSelect = document.getElementById('metastasis');

// Referencias para mostrar resultados
const patientInfoDiv = document.getElementById('patient-info-display');
const parametersUsedContainer = document.getElementById('parameters-used-container');
const modelResultsSection = document.getElementById('model-results-section');
const predictionStatusMessage = document.getElementById('prediction-status-message');
const exponentialResultsDiv = document.getElementById('exponential-results');
const gompertzResultsDiv = document.getElementById('gompertz-results');
const expTiempoEstimadoSpan = document.getElementById('exp-tiempo-estimado');
const expUnidadTiempoSpan = document.getElementById('exp-unidad-tiempo');
const expIntervaloConfianzaSpan = document.getElementById('exp-intervalo-confianza');
const expFormulaDiv = document.getElementById('exp-math-formula');
const expNotesP = document.getElementById('exp-notes');
const gomTiempoEstimadoSpan = document.getElementById('gom-tiempo-estimado');
const gomUnidadTiempoSpan = document.getElementById('gom-unidad-tiempo');
const gomIntervaloConfianzaSpan = document.getElementById('gom-intervalo-confianza');
const gomFormulaDiv = document.getElementById('gom-math-formula');
const gomNotesP = document.getElementById('gom-notes');
const paramsT0Display = document.getElementById('params-T0');
const paramsTcritExpDisplay = document.getElementById('params-Tcrit-exp');
const paramsTcritGomDisplay = document.getElementById('params-Tcrit-gom');
const paramsRFinalDisplay = document.getElementById('params-r-final');
const paramsKFinalDisplay = document.getElementById('params-K-final');
const paramsREmpiricalDisplay = document.getElementById('params-r-empirical');
const paramsRBibliographicDisplay = document.getElementById('params-r-bibliographic');


// --- Funciones de control de UI ---
function showSection(sectionId) {
    introductionSection.classList.add('hidden');
    predictionFormSection.classList.add('hidden');
    resultsSection.classList.add('hidden');
    document.getElementById(sectionId).classList.remove('hidden');
}

function scrollToSection(sectionId) {
    const section = document.getElementById(sectionId);
    if (section) {
        section.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
}

function displayResults(data) {
    showSection('results-section');
    scrollToSection('results-section');

    predictionStatusMessage.textContent = data.message || "Resultados de la predicción:";
    predictionStatusMessage.classList.remove('hidden');

    // Muestra la información del paciente si existe
    if (data.patient_info) {
        patientInfoDiv.innerHTML = `
            <h3>Información del Paciente</h3>
            <p><strong>ID:</strong> ${data.patient_info.identification_number}</p>
            <p><strong>Nombre:</strong> ${data.patient_info.name || 'No proporcionado'}</p>
            <p><strong>Fecha de Nacimiento:</strong> ${data.patient_info.date_of_birth || 'No proporcionada'}</p>
            <p><strong>Etapa Simplificada:</strong> ${data.patient_info.simplified_cancer_stage || 'Desconocida'}</p>
        `;
        patientInfoDiv.classList.remove('hidden');
    }

    // Muestra los parámetros usados si existen
    if (data.parameters_used_for_prediction) {
        const params = data.parameters_used_for_prediction;
        paramsT0Display.textContent = `${params.T0_for_models?.toFixed(2) ?? 'N/A'} cm³`;
        paramsTcritExpDisplay.textContent = `${params.T_critical_exponential_used?.toFixed(2) ?? 'N/A'} cm³`;
        paramsTcritGomDisplay.textContent = `${params.T_critical_gompertz_used?.toFixed(2) ?? 'N/A'} cm³`;
        paramsRFinalDisplay.textContent = params.r_final?.toFixed(5) ?? 'N/A';
        paramsKFinalDisplay.textContent = params.K_final?.toFixed(2) ?? 'N/A';
        paramsREmpiricalDisplay.textContent = params.r_empirical_calculated?.toFixed(5) ?? 'No calculado';
        paramsRBibliographicDisplay.textContent = params.r_bibliographic_value?.toFixed(5) ?? 'N/A';
        parametersUsedContainer.classList.remove('hidden');
    }

    // Muestra los resultados de los modelos si existen
    if (data.model_results) {
        modelResultsSection.classList.remove('hidden');

        // --- MANEJO DEFENSIVO PARA EL MODELO EXPONENCIAL ---
        const expResults = data.model_results.exponential;
        if (expResults && expResults.status !== 'error') {
            exponentialResultsDiv.classList.remove('hidden');
            expTiempoEstimadoSpan.textContent = expResults.prediction_days ?? "N/A";
            expUnidadTiempoSpan.textContent = expResults.unit || "";
            expIntervaloConfianzaSpan.textContent = expResults.confidence_interval?.[0] !== null ? `${expResults.confidence_interval[0]} - ${expResults.confidence_interval[1]} ${expResults.unit}` : "N/A";
            expNotesP.textContent = expResults.notes || "";
            expFormulaDiv.textContent = `$$${expResults.formula}$$`;
        } else {
             // Muestra un mensaje de error si no hay resultados válidos
             exponentialResultsDiv.innerHTML = `<h4>Modelo Exponencial</h4><p class="error-message">${expResults?.error || 'No se pudo calcular.'}</p>`;
             exponentialResultsDiv.classList.remove('hidden');
        }

        // --- MANEJO DEFENSIVO PARA EL MODELO GOMPERTZ ---
        const gomResults = data.model_results.gompertz;
        if (gomResults && gomResults.status !== 'error') {
            gompertzResultsDiv.classList.remove('hidden');
            gomTiempoEstimadoSpan.textContent = gomResults.prediction_days ?? "N/A";
            gomUnidadTiempoSpan.textContent = gomResults.unit || "";
            gomIntervaloConfianzaSpan.textContent = gomResults.confidence_interval?.[0] !== null ? `${gomResults.confidence_interval[0]} - ${gomResults.confidence_interval[1]} ${gomResults.unit}` : "N/A";
            gomNotesP.textContent = gomResults.notes || "";
            gomFormulaDiv.textContent = `$$${gomResults.formula}$$`;
        } else {
             // Muestra un mensaje de error si no hay resultados válidos
             gompertzResultsDiv.innerHTML = `<h4>Modelo de Gompertz</h4><p class="error-message">${gomResults?.error || 'No se pudo calcular.'}</p>`;
             gompertzResultsDiv.classList.remove('hidden');
        }
        
        // Vuelve a procesar MathJax para renderizar las fórmulas
        if (window.MathJax) {
            MathJax.typesetPromise();
        }
    }

    // Renderizar gráfico
    const expCurve = data.model_results?.exponential?.curve_data || [];
    const gomCurve = data.model_results?.gompertz?.curve_data || [];
    const t0 = data.parameters_used_for_prediction?.T0_for_models;
    const tCritical = data.parameters_used_for_prediction?.T_critical_exponential_used;

    if ((expCurve.length > 0 || gomCurve.length > 0) && t0 !== undefined && tCritical !== undefined) {
        renderTumorGrowthChart(expCurve, gomCurve, t0, tCritical);
    }
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
btnStartPrediction.addEventListener('click', () => {
    showSection('prediction-form-section');
    scrollToSection('prediction-form-section');
});

predictionForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    clearFormError();
    showLoading(true);

    const otherFactors = {};
    if (subtipoMolecularSelect.value) otherFactors.subtipo_molecular = subtipoMolecularSelect.value;
    if (gradoHistopatologicoSelect.value) otherFactors.grado_histopatologico = gradoHistopatologicoSelect.value;
    if (erPrSelect.value) otherFactors.er_pr = erPrSelect.value;
    if (her2Select.value) otherFactors.her2 = her2Select.value;
    if (metastasisSelect.value) otherFactors.metastasis = metastasisSelect.value;

    const requestBody = {
        identification_number: identificationNumberInput.value.trim(),
        current_tumor_size: parseFloat(currentTumorSizeInput.value),
        current_measurement_date: currentMeasurementDateInput.value,
        name: patientNameInput.value.trim() || undefined,
        date_of_birth: dateOfBirthInput.value || undefined,
        other_factors: otherFactors
    };

    if (!requestBody.identification_number || !requestBody.current_measurement_date || isNaN(requestBody.current_tumor_size)) {
        displayFormError("Por favor, complete los campos de identificación, tamaño actual y fecha.");
        showLoading(false);
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/predict`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestBody)
        });

        const result = await response.json();

        if (response.ok) {
            displayResults(result);
        } else {
            // Maneja errores 4xx y 5xx
            const errorMessage = result.details ? result.details.map(d => d.msg).join(', ') : result.error;
            displayFormError(errorMessage || 'Ocurrió un error desconocido.');
        }
    } catch (error) {
        console.error('Error de conexión:', error);
        displayFormError('No se pudo conectar con el servidor.');
    } finally {
        showLoading(false);
    }
});

btnNewPrediction.addEventListener('click', () => {
    predictionForm.reset(); 
    showSection('introduction'); 
    scrollToSection('introduction');
    // La línea que causaba el error de 'classList' ha sido eliminada.
});

document.addEventListener('DOMContentLoaded', () => {
    showSection('introduction');
});