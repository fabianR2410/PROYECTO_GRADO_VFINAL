# -*- coding: utf-8 -*-
"""
COVID-19 Metrics Analysis Pipeline
Main execution script
"""
import logging
import sys
from pathlib import Path
import argparse

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent / "scripts"))

from data_loader import CovidDataLoader
from data_cleaner import CovidDataCleaner
from data_imputer import CovidDataImputer
from feature_engineer import CovidFeatureEngineer
from data_saver import CovidDataSaver

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main(countries=None, quick_mode=False):
    """
    Execute the COVID-19 data analysis pipeline.
    
    Args:
        countries: List of countries to analyze (None for all)
        quick_mode: If True, use latest data snapshot for faster execution
    """
    try:
        print("\n" + "="*60)
        print("COVID-19 METRICS ANALYSIS PIPELINE")
        print("="*60 + "\n")
        
        # Step 1: Load data
        print("[1/5] Loading COVID-19 data...")
        loader = CovidDataLoader(data_dir="data/raw")
        source = 'owid_latest' if quick_mode else 'owid'
        data_file = loader.download_data(source=source)
        df = loader.load_data(data_file)
        
        if countries:
            df = df[df['location'].isin(countries)]
            print(f"   -> Filtered to {len(countries)} countries")
        
        print(f"   -> Loaded {len(df):,} records from {df['location'].nunique()} locations\n")
        
        # Step 2: Clean data
        print("[2/5] Cleaning data...")
        cleaner = CovidDataCleaner()
        df_clean = cleaner.clean_all(df)
        print(f"   -> Data cleaned: {len(df_clean):,} valid records\n")
        
        # Step 3: Impute missing values
        print("[3/5] Imputing missing values...")
        imputer = CovidDataImputer()
        df_imputed = imputer.smart_imputation(df_clean)
        print(f"   -> Missing values imputed\n")
        
        # Step 4: Create features
        print("[4/5] Creating features...")
        engineer = CovidFeatureEngineer()
        df_final = engineer.create_all_features(df_imputed)
        features_created = engineer.get_features_created()
        print(f"   -> Created {len(features_created)} new features\n")
        
        # Step 5: Save results
        print("[5/5] Saving results...")
        saver = CovidDataSaver(output_dir="data/processed")
        
        # Save in multiple formats
        parquet_file = saver.save_to_parquet(df_final, filename="covid_data_processed")
        csv_file = saver.save_to_csv(df_final, filename="covid_data_processed")
        
        # Save metadata
        metadata = {
            'countries': countries if countries else 'all',
            'quick_mode': quick_mode,
            'features_created': features_created
        }
        metadata_file = saver.save_metadata(df_final, metadata=metadata)
        stats_file = saver.save_summary_statistics(df_final)
        
        print(f"   -> Saved 4 files in data/processed/\n")
        
        # Final summary
        print("="*60)
        print("PIPELINE COMPLETED SUCCESSFULLY")
        print("="*60)
        print(f"\nResults:")
        print(f"   - Records processed: {len(df_final):,}")
        print(f"   - Total columns: {len(df_final.columns)}")
        print(f"   - Locations: {df_final['location'].nunique()}")
        print(f"   - New features: {len(features_created)}")
        print(f"\nFiles saved:")
        print(f"   - {parquet_file.name}")
        print(f"   - {csv_file.name}")
        print(f"   - {metadata_file.name}")
        print(f"   - {stats_file.name}")
        print("\nNext steps:")
        print("   1. Explore data: jupyter notebook script_prueba/exploracion.ipynb")
        print("   2. Run analysis: python script_prueba/analisis.py")
        print("="*60 + "\n")
        
    except Exception as e:
        logger.error(f"\nError in pipeline: {e}", exc_info=True)
        print("\nTroubleshooting:")
        print("   - Check your internet connection")
        print("   - Install dependencies: pip install -r requirements.txt")
        print("   - Check README.md for more information\n")
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="COVID-19 Metrics Analysis Pipeline"
    )
    parser.add_argument(
        '--countries',
        nargs='+',
        help='List of countries to analyze (default: all)',
        default=None
    )
    parser.add_argument(
        '--quick',
        action='store_true',
        help='Use latest data snapshot for faster execution'
    )
    
    args = parser.parse_args()
    main(countries=args.countries, quick_mode=args.quick)
