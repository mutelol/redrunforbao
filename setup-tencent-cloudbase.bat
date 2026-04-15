@echo off
setlocal
cd /d "%~dp0"

echo This script prepares Tencent CloudBase CLI on this computer.
echo It will not ask you to share your Tencent Cloud account with anyone.
echo Login happens through Tencent's own QR-code flow in your browser.
echo.

node --version >nul 2>&1
if errorlevel 1 (
  echo Node.js was not found. Please install Node.js first, then run this script again.
  pause
  exit /b 1
)

npm --version >nul 2>&1
if errorlevel 1 (
  echo npm was not found. Please reinstall Node.js with npm enabled.
  pause
  exit /b 1
)

where cloudbase >nul 2>&1
if errorlevel 1 (
  echo CloudBase CLI was not found. Installing with a mainland-friendly npm mirror...
  npm install -g @cloudbase/cli --registry=https://registry.npmmirror.com
  if errorlevel 1 (
    echo.
    echo Install failed. Try running this bat as Administrator, or run:
    echo   npm install -g @cloudbase/cli --registry=https://registry.npmmirror.com
    pause
    exit /b 1
  )
) else (
  echo CloudBase CLI is already installed.
)

echo.
echo CloudBase CLI version:
cloudbase --version

echo.
echo Starting CloudBase login. Follow the QR-code / browser prompt from Tencent Cloud.
cloudbase login
if errorlevel 1 (
  echo.
  echo Login did not finish successfully. You can rerun this script later.
  pause
  exit /b 1
)

echo.
echo Setup finished. Next, run deploy-tencent-cloudbase.bat to upload the site.
if "%CI%"=="" pause
