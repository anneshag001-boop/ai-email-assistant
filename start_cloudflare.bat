@echo off
title AI Email Assistant + Cloudflare Tunnel

echo ============================================
echo  AI Email Assistant + Cloudflare Tunnel
echo ============================================
echo.

REM Start the server in the background
echo [1/3] Starting server on http://localhost:8000 ...
start /B /MIN "" ".venv\Scripts\python.exe" -m uvicorn app.main:app --host 0.0.0.0 --port 8000
if %ERRORLEVEL% neq 0 (
    echo [FAILED] Could not start server. Make sure .venv exists.
    pause
    exit /b 1
)
echo [OK] Server started.

REM Wait for server to be ready
timeout /t 4 /nobreak >nul

REM Check if cloudflared is installed
echo [2/3] Checking for cloudflared...
where cloudflared >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [INFO] cloudflared not found. Installing via winget...
    winget install Cloudflare.cloudflared >nul 2>&1
    if %ERRORLEVEL% neq 0 (
        echo [WARNING] Could not install cloudflared automatically.
        echo.
        echo The server is still running at:
        echo   http://localhost:8000
        echo.
        echo To expose it publicly, install cloudflared manually:
        echo   1. Download from: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/
        echo   2. Run: cloudflared tunnel --url http://localhost:8000
        echo.
        pause
        exit /b 1
    )
)
echo [OK] cloudflared found.

REM Start Cloudflare Tunnel
echo [3/3] Starting Cloudflare Tunnel (public URL)...
echo.
echo Public URL will appear below. Share it with anyone.
echo Press CTRL+C to stop everything.
echo.
cloudflared tunnel --url http://localhost:8000

REM Cleanup on exit
echo.
echo Stopping server...
taskkill /f /im python.exe >nul 2>&1
echo Done.
pause
