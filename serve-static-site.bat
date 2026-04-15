@echo off
setlocal

cd /d "%~dp0"
echo [Curly Site] Serving project root on http://0.0.0.0:8000/site/
echo [Curly Site] Open this on your phone while connected to the same Wi-Fi:
echo [Curly Site] http://YOUR-PC-IP:8000/site/
echo.

python -m http.server 8000
