# -*- coding: utf-8 -*-
"""
COVID-19 Data API (Versión 1.4 - Endpoint de Recarga)
FastAPI application serving COVID-19 data.
- Usa 'lifespan'.
- Usa 'Depends'.
- Corrige error JSON (NaN/inf).
- Añade endpoint POST /admin/reload-data.
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
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Almacenamiento de datos en memoria ---
covid_data: Optional[pd.DataFrame] = None
# (Caché de modelos Prophet eliminada)

# --- RUTAS ---
# LÍNEA CORREGIDA:
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "data" / "processed"
# (Ruta a modelos Prophet eliminada)


def load_data() -> pd.DataFrame:
    """Load processed COVID data from disk. Returns the loaded DataFrame."""
    global covid_data
    logger.info("Iniciando carga/recarga de datos...")
    
    try:
        parquet_files = list(DATA_PATH.glob("*.parquet"))
        if parquet_files:
            # Ordenar para tomar el más reciente si hay varios
            latest_file = max(parquet_files, key=lambda p: p.stat().st_mtime)
            df = pd.read_parquet(latest_file)
            logger.info(f"Datos cargados desde {latest_file}")
        else:
            csv_files = list(DATA_PATH.glob("*.csv"))
            if csv_files:
                latest_file = max(csv_files, key=lambda p: p.stat().st_mtime)
                df = pd.read_csv(latest_file)
                logger.info(f"Datos cargados desde {latest_file}")
            else:
                raise FileNotFoundError("No processed data files found in data/processed")

        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])

        covid_data = df # Actualiza la variable global
        logger.info("Variable global 'covid_data' actualizada.")
        return df # Retorna el DataFrame recién cargado

    except Exception as e:
        logger.error(f"Error durante la carga de datos: {e}")
        covid_data = None
        raise # Propagamos el error

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Manejador del ciclo de vida de la API. Carga datos al inicio.
    """
    logger.info("Iniciando API...")
    try:
        load_data() # Carga inicial
        logger.info("Datos cargados exitosamente en el inicio.")
    except Exception as e:
        logger.error(f"Error fatal al cargar datos en el inicio: {e}")
    
    # (Comprobación de MODELS_DIR eliminada)

    yield # La API se ejecuta aquí

    # Código de apagado
    logger.info("Apagando API...")
    global covid_data
    covid_data = None
    # (Limpieza de model_cache eliminada)


# Initialize FastAPI app
app = FastAPI(
    title="COVID-19 Data API",
    description="API para acceder a métricas y series de tiempo de COVID-19",
    version="1.4.0",
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
        logger.warning("Intentando acceder a datos (covid_data is None), intentando recargar...")
        try:
            load_data()
            if covid_data is None: # Si load_data falló y puso None
                 raise HTTPException(status_code=503, detail="Servicio temporalmente no disponible: Error al recargar datos.")
            logger.info("Recarga completada exitosamente dentro de get_data.")
        except Exception as e:
            logger.error(f"Fallo crítico en la recarga dentro de get_data: {e}")
            raise HTTPException(status_code=503, detail=f"Servicio no disponible: Error crítico al recargar datos - {e}")
    return covid_data

# (Dependencia get_prophet_model eliminada)


# --- Endpoint de Recarga ---
@app.post("/admin/reload-data", status_code=status.HTTP_200_OK, tags=["Admin"])
async def trigger_reload_data():
    """
    Endpoint para forzar la recarga de los datos desde el disco.
    """
    logger.info("Recarga de datos solicitada vía endpoint POST /admin/reload-data...")
    try:
        load_data()
        
        # (Limpieza de caché de modelos eliminada)
        
        logger.info("Datos recargados exitosamente vía endpoint.")
        return {"message": "Data reload successful"}
    except FileNotFoundError as e:
         logger.error(f"Error durante la recarga vía endpoint: Archivo no encontrado - {e}")
         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to reload data: Data file not found - {e}")
    except Exception as e:
        logger.error(f"Error durante la recarga vía endpoint: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to reload data: {e}")


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
        "version": "1.4.0",
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
            # (Endpoint /covid/forecast eliminado de la lista)
        },
         "admin_endpoints": {
             "POST /admin/reload-data": "Trigger manual data reload from disk"
         }
    }


# (Endpoint /covid/forecast eliminado)


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
        world_data = df[df['location'].str.lower() == 'world'].copy()
        if world_data.empty:
            logger.warning("Fila 'World' no encontrada, intentando sumar países...")
            latest_idx = df.groupby('location')['date'].idxmax()
            latest_data = df.loc[latest_idx]
            aggregates = ['world', 'europe', 'asia', 'africa', 'north america', 'south america', 'oceania',
                          'european union', 'high income', 'upper middle income', 'lower middle income', 'low income']
            latest_countries = latest_data[~latest_data['location'].str.lower().isin(aggregates)]

            if latest_countries.empty:
                 raise HTTPException(status_code=404, detail="Global 'World' data not found and could not aggregate countries.")

            latest_countries = latest_countries.replace([np.inf, -np.inf], np.nan)

            global_stats = {
                "source": "Aggregated from countries",
                "last_updated": latest_countries['date'].max().isoformat() if not latest_countries.empty else None,
                "total_countries_aggregated": len(latest_countries),
                "aggregated_totals": {}
            }
            numeric_cols = latest_countries.select_dtypes(include=np.number).columns
            for col in numeric_cols:
                if any(k in col.lower() for k in ['total_', 'new_', 'people_', 'hosp_', 'icu_']):
                    col_sum = latest_countries[col].sum()
                    global_stats['aggregated_totals'][col] = float(col_sum) if pd.notna(col_sum) else None
            
            return global_stats

        else:
             latest_world_row = world_data.sort_values('date', ascending=False).iloc[0]
             latest_world = latest_world_row.replace([np.inf, -np.inf], np.nan).astype(object).where(pd.notnull(latest_world_row), None)

             global_summary = {
                 "source": "Directly from 'World' aggregate",
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
    # Es mejor usar 'python start_api.py' que tiene reload=True
    uvicorn.run(app, host="0.0.0.0", port=8000)