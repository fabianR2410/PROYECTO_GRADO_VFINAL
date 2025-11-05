# -*- coding: utf-8 -*-
"""
COVID-19 Data Saver Module
Handles saving processed data in various formats
"""
import pandas as pd
import json
from pathlib import Path
from datetime import datetime
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class CovidDataSaver:
    """Class for saving processed COVID-19 data."""

    def __init__(self, output_dir: str = "data/processed"):
        """
        Initialize the data saver.

        Args:
            output_dir: Directory where processed data will be saved
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def save_to_csv(self, df: pd.DataFrame, filename: Optional[str] = None) -> Path:
        if filename is None:
            filename = f"covid_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        file_path = self.output_dir / f"{filename}.csv"
        logger.info(f"Saving data to CSV: {file_path}")
        df.to_csv(file_path, index=False)
        logger.info(f"Data saved successfully: {len(df)} rows")
        return file_path

    def save_to_parquet(self, df: pd.DataFrame, filename: Optional[str] = None) -> Path:
        if filename is None:
            filename = f"covid_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        file_path = self.output_dir / f"{filename}.parquet"
        logger.info(f"Saving data to Parquet: {file_path}")
        df.to_parquet(file_path, index=False, engine='pyarrow')
        logger.info(f"Data saved successfully: {len(df)} rows")
        return file_path

    def save_to_json(self, df: pd.DataFrame, filename: Optional[str] = None) -> Path:
        if filename is None:
            filename = f"covid_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        file_path = self.output_dir / f"{filename}.json"
        logger.info(f"Saving data to JSON: {file_path}")
        df.to_json(file_path, orient='records', date_format='iso', indent=2)
        logger.info(f"Data saved successfully: {len(df)} rows")
        return file_path

    def save_to_excel(self, df: pd.DataFrame, filename: Optional[str] = None, 
                      sheet_name: str = 'COVID-19 Data') -> Path:
        if filename is None:
            filename = f"covid_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        file_path = self.output_dir / f"{filename}.xlsx"
        logger.info(f"Saving data to Excel: {file_path}")
        df.to_excel(file_path, sheet_name=sheet_name, index=False, engine='openpyxl')
        logger.info(f"Data saved successfully: {len(df)} rows")
        return file_path

    def save_by_country(self, df: pd.DataFrame, format: str = 'csv') -> list:
        if 'location' not in df.columns:
            raise ValueError("DataFrame must have 'location' column")

        countries_dir = self.output_dir / 'by_country'
        countries_dir.mkdir(exist_ok=True)

        saved_files = []
        countries = df['location'].unique()
        logger.info(f"Saving data for {len(countries)} countries...")

        for country in countries:
            country_df = df[df['location'] == country]
            # Convertir explícitamente a string para evitar errores de Pylance
            safe_country_name = str(country).replace(' ', '_').replace('/', '_')

            if format == 'csv':
                file_path = countries_dir / f"{safe_country_name}.csv"
                country_df.to_csv(file_path, index=False)
            elif format == 'parquet':
                file_path = countries_dir / f"{safe_country_name}.parquet"
                country_df.to_parquet(file_path, index=False)
            elif format == 'json':
                file_path = countries_dir / f"{safe_country_name}.json"
                country_df.to_json(file_path, orient='records', date_format='iso')
            else:
                raise ValueError(f"Unsupported format: {format}")

            saved_files.append(file_path)

        logger.info(f"Saved {len(saved_files)} country files")
        return saved_files

    def save_metadata(self, df: pd.DataFrame, metadata: Optional[dict] = None, 
                      filename: Optional[str] = None) -> Path:
        if filename is None:
            filename = f"metadata_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        file_path = self.output_dir / f"{filename}.json"

        meta = {
            'generated_at': datetime.now().isoformat(),
            'total_rows': len(df),
            'total_columns': len(df.columns),
            'columns': df.columns.tolist(),
            'date_range': {
                'start': df['date'].min().isoformat() if 'date' in df.columns else None,
                'end': df['date'].max().isoformat() if 'date' in df.columns else None
            },
            'locations': df['location'].nunique() if 'location' in df.columns else 0,
            'data_types': df.dtypes.astype(str).to_dict()
        }

        if metadata:
            meta['custom'] = metadata

        logger.info(f"Saving metadata: {file_path}")
        with open(file_path, 'w') as f:
            json.dump(meta, f, indent=2)

        return file_path

    def save_summary_statistics(self, df: pd.DataFrame, filename: Optional[str] = None) -> Path:
        if filename is None:
            filename = f"statistics_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        file_path = self.output_dir / f"{filename}.csv"
        logger.info(f"Saving summary statistics: {file_path}")

        stats = df.describe(include='all').transpose()
        stats['missing_count'] = df.isna().sum()
        stats['missing_percentage'] = (df.isna().sum() / len(df) * 100).round(2)

        stats.to_csv(file_path)
        logger.info(f"Statistics saved successfully")
        return file_path

    def save_all_formats(self, df: pd.DataFrame, base_filename: Optional[str] = None) -> dict:
        if base_filename is None:
            base_filename = f"covid_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        saved_files = {}
        logger.info("Saving data in all formats...")

        saved_files['csv'] = self.save_to_csv(df, base_filename)
        saved_files['parquet'] = self.save_to_parquet(df, base_filename)
        saved_files['json'] = self.save_to_json(df, base_filename)
        saved_files['metadata'] = self.save_metadata(df, filename=f"{base_filename}_metadata")
        saved_files['statistics'] = self.save_summary_statistics(df, filename=f"{base_filename}_statistics")

        logger.info(f"All formats saved successfully in {self.output_dir}")
        return saved_files