@echo off
REM Automatically set the path to the Python executable
set PYTHON_EXECUTABLE="C:\Program Files\Python312\python.exe"

REM Automatically set the path to the updater script
set UPDATER_SCRIPT=%~dp0updater.py

:loop
REM Run updater.py
%PYTHON_EXECUTABLE% %UPDATER_SCRIPT%

REM Check the exit code
if %ERRORLEVEL% == 100 (
    echo Restarting updater.py...
    goto loop
)

echo Exiting. No restart needed.
pause
