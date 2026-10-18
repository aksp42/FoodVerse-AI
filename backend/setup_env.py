"""
FoodVerse AI — Backend Environment Setup Script
Smart Bridge Activity 1.1

Usage:
    python setup_env.py

This script:
1. Verifies Python version (>= 3.9 required)
2. Creates/validates the virtual environment at backend/venv
3. Upgrades pip inside the venv
4. Installs all requirements.txt packages in the venv
5. Validates key imports work correctly
6. Copies .env.example to .env if .env is missing

Run this from the backend/ directory.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path


BACKEND_DIR = Path(__file__).parent.resolve()
VENV_DIR = BACKEND_DIR / "venv"
REQUIREMENTS = BACKEND_DIR / "requirements.txt"
ENV_FILE = BACKEND_DIR / ".env"
ENV_EXAMPLE = BACKEND_DIR / ".env.example"

MIN_PYTHON = (3, 9)


def run(cmd: list, **kwargs):
    """Run a subprocess command and stream output."""
    result = subprocess.run(cmd, **kwargs)
    return result.returncode == 0


def step(msg: str):
    print(f"\n{'='*60}")
    print(f"  {msg}")
    print('='*60)


def main():
    # ---- Step 1: Python version check ----------------------------------------
    step("Step 1: Python Version Check")
    ver = sys.version_info
    print(f"  Python: {ver.major}.{ver.minor}.{ver.micro} ({sys.executable})")
    if ver < MIN_PYTHON:
        print(f"  ERROR: Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]}+ is required.")
        sys.exit(1)
    print(f"  OK — Python {ver.major}.{ver.minor} meets the >= 3.9 requirement.")

    # ---- Step 2: Create virtual environment ----------------------------------
    step("Step 2: Virtual Environment")
    if VENV_DIR.exists():
        print(f"  Found existing venv at: {VENV_DIR}")
    else:
        print(f"  Creating venv at: {VENV_DIR}")
        ok = run([sys.executable, "-m", "venv", str(VENV_DIR)])
        if not ok:
            print("  ERROR: Failed to create venv.")
            sys.exit(1)
        print("  Venv created successfully.")

    # Determine venv Python path
    if sys.platform == "win32":
        venv_python = VENV_DIR / "Scripts" / "python.exe"
        activate_cmd = rf"  PowerShell : {VENV_DIR}\Scripts\Activate.ps1"
        activate_cmd_cmd = rf"  CMD        : {VENV_DIR}\Scripts\activate.bat"
    else:
        venv_python = VENV_DIR / "bin" / "python"
        activate_cmd = f"  bash/zsh: source {VENV_DIR}/bin/activate"
        activate_cmd_cmd = ""

    print(f"\n  Venv Python: {venv_python}")
    print(f"\n  To activate manually:")
    print(activate_cmd)
    if activate_cmd_cmd:
        print(activate_cmd_cmd)

    # ---- Step 3: Upgrade pip -------------------------------------------------
    step("Step 3: Upgrade pip, setuptools, wheel")
    run([str(venv_python), "-m", "pip", "install", "--upgrade",
         "pip", "setuptools", "wheel"],
        check=False)
    print("  pip upgraded.")

    # ---- Step 4: Install requirements ----------------------------------------
    step("Step 4: Install requirements.txt")
    if not REQUIREMENTS.exists():
        print(f"  ERROR: {REQUIREMENTS} not found.")
        sys.exit(1)
    print(f"  Installing from: {REQUIREMENTS}")
    print("  (This may take several minutes for large packages like torch...)\n")
    ok = run(
        [str(venv_python), "-m", "pip", "install", "-r", str(REQUIREMENTS)],
    )
    if not ok:
        print("\n  WARNING: Some packages may have failed. Check output above.")
    else:
        print("\n  All packages installed successfully.")

    # ---- Step 5: Validate key imports ----------------------------------------
    step("Step 5: Validate Key Imports")
    checks = [
        ("fastapi", "FastAPI"),
        ("uvicorn", "Uvicorn"),
        ("dotenv", "python-dotenv"),
        ("google.genai", "google-genai / Gemini"),
        ("PIL", "Pillow"),
        ("numpy", "NumPy"),
        ("cv2", "OpenCV Headless"),
        ("torch", "PyTorch"),
        ("torchvision", "Torchvision"),
        ("transformers", "Transformers"),
        ("pandas", "Pandas"),
        ("sklearn", "scikit-learn"),
        ("fpdf", "fpdf2"),
        ("requests", "Requests"),
    ]
    all_ok = True
    for module, label in checks:
        result = subprocess.run(
            [str(venv_python), "-c", f"import {module}; print({module}.__version__ if hasattr({module}, '__version__') else 'ok')"],
            capture_output=True, text=True
        )
        status = "OK " if result.returncode == 0 else "FAIL"
        version = result.stdout.strip() or result.stderr.strip().split("\n")[-1][:60]
        print(f"  [{status}] {label:20s} — {version}")
        if result.returncode != 0:
            all_ok = False

    # ---- Step 6: .env setup --------------------------------------------------
    step("Step 6: Environment Variables (.env)")
    if ENV_FILE.exists():
        print(f"  .env already exists at: {ENV_FILE}")
        print("  (Not overwriting — ensure GEMINI_API_KEY is set.)")
    elif ENV_EXAMPLE.exists():
        shutil.copy(ENV_EXAMPLE, ENV_FILE)
        print(f"  Created .env from .env.example at: {ENV_FILE}")
        print("  ACTION REQUIRED: Open .env and set your GEMINI_API_KEY.")
    else:
        print("  WARNING: No .env or .env.example found. Create .env manually.")

    # ---- Summary -------------------------------------------------------------
    step("Setup Complete")
    if all_ok:
        print("  All import validations PASSED.")
    else:
        print("  Some imports FAILED — check package installation above.")
    print()
    print("  To start the backend server:")
    if sys.platform == "win32":
        print(rf"    PowerShell: {VENV_DIR}\Scripts\Activate.ps1")
    else:
        print(f"    source {VENV_DIR}/bin/activate")
    print("    cd backend")
    print("    uvicorn app:app --reload --port 8000")
    print()


if __name__ == "__main__":
    main()
