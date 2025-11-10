# -*- coding: utf-8 -*-
"""
COVID-19 Data API (Versión 2.8.0 - Reactivado)

- API optimizada para servir al dashboard de Streamlit.
- ¡RE-AÑADIDO! Se reactivó el endpoint /covid/compare-timeseries
  para dar soporte a la Mejora 3 (gráfico de comparación) del dashboard.
- ¡CORREGIDO! Corregido el bug del pattern (regex) en end_date.
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
    version="2.8.0 (con /compare-timeseries)", # Versión actualizada
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
        "version": "2.8.0",
        "status": api_status,
        "data_source": "Local CSV (owid-covid-data.csv)",
        "data_last_updated": covid_data['date'].max().isoformat() if covid_data is not None and 'date' in covid_data.columns else "N/A",
        "endpoints_activos": {
            "/docs": "Interactive API documentation (Swagger UI)",
            "/redoc": "Alternative API documentation (ReDoc)",
            "/covid/countries": "Get list of available countries",
            "/covid/metrics": "Get list of available metrics",
            "/covid/latest": "Get latest data for all or specific countries",
            "/covid/country-history": "Get full history for one country",
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
        return {
            "total": len(metrics),
            "all_metrics": sorted(metrics)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- ENDPOINT RE-AÑADIDO (Para Mejora 3 del Dashboard) ---
@app.get("/covid/compare-timeseries", tags=["COVID Data (Dashboard)"])
async def compare_timeseries(
    df: pd.DataFrame = Depends(get_data),
    countries: str = Query(..., description="Lista de países separados por comas (ej: Ecuador,Peru,Colombia)"),
    metric: str = Query("new_cases_smoothed", description="Métrica a comparar"),
    start_date: Optional[str] = Query(None, description="Fecha inicio (YYYY-MM-DD)", pattern=r"^\d{4}-\d{2}-\d{2}$"),
    
    # --- ¡ESTA ES LA LÍNEA CORREGIDA! ---
    end_date: Optional[str] = Query(None, description="Fecha fin (YYYY-MM-DD)", pattern=r"^\d{4}-\d{2}-\d{2}$")
):
    """
    [RE-ACTIVADO] Compara una métrica específica a través de múltiples países,
    devolviendo sus series de tiempo.
    """
    try:
        country_list_raw = [c.strip() for c in countries.split(',') if c.strip()]
        country_list_lower = [c.lower() for c in country_list_raw]
        
        if not country_list_lower:
            raise HTTPException(status_code=400, detail="La lista de países está vacía.")

        if metric not in df.columns:
            raise HTTPException(status_code=400, detail=f"Métrica '{metric}' no encontrada.")

        # Filtrar por países
        df_filtered = df[df['location'].str.lower().isin(country_list_lower)].copy()

        if df_filtered.empty:
             raise HTTPException(status_code=404, detail="Ninguno de los países solicitados fue encontrado.")

        # Filtrar por fechas
        if start_date:
            df_filtered = df_filtered[df_filtered['date'] >= pd.to_datetime(start_date)]
        if end_date:
            df_filtered = df_filtered[df_filtered['date'] <= pd.to_datetime(end_date)]
        
        if df_filtered.empty:
             raise HTTPException(status_code=404, detail="No se encontraron datos para el rango de fechas especificado.")

        # Estructurar la respuesta
        response_data = {
            "metric": metric,
            "start_date": start_date,
            "end_date": end_date,
            "comparison_data": {}
        }

        # Mapear minúsculas a nombres originales capitalizados
        name_map = df_filtered.drop_duplicates('location', keep='first').set_index(df_filtered['location'].str.lower())['location'].to_dict()

        for country_lower in country_list_lower:
            original_name = name_map.get(country_lower)
            if original_name:
                # Usamos .loc para evitar SettingWithCopyWarning
                country_data = df_filtered.loc[df_filtered['location'].str.lower() == country_lower, ['date', metric]]
                
                if not country_data.empty:
                    # Limpiar NaNs/Infs para JSON
                    country_data = country_data.replace([np.inf, -np.inf], np.nan)
                    country_data_cleaned = country_data.astype(object).where(pd.notnull(country_data), None)
                    
                    response_data["comparison_data"][original_name] = country_data_cleaned.to_dict(orient='records')
                else:
                    # Informar si un país específico no tuvo datos en el rango
                    response_data["comparison_data"][original_name] = []
            else:
                 # Si el país se pidió pero no se encontró (ej. "Ecuado"), usa el nombre crudo
                 raw_name_index = country_list_lower.index(country_lower)
                 response_data["comparison_data"][country_list_raw[raw_name_index]] = []


        return response_data

    except ValueError as e: 
        raise HTTPException(status_code=400, detail=f"Formato de parámetro inválido: {e}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en /covid/compare-timeseries: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
# --- FIN ENDPOINT RE-AÑADIDO ---


# --- ¡ENDPOINT ESENCIAL! (Para Pestaña 2) ---
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