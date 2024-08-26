@echo off

:: Check if running with administrative privileges
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Requesting elevation...
    powershell -Command "Start-Process cmd -ArgumentList '/c cd /d %CD% && %~s0' -Verb RunAs"
    exit /b
)

:: Commands to run with elevated privileges
echo Running as Administrator...
netsh winhttp set proxy proxy-server="http=example:example"
py main.py

pause
