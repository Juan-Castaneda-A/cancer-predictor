# 📜 Predictor de Crecimiento Tumoral en Cáncer de Mama

Este es un proyecto académico full-stack diseñado para modelar y predecir la progresión del cáncer de mama utilizando ecuaciones diferenciales. La aplicación permite a los usuarios introducir datos de pacientes y mediciones tumorales para obtener una estimación del tiempo que tardaría un tumor en alcanzar un umbral crítico, basado en los modelos de crecimiento Exponencial y de Gompertz.

El objetivo principal es servir como una herramienta educativa y de investigación para demostrar la aplicación práctica de modelos matemáticos en el campo de la oncología, **sin reemplazar jamás el diagnóstico o consejo de un profesional médico cualificado.**

[➡️ Ver Demo en Vivo](https://cancer-frontend.onrender.com/)

---

## 🔬 La Ciencia Detrás: Modelos Matemáticos y Ecuaciones Diferenciales

El núcleo de este proyecto es la aplicación de dos modelos de crecimiento basados en ecuaciones diferenciales para simular la dinámica tumoral.

### 1. Modelo Exponencial
Este modelo describe un crecimiento ilimitado donde la tasa de cambio del tamaño del tumor es directamente proporcional a su tamaño actual. Es más preciso durante las fases iniciales del crecimiento, cuando no hay limitaciones de espacio o nutrientes.

* **Ecuación Diferencial:**
    $$
    \frac{dT}{dt} = rT
    $$
* **Solución (fórmula de predicción):**
    $$
    T(t) = T_0 \cdot e^{rt}
    $$
* **Implementación:** La solución y sus cálculos derivados se encuentran en `backend/models/exponential_model.py`.

### 2. Modelo de Gompertz
Este modelo es más realista a largo plazo, ya que introduce una "capacidad de carga" (`K`), que representa el tamaño máximo que el tumor puede alcanzar. La tasa de crecimiento se desacelera a medida que el tumor se acerca a este límite.

* **Ecuación Diferencial:**
    $$
    \frac{dT}{dt} = rT \cdot \ln\left(\frac{K}{T}\right)
    $$
* **Solución (fórmula de predicción):**
    $$
    T(t) = K \cdot \exp\left( \ln\left(\frac{T_0}{K}\right) \cdot \exp(-rt) \right)
    $$
* **Implementación:** La solución y sus cálculos derivados se encuentran en `backend/models/gompertz_model.py`.

### 3. Estimación de Parámetros (`r` y `K`)
Una ecuación no es útil sin sus coeficientes. El `PredictionService` (`backend/services/prediction_service.py`) es el cerebro que estima estos parámetros:

* **Parámetro `K` (Capacidad de Carga):** Se obtiene de datos bibliográficos predefinidos en `backend/config.py`.
* **Parámetro `r` (Tasa de Crecimiento):** Se obtiene de dos formas:
    1.  **`r` Bibliográfica:** Un valor base obtenido de estudios científicos, ajustado por factores clínicos como el subtipo molecular, el grado o la edad del paciente.
    2.  **`r` Empírica:** Si se dispone de al menos dos mediciones para un paciente, el sistema calcula una tasa de crecimiento personalizada y teóricamente más precisa para cada modelo, despejando `r` de las ecuaciones de solución. Esta `r` empírica tiene prioridad sobre la bibliográfica.

---

## 🚀 Arquitectura y Tecnologías

El proyecto sigue una arquitectura cliente-servidor desacoplada.

* **Backend:** Una API RESTful construida con **Flask** (Python). Se encarga de toda la lógica de negocio, cálculos matemáticos y comunicación con la base de datos.
    * **Base de Datos:** **PostgreSQL** (alojada en Supabase), gestionada a través del ORM **SQLAlchemy**.
    * **Validación de Datos:** **Pydantic** para validar y estructurar los datos de entrada de la API.
* **Frontend:** Una Single Page Application (SPA) estática construida con **HTML5, CSS3 y JavaScript (Vanilla JS)**.
    * **Gráficas:** **Chart.js** para la visualización dinámica de las curvas de crecimiento.
    * **Fórmulas Matemáticas:** **MathJax** para renderizar las ecuaciones en formato LaTeX.
* **Despliegue (Hosting):**
    * Backend desplegado como un "Web Service" en **Render**.
    * Frontend desplegado como un "Static Site" en **Render**.
    * Base de datos PostgreSQL alojada en **Supabase**.

---

## 💻 Instalación y Ejecución Local

Para ejecutar este proyecto en tu máquina local, sigue estos pasos.

### Prerrequisitos
* Git
* Python 3.10 o superior
* Una cuenta de Supabase (o cualquier base de datos PostgreSQL) para obtener una URL de conexión.

### 1. Clonar el Repositorio
```bash
git clone <URL-de-tu-repositorio>
cd <nombre-del-repositorio>
```
### 2. Clonar Backend
1. Navega a la carpeta del backend
cd backend

2. Crea y activa un entorno virtual
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

3. Instala las dependencias
pip install -r requirements.txt

4. Configura las variables de entorno
Crea un archivo llamado .env en la carpeta /backend
y añade las siguientes variables, reemplazando con tus valores:
DATABASE_URL="postgresql://user:password@host:port/dbname"
FRONTEND_URL="[http://127.0.0.1:5500](http://127.0.0.1:5500)" # URL donde correrá tu frontend localmente

5. Ejecuta el servidor de Flask
flask run

El backend estará corriendo en http://127.0.0.1:5000

### 3. Ejecutar el Frontend

El frontend es un sitio estático. La forma más fácil de ejecutarlo es con la extensión "Live Server" de Visual Studio Code.
1. Abre la carpeta raíz del proyecto en VS Code.

2. Haz clic derecho sobre el archivo frontend/index.html.

3. Selecciona "Open with Live Server".

Esto abrirá la página en tu navegador, generalmente en una dirección como http://127.0.0.1:5500.

## Hoja de Ruta del Proyecto

Este proyecto tiene un gran potencial de crecimiento. La hoja de ruta planificada se divide en las siguientes fases:

### Fase 0: Mejoras Inmediatas de Visualización y Contenido
El objetivo es enriquecer la experiencia actual antes de construir nuevas funcionalidades de plataforma.

Gráfica Interactiva con Etapas del Cáncer: Dibujar líneas de referencia en la gráfica para visualizar los umbrales de cada etapa del cáncer (Etapa I, II, etc.).

Módulo de Información de Tratamientos (Versión Inicial): Mostrar información educativa general sobre las líneas de tratamiento comunes para la etapa del cáncer calculada.

Tooltips Explicativos en Resultados: Añadir íconos de información (?) que expliquen el significado de cada parámetro (r, K, etc.) en la sección de resultados.

### Fase 1: Plataforma Segura para Doctores
Consolidar la herramienta para el rol del doctor, haciéndola robusta para manejar datos.

Autenticación de Usuarios: Sistema de login seguro, empezando con el rol de "doctor".

Dashboard del Doctor: Vista principal para gestionar la lista de pacientes, con búsqueda y filtros.

Carga Masiva de Datos: Implementar la subida de archivos .csv.

Exportar Reporte a PDF: Habilitar un botón para generar un reporte en PDF de la predicción.

Visualización del Historial en Gráfica: Graficar los puntos de mediciones históricas del paciente.

### Fase 2: IA, Personalización y Simulación
Hacer los modelos más inteligentes y útiles como herramienta de exploración.

Calibración de Parámetros (IA): Calcular r y K personalizados para un paciente usando scipy.optimize.curve_fit.

Añadir un Tercer Modelo (Logístico): Enriquece la comparación de modelos matemáticos.

Simulación Interactiva ("¿Qué pasaría si...?"): Añadir "sliders" para que el doctor pueda modificar r y K y ver el impacto en la curva en tiempo real.

### Fase 3: Expansión y Portal del Paciente
Abrir la plataforma a los pacientes y añadir funcionalidades de mayor nivel.

Portal del Paciente: Vista simplificada y segura para el paciente.

Módulo de Interacción y Seguimiento: Implementar mensajería segura y un formulario para que el paciente reporte síntomas (PROs).

Módulo de Recomendaciones (Versión Avanzada): Integrar un LLM para dar información más detallada, dentro de un entorno seguro para el doctor.

### Fase 4: Investigación y Analítica Avanzada (Largo Plazo)
Ideas ambiciosas para posicionar el proyecto a un nivel de investigación.

Modelado de Impacto de Tratamiento: Modificar las ecuaciones para simular el efecto de la quimioterapia.

Análisis Comparativo de Cohortes: Comparar la curva de un paciente con el promedio de pacientes anónimos similares.

Modelos Predictivos de Riesgo (ML): Usar Machine Learning para predecir la probabilidad de recurrencia.