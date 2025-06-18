// frontend/assets/js/main.js

const API_BASE_URL = 'http://127.0.0.1:8000/api'; // *** IMPORTANTE: Cambia esto a la URL de tu backend ***

// Referencias a elementos del DOM
const doctorLoginSection = document.getElementById('doctor-login-section');
const doctorCodeInput = document.getElementById('doctor_code_input');
const doctorLoginBtn = document.getElementById('doctor_login_btn');
const doctorLoginError = document.getElementById('doctor_login_error');

const introductionSection = document.getElementById('introduction');
const predictionFormSection = document.getElementById('prediction-form-section');
const resultsSection = document.getElementById('results-section');
const aboutSection = document.getElementById('about-section');

const btnExponential = document.getElementById('btnExponential');
const btnGompertz = document.getElementById('btnGompertz');
const btnCalibrate = document.getElementById('btnCalibrate');

const modelNameSpan = document.getElementById('model-name');
const predictionForm = document.getElementById('predictionForm');
const calculateBtn = document.getElementById('calculate-btn');
const loadingMessage = document.getElementById('loading-message');
const formErrorMessage = document.getElementById('form-error-message');

// Nuevas referencias para la gestión de pacientes y visitas
const patientSelect = document.getElementById('patient_select');
const newPatientFields = document.getElementById('new-patient-fields');
const identificacionInput = document.getElementById('identificacion');
const nombrePacienteInput = document.getElementById('nombre_paciente');
const sexoSelect = document.getElementById('sexo');
const edadInput = document.getElementById('edad');

const isFirstVisitYes = document.getElementById('is_first_visit_yes');
const isFirstVisitNo = document.getElementById('is_first_visit_no');
const subsequentVisitFields = document.getElementById('subsequent-visit-fields');
const loadPrevVisitDataBtn = document.getElementById('load_prev_visit_data');
const loadPrevVisitError = document.getElementById('load_prev_visit_error');
const previousTumorSizeCm3Input = document.getElementById('previous_tumor_size_cm3');
const lastVisitDateInput = document.getElementById('last_visit_date');

const rDescription = document.getElementById('r-description');

// Referencias para mostrar los resultados detallados
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
const patientHistoryTableDiv = document.getElementById('patient-history-table');

const btnNewPrediction = document.getElementById('btnNewPrediction');
const btnExportPdf = document.getElementById('btnExportPdf');

let selectedModel = '';
let doctorCode = ''; // Almacenar el código del doctor validado

// --- Funciones de control de UI ---
function showSection(sectionId) {
    const sections = [doctorLoginSection, introductionSection, predictionFormSection, resultsSection, aboutSection];
    sections.forEach(sec => sec.classList.add('hidden'));
    document.getElementById(sectionId).classList.remove('hidden');
}

function scrollToSection(sectionId) {
    const section = document.getElementById(sectionId);
    if (section) {
        section.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
}

function clearFormFields() {
    predictionForm.reset();
    identificacionInput.value = '';
    nombrePacienteInput.value = '';
    sexoSelect.value = '';
    edadInput.value = '';
    patientSelect.innerHTML = '<option value="">-- Nuevo Paciente --</option>'; // Limpiar y poner default
    newPatientFields.classList.remove('hidden'); // Asegurar que campos de nuevo paciente estén visibles
    isFirstVisitYes.checked = true; // Por defecto a "Sí, es primera visita"
    toggleSubsequentVisitFields(); // Ocultar campos de visita subsecuente
    loadPrevVisitError.classList.add('hidden'); // Ocultar error de carga de historial
    clearFormError();
}

function updateFormForModel(model) {
    selectedModel = model;
    modelNameSpan.textContent = model === 'exponencial' ? 'Exponencial' : 'Gompertz';
    rDescription.classList.remove('hidden'); // La descripción de r/K/umbral siempre se muestra

    // Asegurarse de que los campos de visitas subsecuentes estén ocultos al seleccionar el modelo
    isFirstVisitYes.checked = true;
    toggleSubsequentVisitFields();

    showSection('prediction-form-section');
    scrollToSection('prediction-form-section');
    loadPatients(); // Cargar pacientes al entrar al formulario de predicción
}

function toggleSubsequentVisitFields() {
    const isFirstVisit = isFirstVisitYes.checked;
    if (isFirstVisit) {
        subsequentVisitFields.classList.add('hidden');
        previousTumorSizeCm3Input.removeAttribute('required');
        lastVisitDateInput.removeAttribute('required');
        previousTumorSizeCm3Input.value = '';
        lastVisitDateInput.value = '';
    } else {
        subsequentVisitFields.classList.remove('hidden');
        previousTumorSizeCm3Input.setAttribute('required', 'true');
        lastVisitDateInput.setAttribute('required', 'true');
    }
    clearFormError();
    loadPrevVisitError.classList.add('hidden'); // Ocultar errores de historial al cambiar
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

// --- Lógica de Login del Doctor ---
doctorLoginBtn.addEventListener('click', async () => {
    const code = doctorCodeInput.value;
    doctorLoginError.classList.add('hidden');

    if (!code) {
        doctorLoginError.textContent = "Por favor, ingrese el código de doctor.";
        doctorLoginError.classList.remove('hidden');
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/doctor_login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ doctor_code: code })
        });

        const result = await response.json();

        if (response.ok) {
            doctorCode = code; // Guardar el código para futuras solicitudes
            showSection('introduction');
            scrollToSection('introduction');
        } else {
            doctorLoginError.textContent = result.detail || 'Error al iniciar sesión.';
            doctorLoginError.classList.remove('hidden');
        }
    } catch (error) {
        console.error('Error de conexión:', error);
        doctorLoginError.textContent = 'No se pudo conectar con el servidor. Asegúrate de que el backend esté ejecutándose.';
        doctorLoginError.classList.remove('hidden');
    }
});

// --- Carga y Gestión de Pacientes ---
async function loadPatients() {
    if (!doctorCode) {
        // Si no hay doctor logueado, redirigir a login o mostrar error
        showSection('doctor-login-section');
        doctorLoginError.textContent = "Sesión expirada o no iniciada. Por favor, ingrese su código de doctor.";
        doctorLoginError.classList.remove('hidden');
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/patients?doctor_code=${doctorCode}`);
        if (!response.ok) {
            throw new Error('Error al cargar la lista de pacientes.');
        }
        const patients = await response.json();
        
        patientSelect.innerHTML = '<option value="">-- Nuevo Paciente --</option>';
        patients.forEach(p => {
            const option = document.createElement('option');
            option.value = p.id;
            option.textContent = `${p.nombre_paciente} (ID: ${p.identificacion}${p.last_visit_date ? ` - Última visita: ${p.last_visit_date}` : ''})`;
            patientSelect.appendChild(option);
        });
    } catch (error) {
        console.error('Error cargando pacientes:', error);
        // Opcional: mostrar un mensaje al usuario
    }
}

patientSelect.addEventListener('change', () => {
    const selectedPatientId = patientSelect.value;
    if (selectedPatientId === "") {
        // Nuevo paciente
        newPatientFields.classList.remove('hidden');
        // Limpiar campos y hacerlos requeridos para nuevo paciente
        identificacionInput.value = '';
        nombrePacienteInput.value = '';
        sexoSelect.value = '';
        edadInput.value = '';
        identificacionInput.setAttribute('required', 'true');
        nombrePacienteInput.setAttribute('required', 'true');
        isFirstVisitYes.checked = true; // Por defecto a primera visita para nuevo paciente
        toggleSubsequentVisitFields();
    } else {
        // Paciente existente
        newPatientFields.classList.add('hidden');
        // Quitar required para que no bloqueen el envío
        identificacionInput.removeAttribute('required');
        nombrePacienteInput.removeAttribute('required');
        
        // Bloquear campos para edición (opcional, podrías querer que sean editables)
        // identificacionInput.disabled = true;
        // nombrePacienteInput.disabled = true;
        // sexoSelect.disabled = true;
        // edadInput.disabled = true;

        // Por defecto, asumir que es una visita subsecuente para un paciente existente
        // y habilitar la carga de datos anteriores
        isFirstVisitNo.checked = true;
        toggleSubsequentVisitFields();
        // Opcional: Cargar automáticamente datos demográficos del paciente seleccionado
        // fetch(`${API_BASE_URL}/patient_details/${selectedPatientId}?doctor_code=${doctorCode}`)
        // .then(res => res.json()).then(data => { /* poblar campos */ });
    }
});

loadPrevVisitDataBtn.addEventListener('click', async () => {
    const selectedPatientId = patientSelect.value;
    loadPrevVisitError.classList.add('hidden');
    if (!selectedPatientId) {
        loadPrevVisitError.textContent = "Por favor, seleccione un paciente existente.";
        loadPrevVisitError.classList.remove('hidden');
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/patient_history/${selectedPatientId}?doctor_code=${doctorCode}`);
        if (!response.ok) {
            throw new Error('No se pudo cargar el historial del paciente.');
        }
        const history = await response.json();

        if (history.length > 0) {
            // Ordenar por fecha descendente y tomar la última visita
            history.sort((a, b) => new Date(b.fecha_visita) - new Date(a.fecha_visita));
            const lastVisit = history[0];
            previousTumorSizeCm3Input.value = lastVisit.initial_tumor_size_cm3;
            lastVisitDateInput.value = lastVisit.fecha_visita;

            // Mostrar historial completo en los resultados
            renderPatientHistoryTable(history);

        } else {
            loadPrevVisitError.textContent = "No hay historial previo para este paciente. Marque como 'Primera visita'.";
            loadPrevVisitError.classList.remove('hidden');
            // Si no hay historial, forzar "Primera visita"
            isFirstVisitYes.checked = true;
            toggleSubsequentVisitFields();
        }
    } catch (error) {
        console.error('Error cargando datos de visita anterior:', error);
        loadPrevVisitError.textContent = error.message || 'Error al cargar el historial del paciente.';
        loadPrevVisitError.classList.remove('hidden');
    }
});

function renderPatientHistoryTable(history) {
    if (history && history.length > 0) {
        let tableHTML = `
            <table class="history-table">
                <thead>
                    <tr>
                        <th>Fecha Visita</th>
                        <th>Tamaño Tumor (cm³)</th>
                        <th>r Calculado</th>
                        <th>Modelo</th>
                        <th>Tiempo Est. (días)</th>
                    </tr>
                </thead>
                <tbody>
        `;
        history.forEach(visit => {
            tableHTML += `
                <tr>
                    <td>${visit.fecha_visita}</td>
                    <td>${visit.initial_tumor_size_cm3.toFixed(2)}</td>
                    <td>${visit.r_calculado.toFixed(5)}</td>
                    <td>${visit.model_type.charAt(0).toUpperCase() + visit.model_type.slice(1)}</td>
                    <td>${visit.tiempo_estimado_dias ? visit.tiempo_estimado_dias.toFixed(2) : 'N/A'}</td>
                </tr>
            `;
        });
        tableHTML += `
                </tbody>
            </table>
        `;
        patientHistoryTableDiv.innerHTML = tableHTML;
    } else {
        patientHistoryTableDiv.innerHTML = '<p>No hay historial de visitas previo registrado para este paciente.</p>';
    }
}


// --- Event Listeners para Modelos y Formulario ---
btnExponential.addEventListener('click', () => updateFormForModel('exponencial'));
btnGompertz.addEventListener('click', () => updateFormForModel('gompertz'));

isFirstVisitYes.addEventListener('change', toggleSubsequentVisitFields);
isFirstVisitNo.addEventListener('change', toggleSubsequentVisitFields);

predictionForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    clearFormError();
    showLoading(true);

    const formData = new FormData(predictionForm);
    const patientData = {};

    // Obtener el ID del paciente seleccionado (si existe)
    const selectedPatientId = patientSelect.value;
    if (selectedPatientId) {
        patientData.id = parseInt(selectedPatientId); // Pasar ID para buscar en DB
    }

    // Recoger todos los campos del formulario
    for (const [key, value] of formData.entries()) {
        if (key === 'is_first_visit') {
            patientData[key] = (value === 'true');
        } else if (value) {
            if (['initial_tumor_size_cm3', 'previous_tumor_size_cm3'].includes(key)) {
                patientData[key] = parseFloat(value);
            } else if (['edad', 'dias_tratamiento'].includes(key)) {
                patientData[key] = parseInt(value);
            } else {
                patientData[key] = value;
            }
        }
    }

    // Validar campos requeridos para nuevo paciente si no hay ID seleccionado
    if (!selectedPatientId) {
        if (!patientData.identificacion || !patientData.nombre_paciente) {
            displayFormError("Por favor, ingrese el ID y el Nombre del Paciente para un nuevo registro.");
            showLoading(false);
            return;
        }
    }
    
    // Si no es primera visita, asegurar que los campos de historial estén presentes
    if (!patientData.is_first_visit && (!patientData.previous_tumor_size_cm3 || !patientData.last_visit_date)) {
        displayFormError("Para una visita subsecuente, el tamaño del tumor anterior y la fecha de la visita anterior son obligatorios.");
        showLoading(false);
        return;
    }

    // El backend necesita saber si se seleccionó un paciente existente o si se debe crear uno nuevo.
    // Enviamos el 'identificacion' y 'nombre_paciente' siempre. El backend usará el 'identificacion' para buscar/crear.
    // El campo `id` del patientData solo es para cuando se seleccionó un paciente existente.

    try {
        const response = await fetch(`${API_BASE_URL}/predict`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                model_type: selectedModel,
                patient_data: patientData,
                doctor_code: doctorCode // Enviar el código del doctor en cada solicitud
            })
        });

        const result = await response.json();

        if (response.ok) {
            displayResults(result);
            // Después de una predicción exitosa, recargar la lista de pacientes
            loadPatients(); 
        } else {
            displayFormError(result.detail || 'Error desconocido al calcular la predicción.');
        }
    } catch (error) {
        console.error('Error de conexión:', error);
        displayFormError('No se pudo conectar con el servidor. Asegúrate de que el backend esté ejecutándose y la URL sea correcta.');
    } finally {
        showLoading(false);
    }
});

btnNewPrediction.addEventListener('click', () => {
    clearFormFields(); // Limpiar y restablecer todo
    showSection('introduction');
    scrollToSection('introduction');
    patientHistoryTableDiv.innerHTML = '<p>No hay historial de visitas previo registrado para este paciente.</p>'; // Limpiar historial
});

// Inicialización: mostrar solo la sección de login al cargar la página
document.addEventListener('DOMContentLoaded', () => {
    showSection('doctor-login-section');
    toggleSubsequentVisitFields();
    rDescription.classList.remove('hidden');
});