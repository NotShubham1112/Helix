#!/usr/bin/env python
import subprocess
import os
import sys

if __name__ == "__main__":
    try:
        os.chdir(r"D:\Parth\Helix\helix-backend")
        subprocess.call([
            sys.executable, "-m", "uvicorn",
            "app.main:app",
            "--reload",
            "--host", "0.0.0.0",
            "--port", "8000"
        ])
    except KeyboardInterrupt:
        print("\nShutting down Helix Backend...")
        sys.exit(0)
