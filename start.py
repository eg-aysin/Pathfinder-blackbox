"""Launch all 4 services. Run: python start.py"""
import subprocess
import sys
import os
import time
import webbrowser
from pathlib import Path

ROOT = Path(__file__).parent

SERVICES = [
    ("Salesforce Mock", "salesforce_mock", 8003),
    ("Record Box",      "recordbox",       8002),
    ("Pathfinder",      "pathfinder",      8001),
    ("EnerKey",         "enerkey",         8000),
]

processes = []

try:
    for name, folder, port in SERVICES:
        cwd = ROOT / folder
        print(f"Starting {name:20s} on http://localhost:{port}")
        p = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "main:app",
             "--host", "127.0.0.1", "--port", str(port), "--reload"],
            cwd=str(cwd),
        )
        processes.append((name, p))
        time.sleep(1)

    print("\nAll services running! Opening browser...")
    print("Press Ctrl+C to stop all services.\n")
    webbrowser.open("http://localhost:8000")

    # Wait forever until Ctrl+C
    for name, p in processes:
        p.wait()

except KeyboardInterrupt:
    print("\nShutting down...")
    for name, p in processes:
        p.terminate()
    print("All services stopped.")
