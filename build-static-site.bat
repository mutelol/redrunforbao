@echo off
setlocal

cd /d "%~dp0"
echo [Curly Site] Building static site...
echo.

python "%~dp0build_static_site.py"

echo.
if errorlevel 1 (
  echo [Curly Site] Build failed. Check the error output above.
) else (
  echo [Curly Site] Build completed.
)

echo.
if "%CI%"=="" pause
