# -*- coding: utf-8 -*-
"""
COVID-19 Data Loader Module
-----------------------------------
Módulo encargado de cargar, descargar y gestionar datos
de COVID-19 desde fuentes oficiales o archivos locales,
con soporte para agregar fila mundial (“World”).

"""

from __future__ import annotations
import logging
from pathlib import Path
from typing import Optional, Dict
import pandas as pd
import numpy as np
import requests

# ==========================================================
# CONFIGURACIÓN GLOBAL DE LOGGING
# ==========================================================
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

if not logger.handlers:
    console_handler = logging.StreamHandler()
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)


# ==========================================================
# CLASE PRINCIPAL
# ==========================================================
class CovidDataLoader:
    """
    Carga y administra datasets de COVID-19 desde múltiples fuentes.
    
    Se encarga de la lógica de descarga, gestión de caché local y 
    la creación de agregados (como 'World') antes de que los
    datos pasen al pipeline de limpieza.
    """

    def __init__(self, data_dir: str = "data") -> None:
        """
        Inicializa el cargador de datos y asegura la estructura de carpetas.

        Args:
            data_dir (str): Directorio base donde se almacenarán los datos.
        """
        self.data_dir: Path = Path(data_dir)
        self.raw_dir: Path = self.data_dir / "raw"
        self.raw_dir.mkdir(parents=True, exist_ok=True)

        # Fuentes oficiales de OWID
        self.urls: Dict[str, str] = {
            "owid": "https://covid.ourworldindata.org/data/owid-covid-data.csv",
            "owid_latest": "https://covid.ourworldindata.org/data/latest/owid-covid-latest.csv",
        }

    # ----------------------------------------------------------
    # BÚSQUEDA DE ARCHIVOS EXISTENTES
    # ----------------------------------------------------------
    def _find_existing_file(self, source: str) -> Optional[Path]:
        """
        Busca archivos cacheados en diferentes ubicaciones y devuelve el más grande.
        
        Esto permite flexibilidad si el usuario ha movido el archivo
        o si existen múltiples versiones.

        Args:
            source (str): El identificador de la fuente (ej. "owid").

        Returns:
            Optional[Path]: La ruta al archivo más grande encontrado, o None.
        """
        possible_locations = [
            self.data_dir / "owid-covid-data.csv",
            self.data_dir / "owid-covid-data.xlsx",
            self.raw_dir / f"{source}.csv",
            self.raw_dir / f"{source}.xlsx",
        ]

        found_files = [
            (path, path.stat().st_size)
            for path in possible_locations
            if path.exists()
        ]

        if not found_files:
            return None

        # Ordenar por tamaño de archivo (descendente) y tomar el primero
        found_files.sort(key=lambda x: x[1], reverse=True)
        best_file = found_files[0][0]
        logger.info(f"Using cached dataset: {best_file} ({found_files[0][1] / 1e6:.2f} MB)")
        return best_file

    # ----------------------------------------------------------
    # DESCARGA DE DATOS
    # ----------------------------------------------------------
    def download_data(self, source: str = "owid", force: bool = False) -> Path:
        """
        Descarga datos desde OWID o usa una copia local si existe.

        Args:
            source (str): La clave de la fuente a descargar (definida en self.urls).
            force (bool): Si es True, fuerza la descarga ignorando el caché.

        Returns:
            Path: La ruta al archivo descargado o al archivo en caché.
            
        Raises:
            ValueError: Si la fuente (source) no es válida.
        """
        if source not in self.urls:
            raise ValueError(f"Fuente no válida: {source}")

        cached_file = self._find_existing_file(source)
        
        # 1. Usar caché si existe y no se fuerza la descarga
        if cached_file and not force:
            return cached_file

        # 2. Intentar descargar
        target_path = self.raw_dir / f"{source}.csv"
        try:
            logger.info(f"Descargando datos desde {self.urls[source]} ...")
            response = requests.get(self.urls[source], timeout=60)
            response.raise_for_status()

            target_path.write_bytes(response.content)
            logger.info(f"Datos descargados correctamente en {target_path}")
            return target_path

        # 3. Manejar errores (sin conexión, etc.)
        except requests.exceptions.ConnectionError:
            logger.warning("Sin conexión a internet. Buscando archivo en caché...")
            cached = self._find_existing_file(source)
            if cached:
                return cached
            logger.warning("No se encontró caché. Generando datos de ejemplo...")
            return self._create_sample_data(target_path)

        except Exception as e:
            logger.error(f"Error durante la descarga: {e}")
            cached = self._find_existing_file(source)
            if cached:
                return cached
            logger.warning("Creando datos sintéticos para pruebas...")
            return self._create_sample_data(target_path)

    # ----------------------------------------------------------
    # CREACIÓN DE DATOS DE EJEMPLO (GLOBAL)
    # ----------------------------------------------------------
    def _create_sample_data(self, filepath: Path) -> Path:
        """Genera un dataset de ejemplo global (América, Europa, Asia, África, Oceanía)."""
        logger.info("Generando dataset sintético global de COVID-19...")

        continents = {
            "South America": ["Ecuador", "Peru", "Colombia", "Brazil", "Argentina", "Chile"],
            "North America": ["United States", "Canada", "Mexico"],
            "Europe": ["Spain", "France", "Germany", "Italy", "United Kingdom"],
            "Asia": ["China", "India", "Japan", "South Korea", "Indonesia"],
            "Africa": ["South Africa", "Nigeria", "Egypt", "Kenya", "Morocco"],
            "Oceania": ["Australia", "New Zealand", "Fiji"],
        }

        dates = pd.date_range("2020-01-01", "2025-10-24", freq="D")
        data = []

        for continent, countries in continents.items():
            for country in countries:
                # Generar una población estática para el país
                country_population = (hash(country) % 50_000_000) + 1_000_000
                
                for i, date in enumerate(dates):
                    base = 100 + i * 5
                    new_cases = int(base * (1 + 0.05 * ((hash(f"{country}{date}") % 20) - 10)))
                    new_cases = max(new_cases, 0)

                    record = {
                        "iso_code": country[:3].upper(),
                        "continent": continent,
                        "location": country,
                        "date": date,
                        "total_cases": new_cases * (i + 1),
                        "new_cases": new_cases,
                        "new_deaths": int(new_cases * 0.02),
                        "population": country_population, 
                        "people_vaccinated": int((i / len(dates)) * 10_000_000) if date.year >= 2021 else None,
                    }
                    data.append(record)

        df = pd.DataFrame(data)
        df.to_csv(filepath, index=False)
        logger.info(f"✅ Dataset sintético global creado con {len(df):,} registros → {filepath}")
        return filepath

    # ----------------------------------------------------------
    # AGREGAR FILA MUNDIAL (FUNCIÓN CORREGIDA Y ETIQUETADA)
    # ----------------------------------------------------------
    def _add_global_totals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Agrega fila global ("World") sumando métricas de países.
        
        Descarta los agregados de OWID (ej. 'Asia', 'Europe') y
        recalcula el total 'World' desde cero para asegurar consistencia.
        Maneja promedios ponderados por población para métricas estáticas.

        Args:
            df (pd.DataFrame): El DataFrame crudo cargado.

        Returns:
            pd.DataFrame: Un DataFrame que contiene solo países y una fila 
                          'World' recalculada.
        """
        if df.empty or 'date' not in df.columns:
            return df
        
        # 1. Filtrar solo países (excluir 'World' y continentes de OWID)
        countries_df = df[
            df['continent'].notna() & (df['location'] != 'World')
        ].copy()

        if countries_df.empty:
            logger.warning("No country data found to aggregate 'World' row.")
            return df

        # 2. Definir tipos de columnas para la agregación
        
        # Columnas que deben sumarse por fecha (casos, muertes, tests, etc.)
        time_series_sum_cols = [
            'total_cases', 'new_cases', 'total_deaths', 'new_deaths', 
            'total_tests', 'new_tests', 'total_vaccinations', 'new_vaccinations',
            'people_vaccinated', 'people_fully_vaccinated', 'total_boosters',
            'hosp_patients', 'icu_patients'
        ]
        
        # Columnas estáticas que deben sumarse (solo población)
        static_sum_cols = ['population']
        
        # Columnas estáticas que deben promediarse (ponderadas por población)
        static_avg_cols = [
            'median_age', 'aged_65_older', 'aged_70_older', 'gdp_per_capita', 
            'extreme_poverty', 'cardiovasc_death_rate', 'diabetes_prevalence',
            'female_smokers', 'male_smokers', 'handwashing_facilities', 
            'hospital_beds_per_thousand', 'life_expectancy', 'human_development_index'
        ]

        # Filtrar columnas que realmente existen en el DataFrame
        time_series_sum_cols = [c for c in time_series_sum_cols if c in countries_df.columns]
        static_sum_cols = [c for c in static_sum_cols if c in countries_df.columns]
        static_avg_cols = [c for c in static_avg_cols if c in countries_df.columns]

        # 3. Calcular totales de series temporales (agrupados por fecha)
        world_time_series_df = countries_df.groupby('date')[time_series_sum_cols].sum(numeric_only=True).reset_index()

        # 4. Calcular totales estáticos (una sola vez)
        
        # Tomar el último registro de cada país (que tiene la población más reciente)
        latest_countries_df = countries_df.drop_duplicates(subset=['location'], keep='last')
        
        world_static_totals = {}
        
        # Sumar población
        if 'population' in static_sum_cols:
            world_population = latest_countries_df['population'].sum()
            world_static_totals['population'] = world_population
            
            # --- Lógica de Promedio Ponderado (Nivel Profesional) ---
            # Un promedio simple de 'gdp_per_capita' estaría mal.
            # Se debe ponderar por la población de cada país.
            for col in static_avg_cols:
                # (Métrica * Población)
                weighted_col_sum = (latest_countries_df[col] * latest_countries_df['population']).sum()
                
                # (Suma de [Métrica * Población]) / (Población Total)
                if world_population > 0:
                    world_static_totals[col] = weighted_col_sum / world_population
                else:
                    world_static_totals[col] = np.nan
        
        # 5. Combinar los DataFrames
        world_df = world_time_series_df.copy()
        
        # Añadir las columnas estáticas (se repetirán para cada fecha)
        for col, value in world_static_totals.items():
            world_df[col] = value
            
        world_df['location'] = 'World'
        world_df['iso_code'] = 'OWID_WRL'
        world_df['continent'] = 'Global' # Usamos 'Global' para distinguirlo

        # 6. Unir los países + nuestro nuevo 'World'
        df_with_world = pd.concat([countries_df, world_df], ignore_index=True)
        
        return df_with_world.sort_values(['location', 'date']).reset_index(drop=True)

    # ----------------------------------------------------------
    # CARGA DE DATOS
    # ----------------------------------------------------------
    def load_data(
        self,
        source: str = "owid",
        force: bool = False,
        local_filepath: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Carga los datos en un DataFrame desde local o remoto.

        Args:
            source (str): Fuente ('owid' o 'owid_latest').
            force (bool): Forzar descarga nueva.
            local_filepath (Optional[str]): Ruta directa a un archivo CSV/Excel local.

        Returns:
            pd.DataFrame: Datos cargados y con la fila 'World' agregada.
            
        Raises:
            ValueError: Si el dataset cargado está vacío.
        """

        # --- Si se pasa un archivo local ---
        if local_filepath:
            filepath = Path(local_filepath)
            logger.info(f"Cargando datos directamente desde archivo local: {filepath}")
        else:
            filepath = self.download_data(source, force)
            logger.info(f"Cargando datos desde {filepath}")

        try:
            if filepath.suffix in {".xlsx", ".xls"}:
                df = pd.read_excel(filepath)
            else:
                df = pd.read_csv(filepath)
        except Exception as e:
            logger.error(f"Error al leer el archivo {filepath}: {e}")
            raise

        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"], errors="coerce")

        # Agregar fila global (recalculada)
        df = self._add_global_totals(df)

        if df.empty:
            raise ValueError("El dataset cargado está vacío.")

        logger.info(f"{len(df):,} registros cargados — {df['location'].nunique()} países/agregados detectados.")
        return df