# -*- coding: utf-8 -*-
"""
Installation Test Script
Verifies that all dependencies and modules are properly installed
"""
import sys
from pathlib import Path

def test_imports():
    """Test that all required packages can be imported."""
    print("Verificando importaciones de paquetes...")
    
    required_packages = [
        ('pandas', 'pandas'),
        ('numpy', 'numpy'),
        ('requests', 'requests'),
        ('openpyxl', 'openpyxl'),
        ('pyarrow', 'pyarrow'),
        ('fastapi', 'fastapi'),
        ('uvicorn', 'uvicorn'),
        ('streamlit', 'streamlit'),
        ('plotly', 'plotly'),
    ]
    
    failed = []
    for name, import_name in required_packages:
        try:
            __import__(import_name)
            print(f"  OK: {name}")
        except ImportError:
            print(f"  FALLO: {name}")
            failed.append(name)
    
    return len(failed) == 0, failed

def test_modules():
    """Test that all project modules can be imported."""
    print("\nVerificando modulos del proyecto...")
    
    # Add scripts to path
    sys.path.insert(0, str(Path(__file__).parent / "scripts"))
    
    modules = [
        'data_loader',
        'data_cleaner',
        'data_imputer',
        'feature_engineer',
        'data_saver'
    ]
    
    failed = []
    for module in modules:
        try:
            __import__(module)
            print(f"  OK: {module}")
        except Exception as e:
            print(f"  FALLO: {module} - {e}")
            failed.append(module)
    
    return len(failed) == 0, failed

def test_directories():
    """Test that all required directories exist."""
    print("\nVerificando estructura de directorios...")
    
    required_dirs = [
        'data',
        'data/raw',
        'data/processed',
        'scripts',
        'script_prueba',
        'api',
        'dashboard'
    ]
    
    project_root = Path(__file__).parent
    failed = []
    
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        if full_path.exists():
            print(f"  OK: {dir_path}")
        else:
            print(f"  FALLO: {dir_path} no existe")
            failed.append(dir_path)
    
    return len(failed) == 0, failed

def main():
    """Run all tests."""
    print("="*60)
    print("COVID-19 PROJECT - TEST DE INSTALACION")
    print("="*60)
    print()
    
    all_passed = True
    
    # Test imports
    passed, failed = test_imports()
    if not passed:
        print(f"\nPaquetes faltantes: {', '.join(failed)}")
        print("Instala con: pip install -r requirements.txt")
        all_passed = False
    
    # Test modules
    passed, failed = test_modules()
    if not passed:
        print(f"\nModulos con problemas: {', '.join(failed)}")
        all_passed = False
    
    # Test directories
    passed, failed = test_directories()
    if not passed:
        print(f"\nDirectorios faltantes: {', '.join(failed)}")
        all_passed = False
    
    # Final result
    print()
    print("="*60)
    if all_passed:
        print("RESULTADO: TODOS LOS TESTS PASARON")
        print("El proyecto esta correctamente instalado y listo para usar.")
        print()
        print("Siguientes pasos:")
        print("  1. Procesar datos: python quick_start.py")
        print("  2. Iniciar API: python start_api.py")
        print("  3. Iniciar Dashboard: python start_dashboard.py")
    else:
        print("RESULTADO: ALGUNOS TESTS FALLARON")
        print("Por favor, resuelve los problemas indicados arriba.")
    print("="*60)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
