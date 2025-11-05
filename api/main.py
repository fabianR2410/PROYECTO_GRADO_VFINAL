# -*- coding: utf-8 -*-
"""
COVID-19 Data API (Versión 2.1 - Despliegue en Render)
- Ejecuta el ETL completo en memoria al iniciar.
- Carga datos desde la URL de OWID (no archivos locales).
- Usa importaciones relativas (scripts/ está dentro de api/)
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

# --- NUEVAS IMPORTACIONES DEL ETL (CON RUTA RELATIVA) ---
# Asumiendo que 'scripts' está DENTRO de la carpeta 'api'
from .scripts.data_loader import CovidDataLoader
from .scripts.data_cleaner import CovidDataCleaner
from .scripts.data_imputer import CovidDataImputer
from .scripts.feature_engineer import CovidFeatureEngineer
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
    1. Carga desde la URL de OWID
    2. Limpia
    3. Imputa
    4. Crea Features
    """
    global covid_data
    logger.info("Iniciando pipeline ETL completo en memoria...")
    
    try:
        # 1. Cargar Datos (desde la web)
        logger.info("[ETL 1/4] Cargando datos desde la web...")
        loader = CovidDataLoader()
        # ¡IMPORTANTE! No pasamos 'local_filepath', usará la URL de OWID
        df = loader.load_data(source="owid", force=True) 
        
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
        # ¡CAMBIO! Llamamos a la nueva función
        load_data_and_run_etl() 
        logger.info("Datos cargados y procesados exitosamente en el inicio.")
    except Exception as e:
        logger.error(f"Error fatal al ejecutar ETL en el inicio: {e}")
    
    yield # La API se ejecuta aquí

    # Código de apagado
    logger.info("Apagando API...")
    global covid_data
    covid_data = None


# Initialize FastAPI app
app = FastAPI(
    title="COVID-19 Data API",
    description="API para acceder a métricas y series de tiempo de COVID-19 (Datos en vivo)",
    version="2.1.0", # Versión actualizada
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
            # ¡CAMBIO! Llamamos a la nueva función
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
    Endpoint para forzar la re-ejecución de todo el pipeline ETL.
    """
    logger.info("Recarga de ETL solicitada vía endpoint POST /admin/reload-data...")
    try:
        # ¡CAMBIO! Llamamos a la nueva función
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
        "name": "COVID-19 Data API",
        "version": "2.1.0",
        "status": api_status,
        "data_last_updated": covid_data['date'].max().isoformat() if covid_data is not None and 'date' in covid_data.columns else "N/A",
        "endpoints": {
            "/docs": "Interactive API documentation (Swagger UI)",
            "/redoc": "Alternative API documentation (ReDoc)",
            "/covid/countries": "Get list of available countries",
            "/covid/metrics": "Get list of available metrics",
            "/covid/timeseries": "Get time series data for a country",
            "/covid/summary": "Get summary statistics for a country",
            "/covid/compare": "Compare metrics across multiple countries",
            "/covid/latest": "Get latest data for all or specific countries",
            "/covid/global": "Get global aggregated statistics",
        },
         "admin_endpoints": {
             "POST /admin/reload-data": "Trigger manual ETL reload from web"
         }
    }


@app.get("/covid/countries", tags=["COVID Data"])
async def get_countries(df: pd.DataFrame = Depends(get_data)):
    """Obtiene la lista de países/regiones disponibles."""
    try:
        if 'location' not in df.columns:
            raise HTTPException(status_code=500, detail="Location column not found")
        countries = sorted(df['location'].dropna().unique().tolist())
        return {"total": len(countries), "countries": countries}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/covid/metrics", tags=["COVID Data"])
async def get_metrics(df: pd.DataFrame = Depends(get_data)):
    """Obtiene la lista de métricas disponibles, categorizadas."""
    try:
        exclude_cols = ['iso_code', 'continent', 'location', 'date']
        metrics = [col for col in df.columns if col not in exclude_cols]

        categorized = {
            "cases": [m for m in metrics if 'case' in m.lower()],
            "deaths": [m for m in metrics if 'death' in m.lower()],
            "vaccinations": [m for m in metrics if 'vaccin' in m.lower() or 'dose' in m.lower()],
            "testing": [m for m in metrics if 'test' in m.lower()],
            "hospitalizations": [m for m in metrics if 'hospital' in m.lower() or 'icu' in m.lower()],
            "rates": [m for m in metrics if 'rate' in m.lower() or 'per_' in m.lower()],
            "demographics": [m for m in metrics if m in ['population', 'population_density', 'median_age', 'aged_65_older', 'aged_70_older', 'gdp_per_capita', 'extreme_poverty', 'cardiovasc_death_rate', 'diabetes_prevalence', 'female_smokers', 'male_smokers', 'handwashing_facilities', 'hospital_beds_per_thousand', 'life_expectancy', 'human_development_index']],
            "other": []
        }

        all_categorized = sum(categorized.values(), [])
        categorized['other'] = sorted([m for m in metrics if m not in all_categorized])

        for key in categorized:
            categorized[key].sort()

        return {
            "total": len(metrics),
            "categories": categorized,
            "all_metrics": sorted(metrics)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/covid/timeseries", tags=["COVID Data"])
async def get_timeseries(
    df: pd.DataFrame = Depends(get_data),
    country: str = Query(..., description="Country name"),
    metric: str = Query("new_cases", description="Metric to retrieve"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)", pattern=r"^\d{4}-\d{2}-\d{2}$"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)", pattern=r"^\d{4}-\d{2}-\d{2}$")
):
    """Obtiene datos de series de tiempo para un país y métrica específicos."""
    try:
        country_data = df[df['location'].str.lower() == country.lower()].copy()

        if country_data.empty:
            raise HTTPException(status_code=404, detail=f"Country '{country}' not found")

        if metric not in country_data.columns:
            raise HTTPException(status_code=400, detail=f"Metric '{metric}' not found")

        if start_date:
            country_data = country_data[country_data['date'] >= pd.to_datetime(start_date)]
        if end_date:
            country_data = country_data[country_data['date'] <= pd.to_datetime(end_date)]

        result = country_data[['date', metric]].copy()
        result = result.replace([np.inf, -np.inf], np.nan)
        result_obj = result.astype(object)
        data_cleaned = result_obj.where(pd.notnull(result), None)


        return {
            "country": country,
            "metric": metric,
            "data_points": len(data_cleaned), 
            "start_date": data_cleaned['date'].min().isoformat() if not data_cleaned.empty else None,
            "end_date": data_cleaned['date'].max().isoformat() if not data_cleaned.empty else None,
            "data": data_cleaned.to_dict(orient='records')
        }
    except ValueError as e: # Captura errores de formato de fecha, etc.
        raise HTTPException(status_code=400, detail=f"Invalid parameter format: {e}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/covid/summary", tags=["COVID Data"])
async def get_summary(
    df: pd.DataFrame = Depends(get_data),
    country: str = Query(..., description="Country name")
):
    """Obtiene estadísticas resumidas para un país específico (último dato disponible)."""
    try:
        country_data = df[df['location'].str.lower() == country.lower()].copy()

        if country_data.empty:
            raise HTTPException(status_code=404, detail=f"Country '{country}' not found")

        latest_row = country_data.sort_values('date', ascending=False).iloc[0]

        latest = latest_row.replace([np.inf, -np.inf], np.nan).astype(object).where(pd.notnull(latest_row), None)

        summary = {
            "country": latest['location'],
            "iso_code": latest.get('iso_code'), 
            "continent": latest.get('continent'), 
            "last_updated": latest['date'].isoformat() if latest['date'] is not None else None,
            "population": int(latest['population']) if latest.get('population') is not None else None,
            "totals": {}, "new_values": {}, "vaccination": {},
            "testing": {}, "hospital": {}, "other_metrics": {}
        }

        # Llenar diccionarios
        summary['totals']['cases'] = int(latest['total_cases']) if latest.get('total_cases') is not None else None
        summary['totals']['deaths'] = int(latest['total_deaths']) if latest.get('total_deaths') is not None else None
        summary['totals']['tests'] = int(latest['total_tests']) if latest.get('total_tests') is not None else None

        summary['new_values']['cases'] = float(latest['new_cases']) if latest.get('new_cases') is not None else None
        summary['new_values']['deaths'] = float(latest['new_deaths']) if latest.get('new_deaths') is not None else None
        summary['new_values']['tests'] = float(latest['new_tests']) if latest.get('new_tests') is not None else None
        summary['new_values']['vaccinations'] = float(latest['new_vaccinations']) if latest.get('new_vaccinations') is not None else None


        summary['vaccination']['people_vaccinated'] = int(latest['people_vaccinated']) if latest.get('people_vaccinated') is not None else None
        summary['vaccination']['people_fully_vaccinated'] = int(latest['people_fully_vaccinated']) if latest.get('people_fully_vaccinated') is not None else None
        summary['vaccination']['total_boosters'] = int(latest['total_boosters']) if latest.get('total_boosters') is not None else None
        summary['vaccination']['people_vaccinated_per_hundred'] = float(latest['people_vaccinated_per_hundred']) if latest.get('people_vaccinated_per_hundred') is not None else None
        summary['vaccination']['people_fully_vaccinated_per_hundred'] = float(latest['people_fully_vaccinated_per_hundred']) if latest.get('people_fully_vaccinated_per_hundred') is not None else None

        summary['testing']['positive_rate'] = float(latest['positive_rate']) if latest.get('positive_rate') is not None else None
        summary['testing']['tests_per_case'] = float(latest['tests_per_case']) if latest.get('tests_per_case') is not None else None

        summary['hospital']['icu_patients'] = int(latest['icu_patients']) if latest.get('icu_patients') is not None else None
        summary['hospital']['hosp_patients'] = int(latest['hosp_patients']) if latest.get('hosp_patients') is not None else None

        summary['other_metrics']['reproduction_rate'] = float(latest['reproduction_rate']) if latest.get('reproduction_rate') is not None else None
        summary['other_metrics']['stringency_index'] = float(latest['stringency_index']) if latest.get('stringency_index') is not None else None

        if summary['totals']['cases'] and summary['totals']['cases'] > 0 and summary['totals']['deaths'] is not None:
             summary['other_metrics']['case_fatality_rate'] = (summary['totals']['deaths'] / summary['totals']['cases']) * 100
        else:
             summary['other_metrics']['case_fatality_rate'] = None

        return summary
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/covid/compare", tags=["COVID Data"])
async def compare_countries(
    df: pd.DataFrame = Depends(get_data),
    countries: str = Query(..., description="Comma-separated list of countries (e.g., Ecuador,Peru,Colombia)"),
    metric: str = Query("new_cases_smoothed_per_million", description="Metric to compare"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)", pattern=r"^\d{4}-\d{2}-\d{2}$"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)", pattern=r"^\d{4}-\d{2}-\d{2}$")
):
    """Compara una métrica específica a través de múltiples países en un rango de fechas."""
    try:
        country_list = [c.strip() for c in countries.split(',') if c.strip()]
        if not country_list:
            raise HTTPException(status_code=400, detail="No valid countries provided in the list.")

        comparison_data = []
        found_countries = []

        for country in country_list:
            country_data = df[df['location'].str.lower() == country.lower()].copy()

            if country_data.empty:
                logger.warning(f"Country '{country}' not found for comparison.")
                continue

            found_countries.append(country) 

            if metric not in country_data.columns:
                logger.warning(f"Metric '{metric}' not found for country '{country}'.")
                comparison_data.append({"country": country, "error": f"Metric '{metric}' not available"})
                continue

            if start_date:
                country_data = country_data[country_data['date'] >= pd.to_datetime(start_date)]
            if end_date:
                country_data = country_data[country_data['date'] <= pd.to_datetime(end_date)]

            result = country_data[['date', metric]].copy()
            result = result.replace([np.inf, -np.inf], np.nan)
            cleaned_data = result.astype(object).where(pd.notnull(result), None)

            comparison_data.append({
                "country": country_data['location'].iloc[0] if not country_data.empty else country,
                "data": cleaned_data.to_dict(orient='records')
            })

        if not any('data' in item for item in comparison_data):
            raise HTTPException(status_code=404, detail=f"No data found for metric '{metric}' in the specified countries: {', '.join(country_list)}")

        return {
            "metric": metric,
            "countries_requested": country_list,
            "countries_found": found_countries,
            "comparison": comparison_data
        }
    except ValueError as e: 
        raise HTTPException(status_code=400, detail=f"Invalid parameter format: {e}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/covid/latest", tags=["COVID Data"])
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


@app.get("/covid/global", tags=["COVID Data"])
async def get_global_stats(df: pd.DataFrame = Depends(get_data)):
    """Obtiene estadísticas globales agregadas (basadas en la fila 'World')."""
    try:
        # Usamos 'World' porque así lo define 'data_loader.py' al agregar
        world_data = df[df['location'].str.lower() == 'world'].copy() 
        
        if world_data.empty:
             raise HTTPException(status_code=404, detail="Global 'World' data not found.")

        else:
             latest_world_row = world_data.sort_values('date', ascending=False).iloc[0]
             latest_world = latest_world_row.replace([np.inf, -np.inf], np.nan).astype(object).where(pd.notnull(latest_world_row), None)

             global_summary = {
                 "source": "Aggregated by data_loader", # Fuente actualizada
                 "location": latest_world.get('location'),
                 "last_updated": latest_world['date'].isoformat() if latest_world.get('date') is not None else None,
                 "population": int(latest_world['population']) if latest_world.get('population') is not None else None,
                 "total_cases": int(latest_world['total_cases']) if latest_world.get('total_cases') is not None else None,
                 "total_deaths": int(latest_world['total_deaths']) if latest_world.get('total_deaths') is not None else None,
                 "new_cases": float(latest_world['new_cases']) if latest_world.get('new_cases') is not None else None,
                 "new_deaths": float(latest_world['new_deaths']) if latest_world.get('new_deaths') is not None else None,
                 "people_vaccinated": int(latest_world['people_vaccinated']) if latest_world.get('people_vaccinated') is not None else None,
                 "people_fully_vaccinated": int(latest_world['people_fully_vaccinated']) if latest_world.get('people_fully_vaccinated') is not None else None,
                 "total_boosters": int(latest_world['total_boosters']) if latest_world.get('total_boosters') is not None else None,
             }
             return global_summary

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    # Este 'if' es principalmente para pruebas locales, 
    # Render usará el comando 'uvicorn api.main:app'
    uvicorn.run(app, host="0.0.0.0", port=8000)