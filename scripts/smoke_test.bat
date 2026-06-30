@echo off
REM ============================================================
REM  GenPal — quick smoke test against a running local server.
REM  Start the server first: scripts\run_local.bat
REM ============================================================

echo [1/2] Health check  ->  http://127.0.0.1:8000/api/v1/health
curl -s http://127.0.0.1:8000/api/v1/health
echo.
echo.
echo [2/2] Frontend root ->  http://127.0.0.1:8000/
curl -s -o nul -w "HTTP %%{http_code}  (expect 200)\n" http://127.0.0.1:8000/
echo.

pause
