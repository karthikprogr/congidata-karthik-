@echo off
echo ============================================
echo   COGNIDATA - Starting All Services...
echo ============================================

echo.
echo [1/2] Starting Backend (port 8000)...
start "COGNIDATA Backend" cmd /k "cd /d d:\Cognidata_mainfinal-main\cognidata\backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

echo Waiting for backend...
timeout /t 8 /nobreak >nul

echo [2/2] Starting Frontend (port 5173)...
start "COGNIDATA Frontend" cmd /k "cd /d d:\Cognidata_mainfinal-main\cognidata\frontend && npm run dev"

echo Waiting for frontend...
timeout /t 10 /nobreak >nul

:check_backend
curl -s http://localhost:8000/api/health >nul 2>&1
if %errorlevel% neq 0 (
    echo Backend still starting...
    timeout /t 3 /nobreak >nul
    goto check_backend
)
echo [OK] Backend ready

:check_frontend
curl -s http://localhost:5173 >nul 2>&1
if %errorlevel% neq 0 (
    echo Frontend still starting...
    timeout /t 3 /nobreak >nul
    goto check_frontend
)
echo [OK] Frontend ready

echo.
echo ============================================
echo   ALL SERVICES READY
echo ============================================
echo.
echo   OPEN:  http://localhost:5173
echo.
echo   Landing page loads first (same tab).
echo   Click Login to go to the dashboard.
echo.
echo   Login: rudraadmin@gmail.com
echo   Pass:  adminrudra@1234
echo.
timeout /t 2 /nobreak >nul
start http://localhost:5173

pause >nul
