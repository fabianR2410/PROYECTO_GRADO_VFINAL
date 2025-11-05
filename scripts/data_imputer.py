# -*- coding: utf-8 -*-
"""
COVID-19 Data Imputer Module
Handles missing value imputation
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class CovidDataImputer:
    """Clase para imputar valores faltantes en datos de COVID-19."""
    
    def __init__(self):
        """Inicializa el imputador."""
        self.imputation_stats: Dict[str, int] = {
            "forward_filled": 0,
            "interpolated": 0,
            "filled_with_stats": 0,
            "filled_new_with_zero": 0
        }
    
    def smart_imputation(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Aplica imputación inteligente según el tipo de columna.
        
        Args:
            df: DataFrame con datos a imputar
            
        Returns:
            DataFrame con valores imputados
        """
        logger.info("Starting smart imputation...")

        df_imputed = df.copy()

        # 1️⃣ (NUEVO) Rellenar columnas estáticas (POBLACIÓN, etc.)
        df_imputed = self.fill_static_columns(df_imputed)

        # 2️⃣ Forward fill por país (para series acumuladas)
        df_imputed = self.forward_fill_by_location(df_imputed)

        # 3️⃣ Rellenar casos/muertes nuevas con 0
        new_cols = [col for col in df_imputed.columns if 'new_' in col.lower() and pd.api.types.is_numeric_dtype(df_imputed[col])]
        if new_cols:
            initial_nulls_new = df_imputed[new_cols].isnull().sum().sum()
            df_imputed[new_cols] = df_imputed[new_cols].fillna(0)
            filled_new = int(initial_nulls_new - df_imputed[new_cols].isnull().sum().sum())
            if filled_new > 0:
                logger.info(f"Filled {filled_new} 'new_*' values with 0")
                self.imputation_stats["filled_new_with_zero"] += filled_new

        # 4️⃣ Interpolación lineal por país (para valores continuos)
        df_imputed = self.interpolate_numeric(df_imputed)

        # 5️⃣ Imputación con estadísticas por país (último recurso)
        df_imputed = self.fill_with_statistics(df_imputed)

        logger.info("Smart imputation completed successfully ✅")

        # --- ¡ERROR CRÍTICO CORREGIDO! ---
        # La siguiente línea fue eliminada porque convertía
        # todos los NaN restantes (ej. 'gdp' de países sin datos) en 0.
        # df_imputed = df_imputed.fillna(0)
        # --- FIN DE LA CORRECCIÓN ---

        return df_imputed

    # ------------------------------------------------------------------
    # MÉTODOS DE IMPUTACIÓN
    # ------------------------------------------------------------------

    def fill_static_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Rellena columnas estáticas (como 'population') usando ffill y bfill.
        Estas columnas no cambian día a día, por lo que este método es seguro.
        """
        df_filled = df.copy()
        
        static_cols = [
            'population', 'population_density', 'median_age', 'aged_65_older', 
            'aged_70_older', 'gdp_per_capita', 'extreme_poverty', 
            'cardiovasc_death_rate', 'diabetes_prevalence', 'female_smokers', 
            'male_smokers', 'handwashing_facilities', 'hospital_beds_per_thousand', 
            'life_expectancy', 'human_development_index'
        ]
        
        # Guardar columnas que realmente existen en el df
        cols_to_fill = [col for col in static_cols if col in df_filled.columns]

        if not cols_to_fill:
            return df_filled

        if 'location' in df_filled.columns:
            # Rellenar primero hacia adelante, luego hacia atrás, por país
            df_filled[cols_to_fill] = df_filled.groupby('location')[cols_to_fill].ffill()
            df_filled[cols_to_fill] = df_filled.groupby('location')[cols_to_fill].bfill()
        else:
             # Si no hay 'location', rellenar en todo el df
            df_filled[cols_to_fill] = df_filled[cols_to_fill].ffill()
            df_filled[cols_to_fill] = df_filled[cols_to_fill].bfill()
        
        logger.info(f"Filled static columns (ffill/bfill) for: {cols_to_fill}")
        return df_filled

    def forward_fill_by_location(self, df: pd.DataFrame) -> pd.DataFrame:
        """Aplica forward fill por ubicación para series temporales."""
        df_filled = df.copy()

        if 'location' not in df_filled.columns:
            logger.warning("No 'location' column found, skipping forward fill by location")
            return df_filled

        fill_cols = [
            col for col in df_filled.columns
            if 'total' in col.lower() and pd.api.types.is_numeric_dtype(df_filled[col])
        ]
        
        # Excluir estáticos que contengan 'total' si se agregan por error
        fill_cols = [col for col in fill_cols if 'total_boosters' not in col]


        if not fill_cols:
            return df_filled

        initial_nulls = df_filled[fill_cols].isnull().sum().sum()

        for col in fill_cols:
            df_filled[col] = df_filled.groupby('location')[col].ffill()

        final_nulls = df_filled[fill_cols].isnull().sum().sum()
        filled = int(initial_nulls - final_nulls)
        self.imputation_stats["forward_filled"] += filled

        if filled > 0:
            logger.info(f"Forward filled {filled} values across {len(fill_cols)} columns")

        return df_filled

    def interpolate_numeric(self, df: pd.DataFrame) -> pd.DataFrame:
        """Interpola valores numéricos por ubicación (optimizado)."""
        df_interp = df.copy()

        if 'location' not in df_interp.columns:
            logger.warning("No 'location' column found, skipping interpolation")
            return df_interp

        numeric_cols = df_interp.select_dtypes(include=[np.number]).columns.tolist()
        
        # --- MEJORA: Excluir todas las columnas estáticas ---
        static_cols = [
            'iso_code', 'population', 'population_density', 'median_age', 
            'aged_65_older', 'aged_70_older', 'gdp_per_capita', 
            'extreme_poverty', 'cardiovasc_death_rate', 'diabetes_prevalence',
            'female_smokers', 'male_smokers', 'handwashing_facilities', 
            'hospital_beds_per_thousand', 'life_expectancy', 'human_development_index'
        ]
        
        exclude_cols = static_cols + [
            col for col in df_interp.columns if 'new_' in col.lower()
        ]
        numeric_cols = [col for col in numeric_cols if col not in exclude_cols]

        if not numeric_cols:
            logger.info("No columns to interpolate.")
            return df_interp

        initial_nulls = df_interp[numeric_cols].isnull().sum().sum()

        df_interp[numeric_cols] = df_interp.groupby('location')[numeric_cols].transform(
            lambda x: x.interpolate(
                method='linear',
                limit_direction='both',
                limit=7
            )
        )

        final_nulls = df_interp[numeric_cols].isnull().sum().sum()
        interpolated = int(initial_nulls - final_nulls)
        self.imputation_stats["interpolated"] += interpolated

        if interpolated > 0:
            logger.info(f"Interpolated {interpolated} numeric values across {len(numeric_cols)} columns")

        return df_interp

    def fill_with_statistics(self, df: pd.DataFrame, method: str = 'median') -> pd.DataFrame:
        """
        Rellena valores faltantes con estadísticas (media o mediana)
        agrupadas por país.
        """
        df_filled = df.copy()

        numeric_cols = df_filled.select_dtypes(include=[np.number]).columns.tolist()
        
        # --- MEJORA: Excluir todas las columnas estáticas ---
        static_cols = [
            'iso_code', 'population', 'population_density', 'median_age', 
            'aged_65_older', 'aged_70_older', 'gdp_per_capita', 
            'extreme_poverty', 'cardiovasc_death_rate', 'diabetes_prevalence',
            'female_smokers', 'male_smokers', 'handwashing_facilities', 
            'hospital_beds_per_thousand', 'life_expectancy', 'human_development_index'
        ]
        
        numeric_cols = [col for col in numeric_cols if col not in static_cols]

        if not numeric_cols or 'location' not in df_filled.columns:
            return df_filled

        initial_nulls = df_filled[numeric_cols].isnull().sum().sum()

        for col in numeric_cols:
            if df_filled[col].isnull().any():
                if method == 'mean':
                    df_filled[col] = df_filled.groupby('location')[col].transform(
                        lambda x: x.fillna(x.mean())
                    )
                else:  # median
                    df_filled[col] = df_filled.groupby('location')[col].transform(
                        lambda x: x.fillna(x.median())
                    )

        final_nulls = df_filled[numeric_cols].isnull().sum().sum()
        filled = int(initial_nulls - final_nulls)
        self.imputation_stats["filled_with_stats"] += filled

        if filled > 0:
            logger.info(f"Filled {filled} missing values with {method} by location")

        return df_filled

    # ------------------------------------------------------------------

    def get_imputation_report(self) -> Dict[str, int]:
        """Devuelve un reporte resumen de la imputación."""
        return self.imputation_stats


# ----------------------------------------------------------------------
# EJEMPLO DE USO (para pruebas locales)
# ----------------------------------------------------------------------
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    data = {
        "location": ["Ecuador"] * 5 + ["Peru"] * 5,
        "date": pd.date_range("2020-01-01", periods=5).tolist() * 2,
        "total_cases": [100, np.nan, 150, np.nan, 200, 50, 70, np.nan, 120, np.nan],
        "new_cases": [10, np.nan, 20, np.nan, 30, 5, np.nan, 10, np.nan, 15],
        "population": [17_000_000, 17_000_000, np.nan, 17_000_000, np.nan, 30_000_000, np.nan, np.nan, 30_000_000, 30_000_000],
        "other_metric": [1.1, np.nan, 1.3, np.nan, 1.5, 2.1, 2.2, np.nan, np.nan, 2.5]
    }

    df = pd.DataFrame(data)
    print("--- Antes de la imputación ---")
    print(df)
    print(f"\nNulos antes:\n{df.isnull().sum()}")

    imputer = CovidDataImputer()
    df_imputed = imputer.smart_imputation(df)

    print("\n--- Después de la imputación ---")
    print(df_imputed)
    print(f"\nNulos después:\n{df_imputed.isnull().sum()}")

    print("\n--- Reporte de imputación ---")
    print(imputer.get_imputation_report())