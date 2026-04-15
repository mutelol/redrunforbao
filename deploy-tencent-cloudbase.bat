@echo off
setlocal
cd /d "%~dp0"

where cloudbase >nul 2>&1
if errorlevel 1 (
  echo CloudBase CLI was not found.
  echo Please run setup-tencent-cloudbase.bat first.
  pause
  exit /b 1
)

echo [1/3] Building static site from local runs...
python .\build_static_site.py
if errorlevel 1 (
  echo.
  echo Site build failed. Please fix the error above first.
  pause
  exit /b 1
)

set ENV_FILE=.cloudbase-env
set ENV_ID=
if exist "%ENV_FILE%" (
  set /p ENV_ID=<"%ENV_FILE%"
)

if "%ENV_ID%"=="" (
  echo.
  echo Please enter your Tencent CloudBase environment ID.
  echo You can find it in Tencent CloudBase Console, usually like: xxx-123456
  set /p ENV_ID=CloudBase env ID:
  if "%ENV_ID%"=="" (
    echo No environment ID was provided.
    pause
    exit /b 1
  )
  >"%ENV_FILE%" echo %ENV_ID%
)

echo.
echo [2/3] Deploying site/ to Tencent CloudBase static hosting...
pushd site
cloudbase hosting deploy . -e "%ENV_ID%"
set DEPLOY_EXIT=%ERRORLEVEL%
popd

if not "%DEPLOY_EXIT%"=="0" (
  echo.
  echo Deploy failed. If you have not logged in yet, run setup-tencent-cloudbase.bat first.
  pause
  exit /b %DEPLOY_EXIT%
)

echo.
echo [3/3] Fetching hosting detail...
cloudbase hosting detail -e "%ENV_ID%"

echo.
echo Deploy finished. Copy the hosting domain above and open it on your phone.
if "%CI%"=="" pause
