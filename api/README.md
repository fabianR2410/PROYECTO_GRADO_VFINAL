# ⚙️ API y ETL de Datos COVID-19

Este proyecto contiene dos componentes principales:
1.  **ETL:** Scripts para descargar, procesar y guardar los datos de COVID-19.
2.  **API REST:** Una API (basada en FastAPI) para servir los datos procesados.

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
    Asegúrate de tener un archivo `requirements.txt` con todas las librerías necesarias (fastapi, uvicorn, pandas, etc.).
    ```bash
    pip install -r requirements.txt
    ```

---

## 🏛️ Arquitectura del Sistema

El funcionamiento del proyecto se divide en dos fases:

1.  **Fase 1: ETL (Extract, Transform, Load)**
    * Un script (ej. `run_etl.py` - *asegúrate de poner el nombre correcto aquí*) se conecta a la fuente de datos (ej: Our World in Data).
    * Procesa los datos crudos usando Pandas.
    * Guarda los datos limpios en un formato eficiente (ej. Parquet o una base de datos) en una ubicación específica (ej. `data/processed/`).

2.  **Fase 2: API (Servicio de Datos)**
    * La aplicación de API (`api/main.py`, iniciada por `start_api.py`) se ejecuta.
    * Esta API (FastAPI) **lee** los datos procesados en la Fase 1 para responder a las solicitudes HTTP.
    * **Importante:** La API no realiza la descarga de datos, solo los sirve.

**Por lo tanto, el ETL debe ejecutarse al menos una vez antes de iniciar la API para que haya datos que mostrar.**

---

## 🚀 Inicio Rápido (Flujo de trabajo)

Este es el orden correcto para poner el sistema en funcionamiento:

1.  **Ejecuta el ETL:**
    (Cambia `run_etl.py` por el nombre de tu script de ETL)
    ```bash
    python run_etl.py
    ```
    *Espera a que termine. Esto solo necesitas hacerlo la primera vez o para actualizar los datos.*

2.  **Inicia la API:**
    ```bash
    python start_api.py
    ```
    La API estará disponible en: **http://localhost:8000**

---

## 📖 Documentación de la API

Una vez que la API está en funcionamiento, puedes explorar la documentación interactiva para probar los endpoints:

* **Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
* **ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)

## Endpoints Disponibles

### 1. Root Endpoint