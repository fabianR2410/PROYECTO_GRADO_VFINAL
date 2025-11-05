# -*- coding: utf-8 -*-
"""
Start COVID-19 Dashboard
"""
import subprocess
import sys
from pathlib import Path

def main():
    """Start the dashboard."""
    print("="*60)
    print("COVID-19 Interactive Dashboard")
    print("="*60)
    print("\nStarting dashboard...")
    print("Dashboard will be available at: http://localhost:8501")
    print("\nPress CTRL+C to stop the dashboard")
    print("="*60)
    print()
    
    # Get the path to the dashboard app
    dashboard_path = Path(__file__).parent / "dashboard" / "dashboard.py"
    
    # Run streamlit with subprocess
    try:
        subprocess.run([
            sys.executable, 
            "-m", 
            "streamlit", 
            "run", 
            str(dashboard_path),
            "--server.headless=true"
        ])
    except KeyboardInterrupt:
        print("\n\nDashboard stopped by user")
    except Exception as e:
        print(f"\nError starting dashboard: {e}")
        print("\nAlternatively, you can start it manually with:")
        print(f"streamlit run dashboard/app.py")

if __name__ == "__main__":
    main()