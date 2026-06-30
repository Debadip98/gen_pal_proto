@echo off
REM ============================================================
REM  GenPal — copy the static frontend into an Apache htdocs dir.
REM
REM  OPTION A (recommended): point Apache DocumentRoot directly
REM  at frontend\public (see deploy\apache\genpal-httpd.conf).
REM  In that case you do NOT need this script.
REM
REM  OPTION B: copy the files into Apache's own htdocs folder.
REM  Use this when you cannot change DocumentRoot. Edit the
REM  APACHE_DOCROOT path below to match your Apache install.
REM ============================================================

cd /d "%~dp0..\.."

set "SOURCE=%CD%\frontend\public"
set "APACHE_DOCROOT=C:\Apache24\htdocs\genpal"

echo.
echo Copying frontend from:
echo     %SOURCE%
echo to:
echo     %APACHE_DOCROOT%
echo.

if not exist "%APACHE_DOCROOT%" mkdir "%APACHE_DOCROOT%"

xcopy "%SOURCE%\*" "%APACHE_DOCROOT%\" /E /I /Y

echo.
echo Done. If using Option B, set DocumentRoot to "%APACHE_DOCROOT%"
echo and browse to http://localhost:8080
echo.

pause
