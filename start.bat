@echo off
TITLE AI Autonomous Testing Agent
echo ========================================================
echo     Launching AI Autonomous Testing Agent
echo ========================================================
echo.
echo 1. Launching Backend on http://localhost:8000 ...
start "AI Test Agent - Backend" "%~dp0start_backend.bat"

timeout /t 4 /nobreak >nul

echo 2. Launching Frontend on http://localhost:3000 ...
start "AI Test Agent - Frontend" "%~dp0start_frontend.bat"

timeout /t 3 /nobreak >nul

echo 3. Opening Dashboard in your browser ...
start http://localhost:3000

echo.
echo ========================================================
echo Backend API:  http://localhost:8000
echo Swagger Docs: http://localhost:8000/api/docs
echo Frontend UI:  http://localhost:3000
echo ========================================================
echo Both servers have been launched! Press any key to exit this launcher window.
pause >nul
