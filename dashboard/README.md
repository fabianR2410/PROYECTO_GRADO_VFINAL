# 📊 Dashboard Interactivo COVID-19

Un dashboard interactivo, desarrollado en Streamlit y Plotly, para visualizar y explorar la evolución de los datos de COVID-19 a nivel mundial.

---

## 📋 Requisitos Previos

Antes de comenzar, asegúrate de tener instalado:
* Python 3.8+
* Git (para clonar el repositorio)

---

## 🛠️ Instalación

Sigue estos pasos para configurar el entorno de desarrollo local:

1.  **Clona el repositorio:**
    ```bash
    git clone <URL_DE_TU_REPOSITORIO>
    cd <NOMBRE_DEL_PROYECTO>
    ```

2.  **Crea y activa un entorno virtual:**
    ```bash
    # Crea el entorno
    python -m venv .venv

    # Activa el entorno (Windows)
    .venv\Scripts\activate

    # Activa el entorno (macOS/Linux)
    source .venv/bin/activate
    ```

3.  **Instala las dependencias:**
    El archivo `requirements.txt` (debes crearlo si no existe) debe contener todas las librerías necesarias (streamlit, pandas, plotly, etc.).
    ```bash
    pip install -r requirements.txt
    ```

---

## 🚀 Inicio Rápido

Este proyecto tiene dos componentes principales: un script para procesar los datos (`quick_start.py`, según tu sección de "Solución de Problemas") y la aplicación del dashboard (`start_dashboard.py`).

1.  **Procesa los Datos (ETL):**
    Este script se encarga de descargar, limpiar y guardar los datos en un formato optimizado (`data/processed/`) que el dashboard pueda leer.
    ```bash
    python quick_start.py
    ```
    *Nota: Solo necesitas ejecutar esto la primera vez o cuando quieras actualizar los datos.*

2.  **Inicia el Dashboard:**
    Este comando lanza la aplicación de Streamlit.
    ```bash
    python start_dashboard.py
    ```

3.  **Accede al Dashboard:**
    Abre tu navegador y ve a la dirección: **http://localhost:8501**

---

## 🏛️ Arquitectura y Flujo de Datos

El funcionamiento del proyecto se divide en dos fases:

1.  **ETL (Extract, Transform, Load):** El script `quick_start.py` (o similar) se conecta a la fuente de datos (ej: Our World in Data, Johns Hopkins), procesa los datos crudos usando Pandas, y los guarda en formato Parquet o CSV en la carpeta `data/processed/`.
2.  **Visualización:** La aplicación `dashboard/app.py` (ejecutada por `start_dashboard.py`) carga los datos procesados desde `data/processed/`. Streamlit gestiona el cache de estos datos (`@st.cache_data`) para un rendimiento óptimo. Todas las interacciones del usuario (filtros, selección de países) actualizan los gráficos de Plotly en tiempo real.

* **Fuente de Datos:** [Especifica aquí la fuente, ej: Our World in Data]
* **Datos Procesados:** `data/processed/covid_data.parquet` (o el nombre que uses)
* **Aplicación:** `dashboard/app.py`

---

## ✨ Características Principales

El dashboard ofrece múltiples vistas para un análisis completo:

### 1. Estadísticas Globales
Panel superior con métricas clave a nivel mundial:
- Total de casos
- Total de muertes
- Personas vacunadas
- Número de países

### 2. Mapa Mundial Coroplético
Visualización geográfica interactiva que muestra:
- Cualquier métrica seleccionable (ej: "total_cases", "people_vaccinated")
- Datos por país con escala de colores proporcional
- Información detallada al pasar el mouse (hover)

### 3. Análisis de Series de Tiempo
Gráficos de líneas para comparar la evolución temporal entre países:

**Vista Combinada:**
- Múltiples métricas en subgráficos apilados.
- Comparación entre los países seleccionados.
- Zoom y pan interactivo.

**Vista Individual:**
- Un gráfico por métrica para una comparación más clara.

### 4. Comparación entre Países
Gráfico de barras que compara una métrica específica (valores más recientes) para los países seleccionados.

### 5. Análisis Detallado por País
Vista profunda de un país específico, incluyendo:
- Estadísticas resumidas (casos, muertes, vacunación)
- Gráficos de **Promedios Móviles** (7 días) para suavizar el ruido y ver tendencias claras.

### 6. Visualización de Datos Crudos
Tabla interactiva con los datos filtrados, con opciones de búsqueda, ordenamiento y descarga en formato CSV.

---

## 🎛️ Controles del Sidebar

El sidebar izquierdo permite un control total sobre los datos mostrados:

* **Selección de Países:**
    * `Multiselect`: Permite seleccionar múltiples países.
    * `Default`: Ecuador, Perú, Colombia, Brasil.
* **Métrica del Mapa:**
    * `Selectbox`: Elige la métrica a mostrar en el mapa mundial.
* **Métricas para Comparación:**
    * `Multiselect`: Selecciona métricas para los gráficos de serie de tiempo.
    * `Default`: `new_cases`, `new_deaths`.
* **Rango de Fechas:**
    * `Date Input`: Filtra todos los datos por un rango de fechas.
    * `Default`: Últimos 90 días.

---

## 📏 Métricas Disponibles

El dataset incluye, entre otras, las siguientes métricas:

### Casos
- `new_cases`: Nuevos casos diarios
- `total_cases`: Casos acumulados
- `new_cases_smoothed`: Promedio móvil 7 días
- `total_cases_per_million`: Casos por millón de habitantes

### Muertes
- `new_deaths`: Nuevas muertes diarias
- `total_deaths`: Muertes acumuladas
- `new_deaths_smoothed`: Promedio móvil 7 días
- `total_deaths_per_million`: Muertes por millón de habitantes

### Vacunación
- `people_vaccinated`: Personas con al menos 1 dosis
- `people_fully_vaccinated`: Personas totalmente vacunadas
- `total_vaccinations`: Total de dosis administradas

*(Y otras como Testing y Hospitalización si están disponibles)*

---

## 🚀 Rendimiento y Optimización

-   **Cache de datos**: Se utiliza `@st.cache_data` para cargar el dataset principal una sola vez y mantenerlo en memoria, acelerando la respuesta a los filtros.
-   **Formato eficiente**: Se recomienda usar **Parquet** en lugar de CSV para la carga de datos, ya que es significativamente más rápido.
-   **Renderizado selectivo**: Solo se actualizan los componentes gráficos que dependen de un filtro modificado.

---

## 🔧 Solución de Problemas

* **Dashboard no carga o muestra error en los datos:**
    * Asegúrate de haber ejecutado el script `python quick_start.py` al menos una vez para generar los archivos de datos en `data/processed/`.
* **Gráficos no se muestran correctamente:**
    * Intenta limpiar la caché de Streamlit: `streamlit cache clear`
    * Reinstala las librerías: `pip install --upgrade streamlit plotly pandas`
* **Error de Puerto en uso (Address already in use):**
    * Lanza la aplicación en un puerto diferente:
        ```bash
        streamlit run dashboard/app.py --server.port 8502
        ```

---

## 📦 Despliegue

### Local
```bash
# Opción 1 (script personalizado)
python start_dashboard.py

# Opción 2 (comando directo)
streamlit run dashboard/app.py

streamlit run dashboard/app.py --server.port 80 --server.address 0.0.0.0

#doker
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# Expone el puerto por defecto de Streamlit
EXPOSE 8501

# Comando para ejecutar la app
CMD ["streamlit", "run", "dashboard/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
# DOCUMENTACION 
Documentación de Streamlit

Documentación de Plotly Python

Documentación de Pandas