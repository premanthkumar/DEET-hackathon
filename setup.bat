@echo off
:: ═══════════════════════════════════════════════════════════════
:: Resume-to-DEET System — One-click Windows Setup Script
:: ═══════════════════════════════════════════════════════════════
title DEET Portal Setup
color 0A

echo.
echo  ╔══════════════════════════════════════════════════════════╗
echo  ║     Resume-to-DEET Instant Registration System          ║
echo  ║          Setup Script for Windows                       ║
echo  ╚══════════════════════════════════════════════════════════╝
echo.

:: ── Step 1: Check Python ────────────────────────────────────────

where python >nul 2>&1
IF ERRORLEVEL 1 (
    echo [!] Python not found. Please install Python 3.10+ from:
    echo     https://www.python.org/downloads/
    echo     Make sure to check "Add Python to PATH" during install.
    pause
    exit /b 1
)

python --version
echo [OK] Python found.
echo.

:: ── Step 2: Create virtual environment ─────────────────────────

IF NOT EXIST ".venv" (
    echo [*] Creating virtual environment...
    python -m venv .venv
    echo [OK] Virtual environment created.
) ELSE (
    echo [OK] Virtual environment already exists.
)

:: ── Step 3: Activate venv ──────────────────────────────────────

echo [*] Activating virtual environment...
call .venv\Scripts\activate.bat

:: ── Step 4: Install dependencies ───────────────────────────────

echo.
echo [*] Installing Python dependencies...
python -m pip install --upgrade pip --quiet
python -m pip install -r requirements.txt

IF ERRORLEVEL 1 (
    echo [!] Dependency installation failed. Check requirements.txt
    pause
    exit /b 1
)
echo [OK] All dependencies installed.
echo.

:: ── Step 5: Download spaCy language model ──────────────────────

echo [*] Downloading spaCy English model...
python -m spacy download en_core_web_sm
echo [OK] spaCy model ready.
echo.

:: ── Step 6: Initialize database ────────────────────────────────

echo [*] Initializing SQLite database...
python -c "import database; database.init_db(); print('[OK] Database initialized.')"

:: ── Step 7: Done ────────────────────────────────────────────────

echo.
echo  ╔══════════════════════════════════════════════════════════╗
echo  ║  Setup complete! Run the app with:                      ║
echo  ║    python app.py                                        ║
echo  ║  Then open: http://localhost:5000                       ║
echo  ╚══════════════════════════════════════════════════════════╝
echo.
pause
