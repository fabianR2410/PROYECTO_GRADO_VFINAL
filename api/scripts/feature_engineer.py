# -*- coding: utf-8 -*-
"""
COVID-19 Feature Engineering Module
Creates derived features and metrics
"""
import pandas as pd
import numpy as np
import logging
from typing import List, Optional, Dict

logger = logging.getLogger(__name__)


class CovidFeatureEngineer:
    """Class for creating features from COVID-19 data."""
    
    def __init__(self):
        """Initialize the feature engineer."""
        self.features_created = []
    
    def _validate_dataframe(self, df: pd.DataFrame) -> None:
        """
        Validate input DataFrame.
        
        Args:
            df: DataFrame to validate
            
        Raises:
            ValueError: If DataFrame is empty or invalid
        """
        if df is None or df.empty:
            raise ValueError("DataFrame cannot be None or empty")
    
    def _safe_division(self, numerator: pd.Series, denominator: pd.Series, 
                      multiply_by: float = 1.0) -> pd.Series:
        """
        Perform safe division avoiding division by zero and inf values.
        
        Args:
            numerator: Numerator series
            denominator: Denominator series
            multiply_by: Factor to multiply result by
            
        Returns:
            Result series with NaN for invalid operations
        """
        result = np.where(
            (denominator != 0) & (denominator.notna()) & (numerator.notna()),
            (numerator / denominator) * multiply_by,
            np.nan
        )
        return pd.Series(result, index=numerator.index)
    
    def create_rate_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create rate and percentage features.
        
        Args:
            df: DataFrame with COVID-19 data
            
        Returns:
            DataFrame with rate features
        """
        self._validate_dataframe(df)
        df_feat = df.copy()
        
        # Case fatality rate (CFR)
        if 'total_deaths' in df_feat.columns and 'total_cases' in df_feat.columns:
            df_feat['case_fatality_rate'] = self._safe_division(
                df_feat['total_deaths'], 
                df_feat['total_cases'], 
                multiply_by=100
            )
            self.features_created.append('case_fatality_rate')
            logger.debug("Created case_fatality_rate feature")
        
        # Test positivity rate (if not already present)
        if 'positive_rate' not in df_feat.columns:
            if 'new_cases' in df_feat.columns and 'new_tests' in df_feat.columns:
                df_feat['positive_rate'] = self._safe_division(
                    df_feat['new_cases'], 
                    df_feat['new_tests'], 
                    multiply_by=100
                )
                self.features_created.append('positive_rate')
                logger.debug("Created positive_rate feature")
        
        # Vaccination coverage rate
        if 'people_fully_vaccinated' in df_feat.columns and 'population' in df_feat.columns:
            df_feat['vaccination_coverage'] = self._safe_division(
                df_feat['people_fully_vaccinated'], 
                df_feat['population'], 
                multiply_by=100
            )
            self.features_created.append('vaccination_coverage')
            logger.debug("Created vaccination_coverage feature")
        
        # Hospital occupancy rate (if applicable)
        if 'icu_patients' in df_feat.columns and 'hosp_patients' in df_feat.columns:
            df_feat['icu_to_hospitalized_ratio'] = self._safe_division(
                df_feat['icu_patients'], 
                df_feat['hosp_patients'], 
                multiply_by=100
            )
            self.features_created.append('icu_to_hospitalized_ratio')
            logger.debug("Created icu_to_hospitalized_ratio feature")
        
        rate_features_count = len([f for f in self.features_created if 'rate' in f or 'coverage' in f or 'ratio' in f])
        logger.info(f"Created {rate_features_count} rate features")
        
        return df_feat
    
    def create_moving_averages(self, df: pd.DataFrame, windows: Optional[List[int]] = None) -> pd.DataFrame:
        """
        Create moving average features.
        
        Args:
            df: DataFrame with COVID-19 data
            windows: List of window sizes (default: [7, 14])
            
        Returns:
            DataFrame with moving average features
        """
        self._validate_dataframe(df)
        
        if windows is None:
            windows = [7, 14]
        
        if not windows or not all(isinstance(w, int) and w > 0 for w in windows):
            raise ValueError("Windows must be a list of positive integers")
        
        df_feat = df.copy()
        
        # Ensure proper sorting
        if 'location' in df_feat.columns and 'date' in df_feat.columns:
            df_feat = df_feat.sort_values(['location', 'date']).reset_index(drop=True)
        else:
            logger.warning("Missing 'location' or 'date' columns, sorting may be incorrect")
        
        # Columns to create moving averages for
        columns = ['new_cases', 'new_deaths', 'new_tests', 'new_vaccinations']
        available_columns = [col for col in columns if col in df_feat.columns]
        
        if not available_columns:
            logger.warning("No columns available for moving averages")
            return df_feat
        
        for col in available_columns:
            for window in windows:
                ma_col = f'{col}_ma{window}'
                try:
                    if 'location' in df_feat.columns:
                        df_feat[ma_col] = df_feat.groupby('location')[col].transform(
                            lambda x: x.rolling(window=window, min_periods=1, center=False).mean()
                        )
                    else:
                        df_feat[ma_col] = df_feat[col].rolling(
                            window=window, min_periods=1, center=False
                        ).mean()
                    self.features_created.append(ma_col)
                except Exception as e:
                    logger.error(f"Error creating moving average {ma_col}: {str(e)}")
        
        logger.info(f"Created {len(windows) * len(available_columns)} moving average features")
        
        return df_feat
    
    def create_growth_rate_features(self, df: pd.DataFrame, periods: int = 1) -> pd.DataFrame:
        """
        Create growth rate features.
        
        Args:
            df: DataFrame with COVID-19 data
            periods: Number of periods for calculating growth rate (default: 1)
            
        Returns:
            DataFrame with growth rate features
        """
        self._validate_dataframe(df)
        df_feat = df.copy()
        
        if 'location' in df_feat.columns and 'date' in df_feat.columns:
            df_feat = df_feat.sort_values(['location', 'date']).reset_index(drop=True)
        
        # Columns to calculate growth rate for
        columns = ['total_cases', 'total_deaths', 'total_vaccinations']
        available_columns = [col for col in columns if col in df_feat.columns]
        
        for col in available_columns:
            growth_col = f'{col}_growth_rate'
            try:
                if 'location' in df_feat.columns:
                    # Calculate percentage change by location
                    df_feat[growth_col] = df_feat.groupby('location')[col].pct_change(periods=periods) * 100
                else:
                    df_feat[growth_col] = df_feat[col].pct_change(periods=periods) * 100
                
                # Replace inf values with NaN
                df_feat[growth_col] = df_feat[growth_col].replace([np.inf, -np.inf], np.nan)
                
                # Cap extreme values (optional: helps with outliers)
                df_feat[growth_col] = df_feat[growth_col].clip(-1000, 1000)
                
                self.features_created.append(growth_col)
            except Exception as e:
                logger.error(f"Error creating growth rate {growth_col}: {str(e)}")
        
        logger.info(f"Created {len(available_columns)} growth rate features")
        
        return df_feat
    
    def create_per_capita_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create per capita features (if not already present).
        
        Args:
            df: DataFrame with COVID-19 data
            
        Returns:
            DataFrame with per capita features
        """
        self._validate_dataframe(df)
        df_feat = df.copy()
        
        if 'population' not in df_feat.columns:
            logger.warning("Population column not found, skipping per capita features")
            return df_feat
        
        # Check for zero or negative population values
        invalid_pop = (df_feat['population'] <= 0) | (df_feat['population'].isna())
        if invalid_pop.any():
            logger.warning(f"Found {invalid_pop.sum()} rows with invalid population values")
        
        # Define base columns and their per capita counterparts
        per_capita_mapping = {
            'total_cases': 'total_cases_per_million',
            'total_deaths': 'total_deaths_per_million',
            'new_cases': 'new_cases_per_million',
            'new_deaths': 'new_deaths_per_million',
            'total_tests': 'total_tests_per_thousand',
            'new_tests': 'new_tests_per_thousand'
        }
        
        features_created_count = 0
        for base_col, per_capita_col in per_capita_mapping.items():
            if base_col in df_feat.columns and per_capita_col not in df_feat.columns:
                # Determine multiplier based on column name
                multiplier = 1_000_000 if 'million' in per_capita_col else 1_000
                
                df_feat[per_capita_col] = self._safe_division(
                    df_feat[base_col], 
                    df_feat['population'], 
                    multiply_by=multiplier
                )
                self.features_created.append(per_capita_col)
                features_created_count += 1
        
        logger.info(f"Created {features_created_count} per capita features")
        
        return df_feat
    
    def create_temporal_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create temporal features from date column.
        
        Args:
            df: DataFrame with COVID-19 data
            
        Returns:
            DataFrame with temporal features
        """
        self._validate_dataframe(df)
        df_feat = df.copy()
        
        if 'date' not in df_feat.columns:
            logger.warning("Date column not found, skipping temporal features")
            return df_feat
        
        try:
            # Ensure date is datetime
            df_feat['date'] = pd.to_datetime(df_feat['date'], errors='coerce')
            
            # Check for invalid dates
            invalid_dates = df_feat['date'].isna()
            if invalid_dates.any():
                logger.warning(f"Found {invalid_dates.sum()} invalid dates")
            
            # Create temporal features
            df_feat['year'] = df_feat['date'].dt.year
            df_feat['month'] = df_feat['date'].dt.month
            df_feat['day'] = df_feat['date'].dt.day
            df_feat['day_of_week'] = df_feat['date'].dt.dayofweek
            df_feat['week_of_year'] = df_feat['date'].dt.isocalendar().week
            df_feat['quarter'] = df_feat['date'].dt.quarter
            df_feat['is_weekend'] = df_feat['day_of_week'].isin([5, 6]).astype(int)
            
            # Days since start of pandemic (assuming earliest date is start)
            if 'location' in df_feat.columns:
                df_feat['days_since_first_case'] = df_feat.groupby('location')['date'].transform(
                    lambda x: (x - x.min()).dt.days
                )
            else:
                min_date = df_feat['date'].min()
                df_feat['days_since_first_case'] = (df_feat['date'] - min_date).dt.days
            
            temporal_features = ['year', 'month', 'day', 'day_of_week', 'week_of_year', 
                               'quarter', 'is_weekend', 'days_since_first_case']
            self.features_created.extend(temporal_features)
            
            logger.info(f"Created {len(temporal_features)} temporal features")
            
        except Exception as e:
            logger.error(f"Error creating temporal features: {str(e)}")
        
        return df_feat
    
    def create_lag_features(self, df: pd.DataFrame, lags: Optional[List[int]] = None) -> pd.DataFrame:
        """
        Create lag features for time series analysis.
        
        Args:
            df: DataFrame with COVID-19 data
            lags: List of lag periods (default: [1, 7, 14])
            
        Returns:
            DataFrame with lag features
        """
        self._validate_dataframe(df)
        
        if lags is None:
            lags = [1, 7, 14]
        
        if not lags or not all(isinstance(lag, int) and lag > 0 for lag in lags):
            raise ValueError("Lags must be a list of positive integers")
        
        df_feat = df.copy()
        
        if 'location' in df_feat.columns and 'date' in df_feat.columns:
            df_feat = df_feat.sort_values(['location', 'date']).reset_index(drop=True)
        
        # Columns to create lags for
        columns = ['new_cases', 'new_deaths', 'new_tests', 'new_vaccinations']
        available_columns = [col for col in columns if col in df_feat.columns]
        
        if not available_columns:
            logger.warning("No columns available for lag features")
            return df_feat
        
        for col in available_columns:
            for lag in lags:
                lag_col = f'{col}_lag{lag}'
                try:
                    if 'location' in df_feat.columns:
                        df_feat[lag_col] = df_feat.groupby('location')[col].shift(lag)
                    else:
                        df_feat[lag_col] = df_feat[col].shift(lag)
                    self.features_created.append(lag_col)
                except Exception as e:
                    logger.error(f"Error creating lag feature {lag_col}: {str(e)}")
        
        logger.info(f"Created {len(lags) * len(available_columns)} lag features")
        
        return df_feat
    
    def create_cumulative_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create cumulative sum features.
        
        Args:
            df: DataFrame with COVID-19 data
            
        Returns:
            DataFrame with cumulative features
        """
        self._validate_dataframe(df)
        df_feat = df.copy()
        
        if 'location' in df_feat.columns and 'date' in df_feat.columns:
            df_feat = df_feat.sort_values(['location', 'date']).reset_index(drop=True)
        
        # Daily columns to create cumulative sums for (if not already present)
        daily_cols = {
            'new_cases': 'total_cases',
            'new_deaths': 'total_deaths',
            'new_tests': 'total_tests',
            'new_vaccinations': 'total_vaccinations'
        }
        
        features_created_count = 0
        for daily_col, cumsum_col in daily_cols.items():
            if daily_col in df_feat.columns and cumsum_col not in df_feat.columns:
                try:
                    if 'location' in df_feat.columns:
                        df_feat[cumsum_col] = df_feat.groupby('location')[daily_col].cumsum()
                    else:
                        df_feat[cumsum_col] = df_feat[daily_col].cumsum()
                    
                    # Fill NaN values with 0 for cumulative sums
                    df_feat[cumsum_col] = df_feat[cumsum_col].fillna(0)
                    
                    self.features_created.append(cumsum_col)
                    features_created_count += 1
                except Exception as e:
                    logger.error(f"Error creating cumulative feature {cumsum_col}: {str(e)}")
        
        logger.info(f"Created {features_created_count} cumulative features")
        
        return df_feat
    
    def create_difference_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create difference features (change from previous day).
        
        Args:
            df: DataFrame with COVID-19 data
            
        Returns:
            DataFrame with difference features
        """
        self._validate_dataframe(df)
        df_feat = df.copy()
        
        if 'location' in df_feat.columns and 'date' in df_feat.columns:
            df_feat = df_feat.sort_values(['location', 'date']).reset_index(drop=True)
        
        # Columns to create differences for
        columns = ['new_cases', 'new_deaths']
        available_columns = [col for col in columns if col in df_feat.columns]
        
        for col in available_columns:
            diff_col = f'{col}_diff'
            try:
                if 'location' in df_feat.columns:
                    df_feat[diff_col] = df_feat.groupby('location')[col].diff()
                else:
                    df_feat[diff_col] = df_feat[col].diff()
                self.features_created.append(diff_col)
            except Exception as e:
                logger.error(f"Error creating difference feature {diff_col}: {str(e)}")
        
        logger.info(f"Created {len(available_columns)} difference features")
        
        return df_feat
    
    def create_all_features(self, df: pd.DataFrame, 
                          include_difference: bool = False) -> pd.DataFrame:
        """
        Create all features using the complete feature engineering pipeline.
        
        Args:
            df: DataFrame with COVID-19 data
            include_difference: Whether to include difference features (default: False)
            
        Returns:
            DataFrame with all features
        """
        self._validate_dataframe(df)
        logger.info("Starting feature engineering pipeline...")
        
        # Reset features list for this run
        self.features_created = []
        
        df_feat = df.copy()
        
        # Create different types of features in logical order
        df_feat = self.create_temporal_features(df_feat)
        df_feat = self.create_per_capita_features(df_feat)
        df_feat = self.create_rate_features(df_feat)
        df_feat = self.create_moving_averages(df_feat)
        df_feat = self.create_growth_rate_features(df_feat)
        df_feat = self.create_lag_features(df_feat)
        df_feat = self.create_cumulative_features(df_feat)
        
        if include_difference:
            df_feat = self.create_difference_features(df_feat)
        
        logger.info(f"Feature engineering completed: {len(self.features_created)} raw features created (pre-cleanup)")

        # --- ¡INICIO DE LA MODIFICACIÓN! ---
        # Paso final: Eliminar todas las columnas de ingeniería 
        # que no son útiles para el dashboard final.
        
        METRICS_TO_DROP = [
            # Temporal features (created by create_temporal_features)
            'year', 'month', 'day', 'day_of_week', 'week_of_year', 'quarter', 'is_weekend',
            'days_since_first_case', 'Days Since First Case', # Añadir PascalCase por si acaso

            # Lag features (created by create_lag_features)
            'new_cases_lag1', 'new_cases_lag7', 'new_cases_lag14',
            'new_deaths_lag1', 'new_deaths_lag7', 'new_deaths_lag14',
            'new_tests_lag1', 'new_tests_lag7', 'new_tests_lag14',
            'new_vaccinations_lag1', 'new_vaccinations_lag7', 'new_vaccinations_lag14',
            
            # PascalCase Lag (de las capturas de pantalla, por si acaso)
            'New Cases Lag1', 'New Cases Lag7', 'New Cases Lag14',
            'New Deaths Lag1', 'New Deaths Lag7', 'New Deaths Lag14',

            # Difference features (created by create_difference_features)
            'new_cases_diff', 'new_deaths_diff',

            # Moving Averages (created by create_moving_averages)
            # Nota: Mantenemos las columnas '_smoothed' (que vienen de OWID) 
            # y eliminamos nuestras '_ma' calculadas.
            'new_cases_ma7', 'new_cases_ma14',
            'new_deaths_ma7', 'new_deaths_ma14',
            'new_tests_ma7', 'new_tests_ma14',
            'new_vaccinations_ma7', 'new_vaccinations_ma14',
            
            # PascalCase MA (de las capturas de pantalla)
            'New Cases Ma7', 'New Deaths Ma7',

            # Other junk from screenshots (or other sources)
            'New People Vaccinated Smoothed',
            'New People Vaccinated Smoothed Per Hundred'
        ]
        
        # Obtener las columnas que SÍ existen en el DataFrame para evitar errores
        columns_to_drop = [col for col in METRICS_TO_DROP if col in df_feat.columns]
        
        if columns_to_drop:
            df_feat = df_feat.drop(columns=columns_to_drop)
            logger.info(f"Final cleanup: Dropped {len(columns_to_drop)} intermediate engineering features.")
        else:
            logger.info("Final cleanup: No intermediate engineering features found to drop.")
        # --- FIN DE LA MODIFICACIÓN ---
        
        logger.info(f"Final dataset shape (post-cleanup): {df_feat.shape}")
        
        return df_feat
    
    def get_features_created(self) -> List[str]:
        """
        Get list of features created by this engineer.
        (Note: May include features dropped during cleanup)
        
        Returns:
            List of feature names
        """
        return self.features_created.copy()
    
    def get_feature_summary(self) -> Dict[str, int]:
        """
        Get summary of features created by category.
        (Note: Based on features created *before* cleanup)
        
        Returns:
            Dictionary with feature counts by category
        """
        summary = {
            'temporal': len([f for f in self.features_created if any(t in f for t in ['year', 'month', 'day', 'week', 'quarter'])]),
            'rate': len([f for f in self.features_created if 'rate' in f or 'ratio' in f]),
            'per_capita': len([f for f in self.features_created if 'per_million' in f or 'per_thousand' in f]),
            'moving_average': len([f for f in self.features_created if '_ma' in f]),
            'growth': len([f for f in self.features_created if 'growth' in f]),
            'lag': len([f for f in self.features_created if '_lag' in f]),
            'cumulative': len([f for f in self.features_created if 'total_' in f and f not in ['total_cases', 'total_deaths']]),
            'difference': len([f for f in self.features_created if '_diff' in f]),
            'other': 0
        }
        
        # Calculate 'other' features
        categorized = sum(summary.values())
        summary['other'] = len(self.features_created) - categorized
        
        return summary
    
    def reset_features_list(self) -> None:
        """Reset the list of created features."""
        self.features_created = []
        logger.debug("Features list reset")