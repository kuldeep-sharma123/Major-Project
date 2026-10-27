@echo off
TITLE AI Test Agent - Backend
cd /d "%~dp0backend"
echo ==================================================
echo   Starting FastAPI Backend on http://localhost:8000
echo ==================================================
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
pause

