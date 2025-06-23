const API_BASE_URL = 'https://cancer-predictor-ed.onrender.com/api'; //backend

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

// Actualiza las referencias a los nuevos campos del DOM
const identificationNumberInput = document.getElementById('identification_number');
const patientNameInput = document.getElementById('patient_name');
const dateOfBirthInput = document.getElementById('date_of_birth');
const currentTumorSizeInput = document.getElementById('current_tumor_size');
const currentMeasurementDateInput = document.getElementById('current_measurement_date');
const criticalThresholdInput = document.getElementById('T_critical'); // Puede que ya lo tuvieras
// Referencias a los campos de other_factors
const tipoCancerSelect = document.getElementById('tipo_cancer');
const subtipoMolecularSelect = document.getElementById('subtipo_molecular');
const gradoHistopatologicoSelect = document.getElementById('grado_histopatologico');
const erPrSelect = document.getElementById('er_pr');
const her2Select = document.getElementById('her2');
const metastasisSelect = document.getElementById('metastasis');
// **NUEVAS referencias a elementos del DOM para mostrar resultados detallados**
const patientInfoDiv = document.getElementById('patient-info-display'); // Nuevo div para info del paciente
const modelResultsSection = document.getElementById('model-results-section'); // Nueva sección para resultados de modelos
const predictionStatusMessage = document.getElementById('prediction-status-message'); // Nuevo para mensajes generales de estado
const exponentialResultsDiv = document.getElementById('exponential-results'); // Div para resultados Exponencial
const gompertzResultsDiv = document.getElementById('gompertz-results'); // Div para resultados Gompertz

// Referencias para mostrar datos del modelo exponencial
const expTiempoEstimadoSpan = document.getElementById('exp-tiempo-estimado');
const expUnidadTiempoSpan = document.getElementById('exp-unidad-tiempo');
const expIntervaloConfianzaSpan = document.getElementById('exp-intervalo-confianza');
const expFormulaDiv = document.getElementById('exp-math-formula');
const expNotesP = document.getElementById('exp-notes'); // Para notas/mensajes de regresión
// Referencias para mostrar datos del modelo Gompertz
const gomTiempoEstimadoSpan = document.getElementById('gom-tiempo-estimado');
const gomUnidadTiempoSpan = document.getElementById('gom-unidad-tiempo');
const gomIntervaloConfianzaSpan = document.getElementById('gom-intervalo-confianza');
const gomFormulaDiv = document.getElementById('gom-math-formula');
const gomNotesP = document.getElementById('gom-notes'); // Para notas/mensajes de regresión

// Referencias para los nuevos divs de parámetros usados
const paramsGeneralMessage = document.getElementById('params-general-message');
const paramsT0Display = document.getElementById('params-T0');
const paramsTCriticalDisplay = document.getElementById('params-Tcritical');
const paramsRFinalDisplay = document.getElementById('params-r-final');
const paramsKFinalDisplay = document.getElementById('params-K-final');
const paramsREmpiricalDisplay = document.getElementById('params-r-empirical');
const paramsRBibliographicDisplay = document.getElementById('params-r-bibliographic');
const paramsKBibliographicDisplay = document.getElementById('params-K-bibliographic');


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

    // **1. Mostrar el mensaje general del estado de la predicción (si hay regresión)**
    predictionStatusMessage.textContent = data.message; // "El tumor está disminuyendo..." o "Predicción calculada..."
    predictionStatusMessage.classList.remove('hidden'); // Asegúrate de que este elemento esté visible

    // **2. Mostrar información del paciente**
    if (data.patient_info) {
        patientInfoDiv.innerHTML = `
            <h3>Información del Paciente</h3>
            <p><strong>ID:</strong> ${data.patient_info.identification_number}</p>
            <p><strong>Nombre:</strong> ${data.patient_info.name || 'No proporcionado'}</p>
            <p><strong>Fecha de Nacimiento:</strong> ${data.patient_info.date_of_birth || 'No proporcionada'}</p>
            <p><strong>Tamaño actual:</strong> ${data.patient_info.current_tumor_size} cm³</p>
            <p><strong>Fecha de medición:</strong> ${data.patient_info.current_measurement_date}</p>
            <p><strong>Número de mediciones previas:</strong> ${data.patient_info.num_previous_measurements}</p>
        `;
        patientInfoDiv.classList.remove('hidden');
    } else {
        patientInfoDiv.classList.add('hidden');
    }

    // **3. Mostrar los parámetros usados para la predicción**
    if (data.parameters_used_for_prediction) {
        const params = data.parameters_used_for_prediction;
        paramsGeneralMessage.textContent = data.message; // Mensaje como "Se utilizó la tasa bibliográfica..."

        // Actualiza los elementos del DOM con los parámetros
        paramsT0Display.textContent = params.T0_for_models !== null ? params.T0_for_models.toFixed(2) + ' cm³' : 'N/A';
        paramsTCriticalDisplay.textContent = params.T_critical !== null ? params.T_critical.toFixed(2) + ' cm³' : 'N/A';
        paramsRFinalDisplay.textContent = params.r_final !== null ? params.r_final.toFixed(5) + ' (por día)' : 'N/A';
        paramsKFinalDisplay.textContent = params.K_final !== null ? params.K_final.toFixed(2) + ' cm³' : 'N/A';
        paramsREmpiricalDisplay.textContent = params.r_empirical_calculated !== null ? params.r_empirical_calculated.toFixed(5) + ' (por día)' : 'N/A';
        paramsRBibliographicDisplay.textContent = params.r_bibliographic_value !== null ? params.r_bibliographic_value.toFixed(5) + ' (por día)' : 'N/A';
        paramsKBibliographicDisplay.textContent = params.K_bibliographic_value !== null ? params.K_bibliographic_value.toFixed(2) + ' cm³' : 'N/A';
        
        // Muestra el contenedor de parámetros
        document.getElementById('parameters-used-container').classList.remove('hidden');
    } else {
        document.getElementById('parameters-used-container').classList.add('hidden');
    }


    // **4. Procesar y mostrar los resultados de cada modelo**
    if (data.model_results) {
        modelResultsSection.classList.remove('hidden'); // Asegúrate de que la sección de resultados del modelo sea visible

        // --- Modelo Exponencial ---
        const expResults = data.model_results.exponential;
        if (expResults) {
            exponentialResultsDiv.classList.remove('hidden');
            if (expResults.status === "tumor_regressing") {
                expTiempoEstimadoSpan.textContent = "N/A";
                expUnidadTiempoSpan.textContent = "";
                expIntervaloConfianzaSpan.textContent = "N/A (Regresión)";
                expNotesP.textContent = expResults.notes || "El modelo exponencial predice una regresión del tumor.";
            } else {
                expTiempoEstimadoSpan.textContent = expResults.prediction_days !== null ? expResults.prediction_days.toFixed(2) : "N/A";
                expUnidadTiempoSpan.textContent = expResults.unit || "";
                //expIntervaloConfianzaSpan.textContent = expResults.confidence_interval ? 
                //    `${expResults.confidence_interval[0].toFixed(2)} - ${expResults.confidence_interval[1].toFixed(2)} ${expResults.unit}` : "N/A";
                if (
                    expResults.confidence_interval &&
                    Array.isArray(expResults.confidence_interval) &&
                    expResults.confidence_interval.length === 2 &&
                    typeof expResults.confidence_interval[0] === 'number' &&
                    typeof expResults.confidence_interval[1] === 'number'
                ) {
                    expIntervaloConfianzaSpan.textContent =
                        `${expResults.confidence_interval[0].toFixed(2)} - ${expResults.confidence_interval[1].toFixed(2)} ${expResults.unit}`;
                } else {
                    expIntervaloConfianzaSpan.textContent = "N/A";
                }
                
                expNotesP.textContent = expResults.notes || "";
            }
            // MathJax para la fórmula (se abordará en Fase 3 - Parte 4)
            expFormulaDiv.textContent = `$$${expResults.formula}$$`;
            // Chart.js rendering (se abordará en Fase 3 - Parte 3)
            // renderTumorGrowthChart(expResults.curve_data, data.parameters_used_for_prediction.T0_for_models, data.parameters_used_for_prediction.T_critical, 'exponential');
        } else {
            exponentialResultsDiv.classList.add('hidden');
        }

        // --- Modelo Gompertz ---
        const gomResults = data.model_results.gompertz;
        if (gomResults) {
            gompertzResultsDiv.classList.remove('hidden');
            if (gomResults.status === "tumor_regressing") {
                gomTiempoEstimadoSpan.textContent = "N/A";
                gomUnidadTiempoSpan.textContent = "";
                gomIntervaloConfianzaSpan.textContent = "N/A (Regresión)";
                gomNotesP.textContent = gomResults.notes || "El modelo de Gompertz predice una regresión del tumor.";
            } else {
                gomTiempoEstimadoSpan.textContent = gomResults.prediction_days !== null ? gomResults.prediction_days.toFixed(2) : "N/A";
                gomUnidadTiempoSpan.textContent = gomResults.unit || "";
                //gomIntervaloConfianzaSpan.textContent = gomResults.confidence_interval ? 
                //    `${gomResults.confidence_interval[0].toFixed(2)} - ${gomResults.confidence_interval[1].toFixed(2)} ${gomResults.unit}` : "N/A";
                if (
                    gomResults.confidence_interval &&
                    Array.isArray(gomResults.confidence_interval) &&
                    gomResults.confidence_interval.length === 2 &&
                    typeof gomResults.confidence_interval[0] === 'number' &&
                    typeof gomResults.confidence_interval[1] === 'number'
                ) {
                    gomIntervaloConfianzaSpan.textContent =
                        `${gomResults.confidence_interval[0].toFixed(2)} - ${gomResults.confidence_interval[1].toFixed(2)} ${gomResults.unit}`;
                } else {
                    gomIntervaloConfianzaSpan.textContent = "N/A";
                }
                
                gomNotesP.textContent = gomResults.notes || "";
            }
            // MathJax para la fórmula (se abordará en Fase 3 - Parte 4)
            gomFormulaDiv.textContent = `$$${gomResults.formula}$$`;
            // Chart.js rendering (se abordará en Fase 3 - Parte 3)
            // renderTumorGrowthChart(gomResults.curve_data, data.parameters_used_for_prediction.T0_for_models, data.parameters_used_for_prediction.T_critical, 'gompertz');
        } else {
            gompertzResultsDiv.classList.add('hidden');
        }
    } else {
        modelResultsSection.classList.add('hidden');
    }

    // **AHORA, LA LLAMADA A RENDERIZAR EL GRÁFICO**
    // Asegúrate de que los datos de la curva existan y sean válidos
    //const expCurve = data.model_results?.exponential?.curve_data || [];
    let expCurve = [];
    const curveExpRaw = data.model_results?.exponential?.curve_data;
    if (Array.isArray(curveExpRaw) && curveExpRaw.length > 0) {
        expCurve = curveExpRaw.map(point => ({ x: point.x, y: point.y }));
    }


    //const gomCurve = data.model_results?.gompertz?.curve_data || [];
    let gomCurve = [];
    const curveGomRaw = data.model_results?.gompertz?.curve_data;
    if (Array.isArray(curveGomRaw) && curveGomRaw.length > 0) {
        gomCurve = curveGomRaw.map(point => ({ x: point.x, y: point.y }));
    }

    const t0 = data.parameters_used_for_prediction?.T0_for_models;
    const tCritical = data.parameters_used_for_prediction?.T_critical;

    // Solo renderiza el gráfico si hay datos de al menos una curva y los parámetros son válidos
    if ((expCurve.length > 0 || gomCurve.length > 0) && t0 !== null && tCritical !== null) {
        renderTumorGrowthChart(expCurve, gomCurve, t0, tCritical);
    } else {
        // Si no hay datos para el gráfico (ej. regresión sin puntos de crecimiento), destruye el gráfico existente
        if (tumorGrowthChartInstance) {
            tumorGrowthChartInstance.destroy();
            tumorGrowthChartInstance = null; // Reiniciar la instancia
        }
        // Puedes añadir un mensaje en la UI para indicar que no hay gráfico si es un caso de regresión pura
        console.warn("No hay datos de curva disponibles para renderizar el gráfico o parámetros faltantes.");
    }

    // Aquí ya no necesitas las líneas antiguas:
    // renderTumorGrowthChart(data.puntos_curva, data.parametros_usados.T0, data.parametros_usados.T_critical);

    // Ocultar los elementos antiguos que ya no se usan
    tiempoEstimadoSpan.textContent = '--'; // Vacía los antiguos
    unidadTiempoSpan.textContent = '';
    intervaloConfianzaSpan.textContent = '--';
    interpretationText.innerHTML = ''; // Vacía los antiguos
    mathFormulaDiv.textContent = ''; // Vacía los antiguos
    paramsUsedPre.textContent = ''; // Vacía los antiguos

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

    // ************************************************************
    // CAMBIOS CLAVE AQUÍ: Construcción del Objeto de Petición para el Backend
    // ************************************************************
    
    // Recopilar otros factores solo si tienen un valor seleccionado
    const otherFactors = {};
    if (tipoCancerSelect.value) otherFactors.tipo_cancer = tipoCancerSelect.value;
    if (subtipoMolecularSelect.value) otherFactors.subtipo_molecular = subtipoMolecularSelect.value;
    if (gradoHistopatologicoSelect.value) otherFactors.grado_histopatologico = gradoHistopatologicoSelect.value;
    if (erPrSelect.value) otherFactors.er_pr = erPrSelect.value;
    if (her2Select.value) otherFactors.her2 = her2Select.value;
    if (metastasisSelect.value) otherFactors.metastasis = metastasisSelect.value;

    const requestBody = {
        identification_number: identificationNumberInput.value.trim(),
        current_tumor_size: parseFloat(currentTumorSizeInput.value),
        current_measurement_date: currentMeasurementDateInput.value, // Formato YYYY-MM-DD
        T_critical: parseFloat(criticalThresholdInput.value),
        
        // Incluir campos de paciente nuevo si se llenan
        // El backend verificará si son necesarios o si el paciente ya existe
        name: patientNameInput.value.trim() || undefined, // undefined si está vacío, para que Pydantic lo trate como None
        date_of_birth: dateOfBirthInput.value || undefined, // undefined si está vacío
        
        other_factors: otherFactors // Objeto de factores adicionales
    };

    // Validación básica del lado del cliente (Pydantic hará la validación robusta en el backend)
    if (!requestBody.identification_number || isNaN(requestBody.current_tumor_size) || !requestBody.current_measurement_date) {
        displayFormError("Por favor, complete todos los campos obligatorios (Identificación, Tamaño Actual, Fecha de Medición).");
        showLoading(false);
        return;
    }
    if (requestBody.current_tumor_size <= 0) {
        displayFormError("El tamaño actual del tumor debe ser un número positivo.");
        showLoading(false);
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/predict`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestBody)
        });

        const result = await response.json();

        if (response.ok) {
            displayResults(result); // Esta función será la que procese la nueva estructura
        } else {
            // Manejo de errores detallado del backend (Pydantic, ValueErrors)
            if (result.error && result.details) { // Error de Pydantic (422)
                const errorMessages = result.details.map(detail => {
                    const field = detail.loc && detail.loc.length > 1 ? detail.loc[1] : 'Campo desconocido';
                    return `Error en '${field}': ${detail.msg}`;
                }).join('<br>');
                displayFormError(`Datos de entrada inválidos:<br>${errorMessages}`);
            } else if (result.error) { // Otros errores del backend (400, 500)
                displayFormError(result.error);
            } else {
                displayFormError('Error desconocido al calcular la predicción.');
            }
        }
    } catch (error) {
        console.error('Error de conexión:', error);
        displayFormError('No se pudo conectar con el servidor. Asegúrate de que el backend esté ejecutándose.');
    } finally {
        showLoading(false);
    }
});

btnNewPrediction.addEventListener('click', () => {
    predictionForm.reset(); 
    showSection('introduction'); 
    scrollToSection('introduction');
    KGroup.classList.add('hidden'); 
});

document.addEventListener('DOMContentLoaded', () => {
    showSection('introduction');
});

// **IMPORTANTE:** La función updateFormForModel ya no necesitará manejar 'KGroup' porque K ya no es una entrada directa del usuario.
// El K final siempre vendrá del backend (bibliográfico). Puedes simplificarla o mantenerla si planeas reintroducir K como override.
// Por ahora, solo asegúrate de que el campo K en HTML esté fuera de la necesidad de ser requerido por JS.
// Si tu HTML ya no tiene un campo 'K' directo que el usuario deba llenar, puedes eliminar esta parte del if/else.
function updateFormForModel(model) {
    selectedModel = model;
    modelNameSpan.textContent = model === 'exponencial' ? 'Exponencial' : 'Gompertz';
    // KGroup.classList.add('hidden'); // K ya no se ingresa directamente
    // document.getElementById('K').removeAttribute('required'); // K ya no es requerido
    // showSection('prediction-form-section');
    // scrollToSection('prediction-form-section');
    // Simplemente muestra el formulario de predicción
    showSection('prediction-form-section');
    scrollToSection('prediction-form-section');
}