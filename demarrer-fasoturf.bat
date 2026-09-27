@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ============================================================
echo   FasoTurf - demarrage de l'application
echo ============================================================
echo.

set "PY=C:\Users\Lenovo\.workbuddy-ai\binaries\python\versions\3.13.12\python.exe"
if not exist "%PY%" set "PY=python"

if not exist "dist\index.html" (
    echo Interface non compilee : compilation en cours...
    call npm run build
    if errorlevel 1 (
        echo.
        echo ECHEC de la compilation. Verifiez que Node.js est installe.
        pause
        exit /b 1
    )
)

echo Ouverture de http://127.0.0.1:8000 dans le navigateur...
start "" "http://127.0.0.1:8000"

echo.
echo Serveur en cours d'execution. Fermez cette fenetre pour l'arreter.
echo.
"%PY%" -m uvicorn backend.main:app --host 127.0.0.1 --port 8000

echo.
echo Serveur arrete.
pause
