@echo off
TITLE AI Test Agent - Frontend
cd /d "%~dp0frontend"
echo ==================================================
echo   Starting Next.js Frontend on http://localhost:3000
echo ==================================================
call npm run dev
pause

