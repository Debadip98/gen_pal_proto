@echo off
REM ============================================================
REM  GenPal — run the full local demo (API + frontend) on one URL.
REM  Open http://127.0.0.1:8000 after it starts.
REM ============================================================

cd /d "%~dp0.."

if exist ".venv\Scripts\activate.bat" (
    call ".venv\Scripts\activate.bat"
)

echo.
echo Starting GenPal on http://127.0.0.1:8000
echo   App     : http://127.0.0.1:8000
echo   Health  : http://127.0.0.1:8000/api/v1/health
echo   API docs: http://127.0.0.1:8000/docs
echo.
echo Press Ctrl+C to stop.

python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000

pause
