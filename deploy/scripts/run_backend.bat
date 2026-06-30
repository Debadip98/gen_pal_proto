@echo off
REM ============================================================
REM  GenPal — start FastAPI backend (Uvicorn) on 127.0.0.1:8000
REM ============================================================

REM Move to the project root (two levels up from deploy\scripts).
cd /d "%~dp0..\.."

REM Activate the virtual environment if present.
if exist ".venv\Scripts\activate.bat" (
    call ".venv\Scripts\activate.bat"
)

echo.
echo Starting FastAPI backend on http://127.0.0.1:8000 ...
echo API docs: http://127.0.0.1:8000/docs
echo Health  : http://127.0.0.1:8000/api/v1/health
echo.

python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000

pause
