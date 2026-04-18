#!/usr/bin/env python
import subprocess
import os
import sys

os.chdir(r"D:\Parth\Helix\helix-backend")
sys.exit(subprocess.call([
    sys.executable, "-m", "uvicorn",
    "app.main:app",
    "--reload",
    "--host", "127.0.0.1",
    "--port", "8000"
]))
