@echo off
echo Starting Miraat Backend Server...
echo.
echo Navigate to http://localhost:8000/hi to test the application
echo.
cd /d "%~dp0"
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
pause