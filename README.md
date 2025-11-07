# 🚀 Proyecto de Métricas COVID-19

Sistema completo para análisis y visualización de datos de COVID-19, compuesto por un pipeline de ETL, una API REST y un dashboard interactivo.

## Características

-   **Pipeline de Datos**: Descarga, limpieza e imputación automática.
-   **API REST**: Endpoints para acceder a series de tiempo y estadísticas.
-   **Dashboard Interactivo**: Visualizaciones avanzadas con mapas y gráficos.
-   **Generación de Características**: Métricas epidemiológicas avanzadas.
-   **Exportación Flexible**: Múltiples formatos (CSV, Excel, Parquet, JSON).

---

## 🏛️ Arquitectura del Sistema

Este proyecto tiene 3 componentes principales que dependen uno del otro:

1.  **Pipeline ETL** (`main.py`, `quick_start.py`): Descarga los datos crudos de la web, los procesa y los guarda en la carpeta `data/processed/`.
2.  **API REST** (`start_api.py`): Lee los datos de `data/processed/` y los sirve a través de endpoints HTTP.
3.  **Dashboard** (`start_dashboard.py`): Lee los datos de `data/processed/` y los muestra en una interfaz web interactiva.

> **Importante:** Debes ejecutar el **Pipeline ETL (Paso 2)** al menos una vez para generar los archivos en `data/processed/` antes de poder usar la API o el Dashboard.

---

## 🛠️ Instalación

### Requisitos previos
-   Python 3.8 o superior
-   Git (para clonar el repositorio)

### Pasos de instalación

1.  **Clona el repositorio:**
    ```bash
    git clone <URL_DE_TU_REPOSITORIO>
    cd covid_project
    ```

2.  **Crea y activa un entorno virtual (Recomendado):**
    ```bash
    # Crea el entorno
    python -m venv .venv

    # Activa el entorno (Windows)
    .venv\Scripts\activate

    # Activa el entorno (macOS/Linux)
    source .venv/bin/activate
    ```

3.  **Instala las dependencias:**
    ```bash
    pip install -r requirements.txt
    ```

---

## 🚀 Guía de Inicio Rápido (Flujo de Trabajo)

Sigue estos 3 pasos para poner todo el sistema en funcionamiento:

### Paso 1: Ejecuta el Pipeline de Datos (ETL)

Este comando descargará los datos más recientes, los limpiará, generará características y los guardará en `data/processed/`.

```bash
python quick_start.py