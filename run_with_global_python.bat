@echo off
echo ========================================
echo Ramy Sentiment Intelligence
echo Using Global Python Environment
echo ========================================
echo.
echo Server will start on: http://localhost:8000
echo API Documentation: http://localhost:8000/docs
echo.
echo Press CTRL+C to stop the server
echo.

cd /d D:\project\Ramy
"C:\Users\Samir Guenchi\AppData\Local\Programs\Python\Python312\python.exe" -m uvicorn webapp.main:app --host 0.0.0.0 --port 8000

pause
