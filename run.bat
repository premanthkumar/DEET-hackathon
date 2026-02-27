@echo off
:: Quick launcher — activates venv and starts the Flask server
call .venv\Scripts\activate.bat 2>nul || (
    echo [!] Virtual environment not found. Run setup.bat first.
    pause & exit /b 1
)
echo [*] Starting Resume-to-DEET server...
echo [*] Open your browser at: http://localhost:5000
echo.
python app.py
