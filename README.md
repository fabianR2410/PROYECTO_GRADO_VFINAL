# 🚀 Proyecto de Análisis y Visualización COVID-19 (Grupo 6)

Este repositorio contiene el código fuente de un sistema completo de Business Intelligence para el análisis de datos de COVID-19. El proyecto está compuesto por un pipeline ETL, una API RESTful (Backend) y un dashboard interactivo (Frontend).

## Demo en Vivo

Puedes interactuar con el proyecto desplegado en los siguientes enlaces:

* **🖥️ Dashboard Interactivo (Streamlit Cloud):**
    * [**https://proyectogradogrupo6.streamlit.app/**](https://proyectogradogrupo6.streamlit.app/)
* **⚙️ Documentación de la API (Render):**
    * [**https://grupo6-covid-api.onrender.com/docs**](https://grupo6-covid-api.onrender.com/docs)
* **CONTRIBUCIONES (GitHub):**
    * [**https://github.com/fabianR2410/PROYECTO_GRADO_VFINAL**](https://github.com/fabianR2410/PROYECTO_GRADO_VFINAL)

---

## 🏛️ Arquitectura del Sistema

Este proyecto utiliza una arquitectura de microservicios desacoplada, con el frontend y el backend desplegados de forma independiente.

    A[Usuario 👤] --> B(Frontend: Streamlit Cloud ☁️);
    B -- Petición HTTP --> C(Backend: API en Render 🚀);
    C -- 1. Carga --> D[data/owid-covid-data.csv];
    C -- 2. Procesa --> E(Pipeline ETL en memoria);
    E -- Limpia --> F[scripts/data_cleaner.py];
    E -- Imputa --> G[scripts/data_imputer.py];
    E -- Enriquece --> H[scripts/feature_engineer.py];
    C -- Respuesta JSON --> B;


1. Backend (API en Render)
    El "cerebro" del sistema es una API RESTful construida con FastAPI (main.py).

    Está desplegada en Render (https://grupo6-covid-api.onrender.com).

    Arranque Inteligente: Al iniciar, la API carga el archivo data/owid-covid-data.csv, ejecuta el pipeline completo de ETL (limpieza, imputación y creación de características) y almacena los datos procesados en memoria (un DataFrame de Pandas).

    Sirve los datos procesados a través de endpoints optimizados para el dashboard.

2. Frontend (Dashboard en Streamlit Cloud)
La interfaz de usuario es un dashboard interactivo (dashboard.py) construido con Streamlit.

Está desplegado en Streamlit Cloud (https://proyectogradogrupo6.streamlit.app).

Desacoplado: El dashboard no procesa datos. Simplemente realiza peticiones HTTP (requests) a la API en Render para obtener los datos que necesita y los visualiza.

Utiliza st.secrets para almacenar de forma segura la URL de la API de producción.

🛠️ Tecnologías Utilizadas
Backend: FastAPI, Pandas, Uvicorn.

Frontend: Streamlit, Plotly, Requests.

Pipeline: Pandas, NumPy.

Despliegue: Render (para la API), Streamlit Cloud (para el Dashboard), Git/GitHub.

🚀 Cómo Ejecutar el Proyecto Localmente
Sigue estos pasos para ejecutar el sistema completo (API y Dashboard) en tu propia máquina.

Requisitos Previos
Python 3.8+

Git

1. Configuración Inicial (Clonar y Entorno)
    
        Clona el repositorio:

        git clone https://github.com/fabianR2410/PROYECTO_GRADO_VFINAL.git
        cd PROYECTO_GRADO_VFINAL

2. Crea un entorno virtual (recomendado):
    python -m venv .venv

3. Activa el entorno:

    En Windows: .venv\Scripts\activate

    En macOS/Linux: source .venv/bin/activate

4. Instala las dependencias: Importante: Este proyecto tiene las dependencias separadas. Debes instalar ambas.En la Direcion tal y como se clone el repositorio por ejemplo
   
   API/ETL   
   C:\Users\Usuario\OneDrive - UNIANDES\Aplicaciones\covid_project (2)\covid_project\api>pip install -r requirements.txt 
   DASHBOARD
   C:\Users\Usuario\OneDrive - UNIANDES\Aplicaciones\covid_project (2)\covid_project\dashboard>pip install -r requirements.txt

5. Obtener los Datos Crudos
La API (main.py) está diseñada para leer un archivo CSV específico al arrancar.

Crea una carpeta llamada data en la raíz del proyecto (si no existe).

Descarga el archivo de datos de COVID-19 de Our World in Data:

Enlace de descarga: https://www.kaggle.com/datasets/caesarmario/our-world-in-data-covid19-dataset
Guarda el archivo en la carpeta que creaste con el nombre exacto: api/data/owid-covid-data.csv.

6. Ejecutar el Backend (API) Localmente
   
    Abre una terminal (con el entorno virtual activado).

    Navega a la raíz del proyecto (donde está main.py).

    Inicia el servidor de la API con Uvicorn:
        uvicorn main:app --reload

7. La API se ejecutará. Verás registros en la consola indicando que el pipeline ETL se está ejecutando. Una vez que termine, la API estará         disponible en:
                http://127.0.0.1:8000

Puedes verificar que funciona abriendo la documentación local en http://127.0.0.1:8000/docs.

8. Ejecutar el Frontend (Dashboard) Localmente
El dashboard necesita saber dónde encontrar la API. Le diremos que use nuestra API local.

    Crea una carpeta llamada .streamlit en la raíz del proyecto (si no existe).

    Dentro de .streamlit, crea un archivo llamado secrets.toml.

    Pega el siguiente contenido en secrets.toml. Esto le dice al dashboard que se conecte a tu API local en lugar de la de Render.

    # .streamlit/secrets.toml
    API_URL = "[http://127.0.0.1:8000](http://127.0.0.1:8000)"


9. Abre una segunda terminal (deja la API corriendo en la primera).

    Activa el entorno virtual en esta nueva terminal.

    Ejecuta la aplicación de Streamlit:
        
        streamlit run dashboard.py

10. Tu navegador se abrirá automáticamente, mostrando el dashboard (http://localhost:8501) cargando datos desde tu API local.
 
🏆 Equipo de Desarrollo (Grupo 6)
    
    FABIAN REYES

    WORMAN ANDRADE

    CELSO AGUIRRE