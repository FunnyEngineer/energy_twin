@echo off
REM Setup script for Energy Twin Finder (Windows)

echo 🌍 Setting up Energy Twin Finder...
echo.

REM Create virtual environment
echo 📦 Creating virtual environment...
python -m venv venv

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install dependencies
echo 📥 Installing dependencies...
pip install -r requirements.txt

REM Create .env file if it doesn't exist
if not exist .env (
    echo 📝 Creating .env file...
    copy .env.example .env
    echo.
    echo ⚠️  Please edit .env and add your OpenWeatherMap API key
    echo    Get a free key at: https://openweathermap.org/api
)

REM Generate sample data
echo 🏠 Generating sample home data...
python generate_data.py

echo.
echo ✅ Setup complete!
echo.
echo To start the application:
echo   1. Activate virtual environment:
echo      venv\Scripts\activate
echo   2. Run the server:
echo      python app.py
echo   3. Open http://localhost:5000 in your browser
echo.
pause
