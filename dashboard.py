"""
Dashboard Launcher - Launches the Streamlit dashboard
"""

import subprocess
import sys
from pathlib import Path


def launch_dashboard(port: int = 8501):
    """
    Launch the Streamlit dashboard on the specified port
    """
    dashboard_path = Path(__file__).parent / "dashboard_app.py"

    if not dashboard_path.exists():
        print(f"❌ Dashboard app not found: {dashboard_path}")
        return

    print(f"🚀 Launching dashboard on http://localhost:{port}")
    print("Press Ctrl+C to stop the dashboard")

    try:
        # Launch streamlit
        cmd = [sys.executable, "-m", "streamlit", "run", str(dashboard_path), "--server.port", str(port)]
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n👋 Dashboard stopped")
    except Exception as e:
        print(f"❌ Failed to launch dashboard: {e}")