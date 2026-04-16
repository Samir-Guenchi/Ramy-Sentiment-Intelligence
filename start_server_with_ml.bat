@echo off
REM Ramy Web Server with ML Support
echo Starting Ramy Sentiment Intelligence Web Server...
echo.

REM Set Python path to include Python 3.12 packages
set PYTHONPATH=C:\Users\Samir Guenchi\AppData\Local\Programs\Python\Python312\Lib\site-packages;%PYTHONPATH%

REM Change to project directory
cd /d D:\project\Ramy

REM Start the server
echo Server starting on http://localhost:8000
echo Press CTRL+C to stop
echo.
python -m uvicorn webapp.main:app --host 0.0.0.0 --port 8000
