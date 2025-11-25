@echo off
setlocal

REM ----------------------------------------
REM Paths
REM ----------------------------------------
set CHROME_EXE="C:\Program Files\Google\Chrome\Application\chrome.exe"
set PROFILE_DIR="C:\chrome-profile-playwright"
set PY_SCRIPT="G:\Projects\job_app_automation\app.py"



REM ----------------------------------------
REM Start Chrome with CDP enabled
REM ----------------------------------------
echo Starting Chrome with remote debugging...
start "" %CHROME_EXE% ^
    --remote-debugging-port=9222 ^
    --user-data-dir=%PROFILE_DIR% ^
    --no-first-run ^
    --disable-popup-blocking ^
    --disable-default-apps

REM ----------------------------------------
REM Give Chrome time to initialize
REM ----------------------------------------
timeout /t 2 >nul

REM ----------------------------------------
REM Run Python script
REM ----------------------------------------
echo Running Python script...
python %PY_SCRIPT%

echo.
echo Finished.
pause
endlocal
