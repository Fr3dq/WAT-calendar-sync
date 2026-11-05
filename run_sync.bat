@echo off
rem Runs the WAT plan sync once and appends its output to sync.log.
rem Used by the daily Windows scheduled task "WAT calendar sync".
cd /d "%~dp0"
set PYTHONUTF8=1
echo ===== %date% %time% ===== >> sync.log
".venv\Scripts\python.exe" wat_plan.py >> sync.log 2>&1
echo Exit code: %errorlevel% >> sync.log
