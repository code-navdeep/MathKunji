@echo off
setlocal

:: MathKunji - One-click launcher for Windows
:: Double-click this file to build and run MathKunji

:: Change to the directory where this script is located
cd /d "%~dp0"

echo ========================================
echo    MathKunji - Mathematical Solver
echo ========================================
echo.

:: Check if Docker is running
docker info > nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker is not running.
    echo.
    echo Please start Docker Desktop and try again.
    echo.
    pause
    exit /b 1
)

echo Docker is running. Building and starting MathKunji via Compose...
echo.

:: Build and start via Docker Compose
:: (uses docker-compose.yml; groups the container under the project in Docker Desktop,
:: same as the macOS launcher, so both platforms produce the same container name/lifecycle)
docker compose up -d --build
if errorlevel 1 (
    echo.
    echo ERROR: Build/start failed. Please check the error messages above.
    echo.
    pause
    exit /b 1
)

echo.
echo MathKunji is starting.
echo.

:: Wait until the app actually answers before opening the browser.
:: "docker compose up -d" returns once the CONTAINER has started, not once
:: Gradio is listening -- it still has to import gradio, sympy and matplotlib
:: and bind the port. A fixed short wait reliably opened the browser on a
:: connection-refused page and left the user to refresh by hand.
::
:: curl.exe only ships with Windows 10 1803 and later. Without this check a
:: missing curl would fail every iteration and turn the poll into a full
:: 60-second stall, which is worse than the problem being fixed.
where curl >nul 2>&1
if errorlevel 1 (
    echo curl not available - waiting 15 seconds instead...
    timeout /t 15 /nobreak > nul
    goto ready
)

set /a tries=0
:waitloop
set /a tries+=1
curl -s -o NUL http://localhost:7860 >nul 2>&1
if not errorlevel 1 goto ready
if %tries% geq 60 goto ready
timeout /t 1 /nobreak > nul
goto waitloop
:ready

:: Open browser
echo.
echo Opening browser...
start http://localhost:7860

echo.
echo ========================================
echo    MathKunji is now running!
echo ========================================
echo.
echo Access the app at: http://localhost:7860
echo.
echo To stop the app, use Docker Desktop or run:
echo   docker compose down
echo.
pause
