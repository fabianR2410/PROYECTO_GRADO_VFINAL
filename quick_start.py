# -*- coding: utf-8 -*-
"""
COVID-19 Quick Start Script
Simple script to get started quickly with COVID-19 data analysis
"""
import logging
import sys
from pathlib import Path

# --- CORRECCIÓN ---
# Eliminamos sys.path.insert (ya no necesario)
from scripts.data_loader import CovidDataLoader
from scripts.data_cleaner import CovidDataCleaner
from scripts.data_imputer import CovidDataImputer
from scripts.feature_engineer import CovidFeatureEngineer
from scripts.data_saver import CovidDataSaver
# ------------------

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def quick_start():
    """Execute a quick start pipeline for COVID-19 data analysis."""
    try:
        print("\n" + "="*60)
        print("COVID-19 QUICK START (MODO CASO DE ESTUDIO)")
        print("="*60 + "\n")
        
        # 1. Load data
        print("[1/5] Loading data...")
        loader = CovidDataLoader()

        # --- CAMBIO PARA CASO DE ESTUDIO ---
        # Usamos la ruta a tu archivo local
        RUTA_DATOS_LOCALES = "data/raw/owid-covid-data.csv"
        
        print(f"   Cargando datos locales desde: {RUTA_DATOS_LOCALES}")
        df = loader.load_data(local_filepath=RUTA_DATOS_LOCALES)
        # --- FIN DEL CAMBIO ---
        
        print(f"   Loaded {len(df):,} records\n")
        
        # 2. Clean data
        print("[2/5] Cleaning data...")
        cleaner = CovidDataCleaner()
        df_clean = cleaner.clean_data(df)
        print(f"   Cleaned data: {len(df_clean):,} records\n")
        
        # 3. Impute missing values
        print("[3/5] Imputing missing values...")
        imputer = CovidDataImputer()
        df_imputed = imputer.smart_imputation(df_clean)
        print(f"   Imputation completed\n")
        
        # 4. Create features
        print("[4/5] Creating features...")
        engineer = CovidFeatureEngineer()
        df_final = engineer.create_all_features(df_imputed)
        print(f"   Created {len(engineer.get_features_created())} new features\n")
        
        # 5. Save results
        print("[5/5] Saving results...")
        saver = CovidDataSaver(output_dir="data/processed")
        
        # Guardar como Parquet con un nombre fijo para que la API siempre lea el mismo
        parquet_file = saver.save_to_parquet(df_final, filename="covid_processed_data")
        
        # Save metadata
        metadata = {
            'mode': 'case_study',
            'features_created': engineer.get_features_created()
        }
        metadata_file = saver.save_metadata(df_final, metadata=metadata, filename="case_study_metadata")
        
        # Save summary statistics
        stats_file = saver.save_summary_statistics(df_final, filename="case_study_summary")
        
        print(f"   Saved 3 files in data/processed/\n")
        
        # Final summary
        print("="*60)
        print("QUICK START COMPLETED")
        print("="*60)
        print(f"\nResults:")
        print(f"   - Records processed: {len(df_final):,}")
        print(f"   - Total columns: {len(df_final.columns)}")
        print(f"   - Locations: {df_final['location'].nunique()}")
        print(f"   - New features: {len(engineer.get_features_created())}")
        print(f"\nFiles saved:")
        print(f"   - {parquet_file.name}")
        print(f"   - {metadata_file.name}")
        print(f"   - {stats_file.name}")
        print(f"\nNext steps:")
        print(f"   1. Start API: python start_api.py")
        print(f"   2. Start Dashboard: python start_dashboard.py")
        print("="*60 + "\n")
        
    except Exception as e:
        logger.error(f"\nError: {e}", exc_info=False)
        print("\nTroubleshooting:")
        print("   - Ensure 'data/raw/owid-covid-data.csv' exists.")
        print("   - Install dependencies: pip install -r requirements.txt")
        sys.exit(1)


if __name__ == "__main__":
    quick_start()