@echo off
setlocal
cls

:: Check for Docker
docker --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Docker is not installed or not in PATH. Please install Docker.
    exit /b 1
)

:: Check for Python 3.10
python --version 2>NUL | findstr "3.10" >nul
if %ERRORLEVEL% NEQ 0 (
    echo [WARNING] Python 3.10 not found. Installing...
    
    :: Run the silent installer for Python 3.10
    start /wait "" "%~dp0extras\win_python.exe" /quiet InstallAllUsers=1 PrependPath=1 Include_test=0

    :: Refresh environment variables so the new Python installation is recognized
    set "PATH=%PATH%;C:\Program Files\Python310\Scripts;C:\Program Files\Python310\"

    :: Verify installation
    python --version 2>NUL | findstr "3.10" >nul
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Python 3.10 installation failed. Please install it manually.
        exit /b 1
    )
    echo [INFO] Python 3.10 installed successfully.
)

:: Create and activate virtual environment silently
if not exist venv (
    echo [INFO] Creating virtual environment...
    python -m venv venv >nul 2>&1
)

call venv\Scripts\activate >nul 2>&1

:: Install dependencies, suppressing output except for errors
if exist requirements.txt (
    echo [INFO] Installing dependencies...
    pip install -r requirements.txt >nul 2>&1
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Failed to install dependencies. Check requirements.txt.
        exit /b 1
    )
) else (
    echo [ERROR] requirements.txt not found!
    exit /b 1
)

:: Change to the /app directory
cd /d "%~dp0\app"

:: Start Docker Desktop on Windows if not running
tasklist | findstr /I "Docker Desktop.exe" >nul
if %ERRORLEVEL% NEQ 0 (
    echo [INFO] Starting Docker Desktop...
    start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    timeout /t 10 >nul
)

:: Ensure Docker is running
docker info >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Docker is not running. Please start Docker manually.
    exit /b 1
)

:: Find an open port (default to 5000)
set PORT=5000
for /f "tokens=5" %%a in ('netstat -ano ^| find ":5000" ^| find "LISTEN"') do (
    echo [INFO] Port 5000 is in use. Searching for an open port...
    for /l %%p in (5001,1,5100) do (
        netstat -ano | findstr "%%p" >nul || (
            set PORT=%%p
            goto PORT_FOUND
        )
    )
    echo [ERROR] No open ports found! Exiting...
    exit /b 1
)

:PORT_FOUND
echo [INFO] Running Flask on port %PORT%

:: Set the environment variable for Flask
set FLASK_PORT=%PORT%

:: Run Flask
set FLASK_APP=app.py
start /b python -m flask run --host=127.0.0.1 --port=%PORT%

:: Open browser to Flask site
timeout /t 3 >nul
start http://127.0.0.1:%PORT%

echo [SUCCESS] Flask server running at http://127.0.0.1:%PORT%
exit /b 0
