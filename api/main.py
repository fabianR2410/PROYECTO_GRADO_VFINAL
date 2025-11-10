# -*- coding: utf-8 -*-
"""
COVID-19 Data API (Versión 2.7.0 - Refactorizada)

- API optimizada para servir *exclusivamente* al dashboard de Streamlit.
- Se eliminaron 5 endpoints redundantes que no se utilizaban en el frontend:
  (timeseries, summary, compare, compare-timeseries, global)
- Mantiene la carga del ETL desde el CSV local al iniciar.
"""
from fastapi import FastAPI, HTTPException, Query, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List, AsyncGenerator, Dict, Any
from contextlib import asynccontextmanager
import pandas as pd
import numpy as np
from pathlib import Path
import logging
from datetime import datetime

# --- IMPORTACIONES DEL ETL (CORREGIDAS PARA RENDER) ---
from scripts.data_loader import CovidDataLoader
from scripts.data_cleaner import CovidDataCleaner
from scripts.data_imputer import CovidDataImputer
from scripts.feature_engineer import CovidFeatureEngineer
# --------------------------------------------------------

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Almacenamiento de datos en memoria ---
covid_data: Optional[pd.DataFrame] = None

# --- LÓGICA DE CARGA MODIFICADA ---
# Esta función ahora ejecutará el ETL completo
def load_data_and_run_etl() -> pd.DataFrame:
    """
    Ejecuta el pipeline ETL completo en memoria:
    1. Carga desde el CSV local
    2. Limpia
    3. Imputa
    4. Crea Features
    """
    global covid_data
    logger.info("Iniciando pipeline ETL completo en memoria...")
    
    try:
        # 1. Cargar Datos (desde CSV local)
        logger.info("[ETL 1/4] Cargando datos desde archivo CSV local...")
        loader = CovidDataLoader()
        
        # Esta es la ruta al CSV que debes subir
        # (Render trabaja desde la carpeta 'api', así que la ruta es 'data/...')
        df = loader.load_data(local_filepath="data/owid-covid-data.csv") 
        
        # 2. Limpiar Datos
        logger.info("[ETL 2/4] Limpiando datos...")
        cleaner = CovidDataCleaner()
        df_clean = cleaner.clean_data(df)
        
        # 3. Imputar Valores
        logger.info("[ETL 3/4] Imputando valores faltantes...")
        imputer = CovidDataImputer()
        df_imputed = imputer.smart_imputation(df_clean)
        
        # 4. Crear Features
        logger.info("[ETL 4/4] Creando features...")
        engineer = CovidFeatureEngineer()
        df_final = engineer.create_all_features(df_imputed)
        
        # 5. Guardar en memoria
        covid_data = df_final # Actualiza la variable global
        logger.info("Pipeline ETL completado. Variable global 'covid_data' actualizada.")
        return df_final

    except Exception as e:
        logger.error(f"Error fatal durante el pipeline ETL: {e}", exc_info=True)
        covid_data = None
        raise # Propagamos el error

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Manejador del ciclo de vida de la API. Ejecuta el ETL al inicio.
    """
    logger.info("Iniciando API...")
    try:
        # Llamamos a la función que carga desde el CSV
        load_data_and_run_etl() 
        logger.info("Datos cargados (desde CSV) y procesados exitosamente en el inicio.")
    except Exception as e:
        logger.error(f"Error fatal al ejecutar ETL en el inicio: {e}")
    
    yield # La API se ejecuta aquí

    # Código de apagado
    logger.info("Apagando API...")
    global covid_data
    covid_data = None


# Initialize FastAPI app
app = FastAPI(
    title="COVID-19 Data API (para Dashboard)",
    description="API optimizada para servir datos al Dashboard de COVID-19 (Datos Locales)",
    version="2.7.0 (Refactorizada)", # Versión actualizada
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Dependencia de Datos ---
def get_data() -> pd.DataFrame:
    """
    Dependencia de FastAPI para obtener el DataFrame.
    """
    global covid_data
    if covid_data is None:
        logger.warning("Intentando acceder a datos (covid_data is None), intentando recargar ETL...")
        try:
            # Llamamos a la función que carga desde el CSV
            load_data_and_run_etl()
            if covid_data is None: # Si falló
                 raise HTTPException(status_code=503, detail="Servicio temporalmente no disponible: Error al recargar ETL.")
            logger.info("Recarga de ETL completada exitosamente dentro de get_data.")
        except Exception as e:
            logger.error(f"Fallo crítico en la recarga de ETL dentro de get_data: {e}")
            raise HTTPException(status_code=503, detail=f"Servicio no disponible: Error crítico al recargar ETL - {e}")
    return covid_data

# --- Endpoint de Recarga ---
@app.post("/admin/reload-data", status_code=status.HTTP_200_OK, tags=["Admin"])
async def trigger_reload_data():
    """
    Endpoint para forzar la re-ejecución de todo el pipeline ETL (leyendo el CSV).
    """
    logger.info("Recarga de ETL solicitada vía endpoint POST /admin/reload-data...")
    try:
        # Llamamos a la función que carga desde el CSV
        load_data_and_run_etl()
        logger.info("Datos recargados (ETL) exitosamente vía endpoint.")
        return {"message": "Data ETL reload successful"}
    except Exception as e:
        logger.error(f"Error durante la recarga (ETL) vía endpoint: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to reload ETL data: {e}")


# --- Endpoints Públicos ---

@app.get("/", tags=["General"])
async def root():
    """Endpoint raíz con información de la API."""
    api_status = "online"
    if covid_data is None:
        api_status = "error_loading_data"
        try:
            get_data() 
            if covid_data is not None:
                api_status = "online" # Se recuperó
        except:
            pass 


    return {
        "name": "COVID-19 Data API (Dashboard)",
        "version": "2.7.0 (Refactorizada)",
        "status": api_status,
        "data_source": "Local CSV (owid-covid-data.csv)",
        "data_last_updated": covid_data['date'].max().isoformat() if covid_data is not None and 'date' in covid_data.columns else "N/A",
        "endpoints_activos": {
            "/docs": "Interactive API documentation (Swagger UI)",
            "/redoc": "Alternative API documentation (ReDoc)",
            "/covid/countries": "Get list of available countries",
            "/covid/metrics": "Get list of available metrics",
            "/covid/latest": "Get latest data for all or specific countries",
            "/covid/country-history": "Get full history for one country"
        },
         "admin_endpoints": {
             "POST /admin/reload-data": "Trigger manual ETL reload from CSV"
         }
    }


@app.get("/covid/countries", tags=["COVID Data (Dashboard)"])
async def get_countries(df: pd.DataFrame = Depends(get_data)):
    """Obtiene la lista de países/regiones disponibles."""
    try:
        if 'location' not in df.columns:
            raise HTTPException(status_code=500, detail="Location column not found")
        countries = sorted(df['location'].dropna().unique().tolist())
        return {"total": len(countries), "countries": countries}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/covid/metrics", tags=["COVID Data (Dashboard)"])
async def get_metrics(df: pd.DataFrame = Depends(get_data)):
    """Obtiene la lista de métricas disponibles, categorizadas."""
    try:
        exclude_cols = ['iso_code', 'continent', 'location', 'date']
        metrics = [col for col in df.columns if col not in exclude_cols]
        # ... (Tu código de categorización va aquí si lo tienes)
        return {
            "total": len(metrics),
            "all_metrics": sorted(metrics)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- ENDPOINTS ELIMINADOS (No usados por el Dashboard) ---
#
# GET /covid/timeseries
# GET /covid/summary
# GET /covid/compare
# GET /covid/compare-timeseries
# GET /covid/global
#
# Se eliminaron estos 5 endpoints porque el dashboard actual
# no los utiliza. La carga de datos se optimizó usando
# /latest y /country-history.
#
# --- FIN DE ENDPOINTS ELIMINADOS ---


# --- ¡NUEVO ENDPOINT! (Esencial para la Pestaña 2) ---
@app.get("/covid/country-history", tags=["COVID Data (Dashboard)"])
async def get_country_history(
    df: pd.DataFrame = Depends(get_data),
    country: str = Query(..., description="Country name (e.g., Ecuador, World)")
):
    """
    Obtiene TODAS las métricas y TODA la historia para un solo país o agregado.
    Esto es para el refactor de rendimiento del dashboard.
    """
    try:
        country_data = df[df['location'].str.lower() == country.lower()].copy()
        if country_data.empty:
            raise HTTPException(status_code=404, detail=f"País '{country}' no encontrado.")
        
        # Reemplazar infinitos y NaNs por None para un JSON limpio
        country_data = country_data.replace([np.inf, -np.inf], np.nan)
        country_data_cleaned = country_data.astype(object).where(pd.notnull(country_data), None)
        
        return country_data_cleaned.to_dict(orient='records')
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
# --- FIN NUEVO ENDPOINT ---


@app.get("/covid/latest", tags=["COVID Data (Dashboard)"])
async def get_latest(
    df: pd.DataFrame = Depends(get_data),
    countries: Optional[str] = Query(None, description="Comma-separated list of countries (optional)")
):
    """Obtiene el último registro disponible para todos los países o una lista específica."""
    try:
        latest_idx = df.groupby('location')['date'].idxmax()
        latest_data = df.loc[latest_idx]

        if countries:
            country_list = [c.strip().lower() for c in countries.split(',') if c.strip()]
            if not country_list:
                 raise HTTPException(status_code=400, detail="Country list provided but contains no valid names.")
            latest_data = latest_data[latest_data['location'].str.lower().isin(country_list)]

        if latest_data.empty:
            raise HTTPException(status_code=404, detail="No data found for the specified criteria.")

        latest_data = latest_data.replace([np.inf, -np.inf], np.nan)
        latest_data_cleaned = latest_data.astype(object).where(pd.notnull(latest_data), None)

        result = latest_data_cleaned.to_dict(orient='records')

        return {
            "total_records": len(result),
            "data": result
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    # Este 'if' es principalmente para pruebas locales, 
    # Render usará el comando 'uvicorn main:app'
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)