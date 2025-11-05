"""
Start COVID-19 API Server (with auto-reload)
"""
import sys
from pathlib import Path
import uvicorn

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

def main():
    """Start the API server in reload mode."""
    
    # Ya no necesitas: from api.main import app
    
    print("="*60)
    print("COVID-19 API Server (Modo Desarrollo)")
    print("="*60)
    print("\nStarting server...")
    print("API will be available at: http://localhost:8000")
    print("Interactive docs at: http://localhost:8000/docs")
    print("Alternative docs at: http://localhost:8000/redoc")
    print("\n[INFO] Servidor en modo RELOAD. Se reiniciará solo si guardas cambios.")
    print("Press CTRL+C to stop the server")
    print("="*60)
    print()
    
    uvicorn.run(
        "api.main:app",  # <--- Pasa la app como string
        host="0.0.0.0",
        port=8000,
        log_level="info",
        reload=True      # <--- Esta es la magia
    )

if __name__ == "__main__":
    main()