@echo off
setlocal
REM ============================================================
REM  GenPal — start Apache HTTPD serving frontend/public and
REM  reverse-proxying /api to FastAPI on 127.0.0.1:8000.
REM
REM  Apache install dir defaults to %USERPROFILE%\Apache24.
REM  Override by setting APACHE_HOME before running, e.g.:
REM      set APACHE_HOME=C:\Apache24 && deploy\scripts\run_apache.bat
REM ============================================================

if "%APACHE_HOME%"=="" set "APACHE_HOME=%USERPROFILE%\Apache24"
set "HTTPD=%APACHE_HOME%\bin\httpd.exe"

REM Project root = two levels up from this script (deploy\scripts).
set "PROJECT_ROOT=%~dp0..\.."
pushd "%PROJECT_ROOT%"
set "PROJECT_ROOT=%CD%"
popd

if not exist "%HTTPD%" (
    echo [ERROR] httpd.exe not found at "%HTTPD%".
    echo         Set APACHE_HOME to your Apache install dir and retry.
    exit /b 1
)

set "TEMPLATE=%PROJECT_ROOT%\deploy\apache\genpal-runtime.conf.template"
set "CONF=%APACHE_HOME%\conf\genpal-runtime.conf"

REM Substitute placeholders (forward slashes for Apache) via PowerShell.
powershell -NoProfile -Command ^
  "$srv = '%APACHE_HOME%' -replace '\\','/';" ^
  "$gp  = '%PROJECT_ROOT%' -replace '\\','/';" ^
  "(Get-Content -Raw '%TEMPLATE%').Replace('__SRVROOT__', $srv).Replace('__GENPAL_ROOT__', $gp) | Set-Content -Encoding ascii '%CONF%'"
if errorlevel 1 (
    echo [ERROR] Failed to generate runtime config.
    exit /b 1
)

echo Validating config...
"%HTTPD%" -t -f "%CONF%"
if errorlevel 1 (
    echo [ERROR] Apache config test failed.
    exit /b 1
)

echo.
echo Starting Apache on http://localhost:8080
echo   DocumentRoot : %PROJECT_ROOT%\frontend\public
echo   Proxy        : /api  ->  http://127.0.0.1:8000/api
echo   (Start the backend separately: deploy\scripts\run_backend.bat)
echo.
echo Press Ctrl+C to stop.
"%HTTPD%" -f "%CONF%"

endlocal
