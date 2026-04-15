@echo off
setlocal
cd /d "%~dp0"

echo [1/4] Building GitHub Pages site...
python .\build_static_site.py
if errorlevel 1 (
  echo.
  echo Build failed. Please fix the error above first.
  pause
  exit /b 1
)

git rev-parse --is-inside-work-tree >nul 2>&1
if errorlevel 1 (
  echo.
  echo This folder is not a Git repository yet.
  echo Create an empty GitHub repo first, then run:
  echo   git init
  echo   git branch -M main
  echo   git remote add origin https://github.com/YOUR_NAME/YOUR_REPO.git
  echo After that, run this bat again.
  pause
  exit /b 1
)

git remote get-url origin >nul 2>&1
if errorlevel 1 (
  echo.
  echo Git is ready, but no remote named origin was found.
  echo Run:
  echo   git remote add origin https://github.com/YOUR_NAME/YOUR_REPO.git
  echo Then run this bat again.
  pause
  exit /b 1
)

echo [2/4] Staging site updates...
git add site .github\workflows\deploy-pages.yml README.md

echo [3/4] Creating commit if needed...
git commit -m "Update Curly content site" >nul 2>&1

echo [4/4] Pushing to GitHub...
git push origin HEAD
if errorlevel 1 (
  echo.
  echo Push failed. Check your Git credentials and remote settings.
  pause
  exit /b 1
)

echo.
echo Push finished.
echo If this is the first deployment, GitHub may take a short while to build the Pages site.
echo Your workflow file is already included: .github/workflows/deploy-pages.yml

if "%CI%"=="" pause
