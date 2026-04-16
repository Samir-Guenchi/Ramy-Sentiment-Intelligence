@echo off
REM Ramy Sentiment Intelligence - Web Application Launcher
REM Windows Batch Script

echo ========================================
echo Ramy Sentiment Intelligence
echo Web Application Launcher
echo ========================================
echo.

REM Check if virtual environment exists
if not exist ".venv" (
    echo ERROR: Virtual environment not found!
    echo Please create it first: python -m venv .venv
    pause
    exit /b 1
)

REM Activate virtual environment (try both possible locations)
echo [1/3] Activating virtual environment...
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
) else if exist ".venv\bin\activate" (
    REM Unix-style venv on Windows, just set PATH
    set PATH=%CD%\.venv\bin;%PATH%
) else (
    echo Warning: Could not find activation script, continuing anyway...
)

REM Check if dependencies are installed
echo [2/3] Checking dependencies...
python -c "import fastapi" 2>nul
if errorlevel 1 (
    echo.
    echo Dependencies not found. Installing...
    pip install fastapi==0.109.0 starlette==0.35.1 "pydantic<2" uvicorn jinja2 markupsafe python-multipart pandas numpy
    if errorlevel 1 (
        echo.
        echo ERROR: Failed to install dependencies!
        pause
        exit /b 1
    )
)

REM Start the server
echo [3/3] Starting web server...
echo.
echo ========================================
echo Server will start on: http://localhost:8000
echo Press CTRL+C to stop the server
echo ========================================
echo.

python -m uvicorn webapp.main:app --host 0.0.0.0 --port 8000

REM If server stops
echo.
echo Server stopped.
pause
