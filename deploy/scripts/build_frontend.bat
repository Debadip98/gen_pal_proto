@echo off
REM ============================================================
REM  GenPal — "build" the static frontend.
REM
REM  The prototype frontend is plain HTML/CSS/JS and needs NO
REM  build step. The browser loads ES modules directly from
REM  frontend/public and frontend/src.
REM
REM  This script simply reports where the servable files live.
REM  It exists so the workflow matches the documented structure
REM  and leaves room for a future bundler in frontend/dist.
REM ============================================================

cd /d "%~dp0..\.."

echo.
echo No build step required for the plain HTML/CSS/JS prototype.
echo Apache should serve this folder directly as DocumentRoot:
echo.
echo     %CD%\frontend\public
echo.
echo If you later add a bundler, emit output to frontend\dist and
echo point Apache DocumentRoot there instead.
echo.

pause
