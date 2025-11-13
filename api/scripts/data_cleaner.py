# -*- coding: utf-8 -*-
"""
COVID-19 Data Cleaner Module
Handles data cleaning and preprocessing
"""

import pandas as pd
import numpy as np
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class CovidDataCleaner:
    """Clase para limpiar y preprocesar datos de COVID-19."""

    def __init__(self, missing_threshold: float = 0.5):
        """
        Inicializa el limpiador de datos.

        Args:
            missing_threshold (float): Umbral de valores faltantes para eliminar columnas (0.0 a 1.0)
        """
        self.missing_threshold: float = missing_threshold
        self.columns_dropped: List[str] = []
        self.duplicates_removed: int = 0
        self.outliers_handled: int = 0

    # ==========================================================
    # MÉTODO PRINCIPAL
    # ==========================================================
    def clean_data(self, df: 'pd.DataFrame') -> 'pd.DataFrame':
        """
        Aplica todo el proceso de limpieza de datos.

        Args:
            df (pd.DataFrame): DataFrame con datos crudos.

        Returns:
            pd.DataFrame: DataFrame limpio.
        """
        logger.info(f"Starting data cleaning... Initial shape: {df.shape}")

        df_clean = df.copy()

        # 1️⃣ Eliminar duplicados
        df_clean = self.remove_duplicates(df_clean)

        # 2️⃣ Manejar columnas con muchos valores faltantes
        df_clean = self.handle_missing_columns(df_clean)

        # 3️⃣ Validar y limpiar fechas
        df_clean = self.clean_dates(df_clean)

        # 4️⃣ Limpiar valores numéricos
        df_clean = self.clean_numeric_values(df_clean)

        # 5️⃣ Manejar outliers
        df_clean = self.handle_outliers(df_clean)

        logger.info(f"✅ Data cleaning completed. Final shape: {df_clean.shape}")
        logger.info(f"   Duplicates removed: {self.duplicates_removed}")
        logger.info(f"   Columns dropped: {len(self.columns_dropped)}")
        logger.info(f"   Outliers handled: {self.outliers_handled}")

        return df_clean

    # ==========================================================
    # MÉTODOS INDIVIDUALES
    # ==========================================================
    def remove_duplicates(self, df: 'pd.DataFrame') -> 'pd.DataFrame':
        """Elimina filas duplicadas."""
        initial_rows = len(df)

        if 'location' in df.columns and 'date' in df.columns:
            df_clean = df.drop_duplicates(subset=['location', 'date'], keep='last')
        else:
            df_clean = df.drop_duplicates()

        self.duplicates_removed = initial_rows - len(df_clean)

        if self.duplicates_removed > 0:
            logger.info(f"Removed {self.duplicates_removed} duplicate rows")

        return df_clean

    def handle_missing_columns(self, df: 'pd.DataFrame') -> 'pd.DataFrame':
        """Elimina columnas con exceso de valores faltantes."""
        missing_pct = df.isnull().sum() / len(df)

        # Identificar columnas a eliminar
        cols_to_drop = missing_pct[missing_pct > self.missing_threshold].index.tolist()
        cols_to_drop = [str(c) for c in cols_to_drop]

        # No eliminar columnas esenciales
        essential_cols = ['location', 'date', 'iso_code', 'continent', 'population']
        cols_to_drop = [col for col in cols_to_drop if col not in essential_cols]

        if cols_to_drop:
            df_clean = df.drop(columns=cols_to_drop)
            self.columns_dropped = [str(c) for c in cols_to_drop]
            logger.info(
                f"Dropped {len(cols_to_drop)} columns with >{self.missing_threshold*100:.1f}% missing values"
            )
        else:
            df_clean = df

        return df_clean

    def clean_dates(self, df: 'pd.DataFrame') -> 'pd.DataFrame':
        """Limpia y valida columna de fechas."""
        if 'date' not in df.columns:
            logger.warning("⚠️ No 'date' column found.")
            return df

        df_clean = df.copy()

        # Guardar una copia para depuración si es necesario
        original_dates_for_debug = df_clean['date'].copy()

        if not pd.api.types.is_datetime64_any_dtype(df_clean['date']):
            
            # --- INICIO DE LA CORRECCIÓN ---
            # Se elimina el 'infer_datetime_format=True' obsoleto.
            # Esta es la forma moderna y robusta de manejarlo.
            df_clean['date'] = pd.to_datetime(df_clean['date'], errors='coerce')
            # --- FIN DE LA CORRECCIÓN ---


        invalid_dates_mask = df_clean['date'].isnull()
        invalid_dates_count = invalid_dates_mask.sum()
        
        if invalid_dates_count > 0:
            # Mostrar una muestra de las fechas problemáticas
            problematic_dates_sample = original_dates_for_debug[invalid_dates_mask].unique()
            logger.warning(f"Removing {invalid_dates_count} rows with invalid dates")
            logger.info(f"Sample of problematic dates being removed: {problematic_dates_sample[:10]}")
            
            df_clean = df_clean[df_clean['date'].notna()]

        if not df_clean.empty and 'location' in df_clean.columns:
            df_clean = df_clean.sort_values(['location', 'date'])
            
        return df_clean

    def clean_numeric_values(self, df: 'pd.DataFrame') -> 'pd.DataFrame':
        """Limpia valores numéricos (negativos, infinitos, etc)."""
        df_clean = df.copy()
        numeric_cols = df_clean.select_dtypes(include=[np.number]).columns

        for col in numeric_cols:
            df_clean[col] = df_clean[col].replace([np.inf, -np.inf], np.nan)

            # Para columnas que no pueden ser negativas
            if any(keyword in col.lower() for keyword in ['total', 'new', 'people', 'population', 'hosp', 'icu']):
                negative_count = (df_clean[col] < 0).sum()
                if negative_count > 0:
                    logger.debug(f"Replacing {negative_count} negative values in {col} with 0")
                    # Reemplazar negativos con 0 en lugar de NaN para estas columnas
                    df_clean.loc[df_clean[col] < 0, col] = 0

        return df_clean

    def handle_outliers(
        self,
        df: 'pd.DataFrame',
        method: str = 'iqr',
        factor: float = 3.0
    ) -> 'pd.DataFrame':
        """
        Maneja valores atípicos en columnas numéricas (usando "capping").
        """
        df_clean = df.copy()

        numeric_cols = df_clean.select_dtypes(include=[np.number]).columns
        
        # --- MEJORA: Excluir todas las columnas estáticas y de identificación ---
        exclude_cols = [
            'iso_code', 'population', 'population_density', 'median_age', 
            'aged_65_older', 'aged_70_older', 'gdp_per_capita', 
            'extreme_poverty', 'cardiovasc_death_rate', 'diabetes_prevalence',
            'female_smokers', 'male_smokers', 'handwashing_facilities', 
            'hospital_beds_per_thousand', 'life_expectancy', 'human_development_index',
            # También excluir columnas temporales creadas
            'year', 'month', 'day', 'day_of_week', 'week_of_year', 'quarter', 'is_weekend'
        ]
        
        numeric_cols = [col for col in numeric_cols if col not in exclude_cols]
        outliers_total = 0

        for col in numeric_cols:
            if df_clean[col].dropna().empty:
                continue

            if method == 'iqr':
                # --- Lógica de IQR (ya estaba correcta) ---
                if 'location' in df_clean.columns:
                    Q1 = df_clean.groupby('location')[col].transform('quantile', 0.25)
                    Q3 = df_clean.groupby('location')[col].transform('quantile', 0.75)
                else:
                    Q1 = df_clean[col].quantile(0.25)
                    Q3 = df_clean[col].quantile(0.75)

                IQR = Q3 - Q1
                
                lower_bound = Q1 - (factor * IQR)
                upper_bound = Q3 + (factor * IQR)
                
                outliers_lower = (df_clean[col] < lower_bound)
                outliers_upper = (df_clean[col] > upper_bound)
                
                outlier_count = outliers_lower.sum() + outliers_upper.sum()
                
                if outlier_count > 0:
                    df_clean.loc[outliers_lower, col] = lower_bound
                    df_clean.loc[outliers_upper, col] = upper_bound
                    outliers_total += outlier_count

            elif method == 'zscore':
                # --- INICIO DE LA CORRECCIÓN DE TIPO (Z-SCORE) ---
                
                z_scores = pd.Series(0.0, index=df_clean.index) # Inicializar
                lower_bound_z = pd.Series(0.0, index=df_clean.index)
                upper_bound_z = pd.Series(0.0, index=df_clean.index)

                if 'location' in df_clean.columns:
                    # Caso 1: 'std' es una Serie
                    mean = df_clean.groupby('location')[col].transform('mean')
                    std_series = df_clean.groupby('location')[col].transform('std')
                    
                    # Aplicar .replace() a la Serie
                    std_series = std_series.replace(0, np.nan) 
                    
                    z_scores = (df_clean[col] - mean) / std_series
                    
                    # Límites (Series)
                    lower_bound_z = mean - factor * std_series
                    upper_bound_z = mean + factor * std_series

                else:
                    # Caso 2: 'std' es un float
                    mean = df_clean[col].mean()
                    std_float = df_clean[col].std()
                    
                    if std_float == 0 or pd.isna(std_float):
                        # z_scores se queda en 0 (como se inicializó)
                        pass
                    else:
                        z_scores = (df_clean[col] - mean) / std_float
                    
                    # Límites (Floats)
                    lower_bound_z = mean - factor * (std_float if pd.notna(std_float) else 0)
                    upper_bound_z = mean + factor * (std_float if pd.notna(std_float) else 0)

                # Reemplazar NaNs (de std=0 o std=nan) por 0, ya que no son outliers
                z_scores = z_scores.fillna(0) 

                outliers_lower = (z_scores < -factor)
                outliers_upper = (z_scores > factor)
                
                outlier_count = outliers_lower.sum() + outliers_upper.sum()
                
                if outlier_count > 0:
                    # Aplicar "capping" (tope)
                    # .loc funciona bien si el límite es un float o una Serie alineada
                    df_clean.loc[outliers_lower, col] = lower_bound_z
                    df_clean.loc[outliers_upper, col] = upper_bound_z
                    outliers_total += outlier_count
                # --- FIN DE LA CORRECCIÓN DE TIPO ---
                else:
                    continue
            else:
                logger.warning(f"Unknown method '{method}' for outlier detection.")
                continue

        self.outliers_handled = outliers_total

        if outliers_total > 0:
            logger.info(f"Handled {outliers_total} outliers (capped) across numeric columns")

        return df_clean

    # ==========================================================
    # REPORTE FINAL
    # ==========================================================
    def get_cleaning_report(self) -> Dict[str, object]:
        """Genera un reporte con estadísticas de limpieza."""
        return {
            'duplicates_removed': self.duplicates_removed,
            'columns_dropped': len(self.columns_dropped),
            'dropped_column_names': self.columns_dropped,
            'outliers_handled': self.outliers_handled,
        }
# --- ARCHIVO TERMINA AQUÍ ---
# (Asegúrate de que no haya nada en la línea 280, ni siquiera un '}')