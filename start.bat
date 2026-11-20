@echo off
setlocal enabledelayedexpansion

cd /d "%~dp0"

echo ============================================================
echo   Day 6: ML Lifecycle ^& Pipelines - JupyterLab Launcher
echo ============================================================

where docker >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not installed. Please install Docker Desktop first.
    echo         See DOCKER_SETUP.md for step-by-step instructions.
    pause
    exit /b 1
)

docker info >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker Desktop is not running. Start Docker Desktop and try again.
    pause
    exit /b 1
)

if not exist ".env" (
    if exist ".env.example" (
        copy /Y ".env.example" ".env" >nul
        echo [INFO] Created .env from .env.example
    )
)

set JUPYTER_PORT=8888
set JUPYTER_TOKEN=day6-training
if exist ".env" (
    for /f "usebackq tokens=1,* delims==" %%A in (".env") do (
        set "LINE=%%A"
        if not "!LINE!"=="" if not "!LINE:~0,1!"=="#" (
            set "%%A=%%B"
        )
    )
)

if not exist "..\notebooks" (
    echo [ERROR] Expected ..\notebooks directory next to docker-jupyterlab\.
    pause
    exit /b 1
)

echo [INFO] Building and starting JupyterLab container...
docker compose up -d --build
if errorlevel 1 (
    echo [ERROR] Failed to start Docker Compose stack. Check error messages above.
    pause
    exit /b 1
)

echo.
echo [READY] JupyterLab is starting up!
echo         Open in your browser:
echo         http://localhost:%JUPYTER_PORT%/lab?token=%JUPYTER_TOKEN%
echo.
echo Useful commands:
echo   View logs : docker compose logs -f
echo   Stop lab  : docker compose down
echo ============================================================
pause
