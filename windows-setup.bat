@echo off
REM Setup script for Windows

echo Setting up Inventory Management System Backend...

REM Check Python version
python --version

REM Create virtual environment
echo Creating virtual environment...
python -m venv venv

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Setup database
echo Setting up database...
python ..\scripts\setup_database.py

echo.
echo Setup complete!
echo.
echo To start the server, run:
echo   venv\Scripts\activate.bat
echo   uvicorn main:app --reload --host 0.0.0.0 --port 8000
echo.
echo API Documentation: http://localhost:8000/docs
