@echo off
setlocal

cd /d "%~dp0"
echo [Curly Agent] Starting content generation...
echo.

python "%~dp0run_curly_agent.py"

echo.
if errorlevel 1 (
  echo [Curly Agent] Run failed. Check the error output above.
) else (
  echo [Curly Agent] Run completed.
)

echo.
if "%CI%"=="" pause
