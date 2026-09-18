# Script de démarrage combiné FasoTurf (API FastAPI + Frontend Vite)
Write-Host "==========================================" -ForegroundColor Green
Write-Host "   Démarrage de la plateforme FasoTurf    " -ForegroundColor Yellow
Write-Host "==========================================" -ForegroundColor Green

# 1. Démarrage de l'API FastAPI en arrière-plan
Write-Host "[1/2] Lancement du Backend FastAPI sur http://127.0.0.1:8000..." -ForegroundColor Cyan
$apiProcess = Start-Process python -ArgumentList "-m uvicorn backend.main:app --host 127.0.0.1 --port 8000" -PassThru

Start-Sleep -Seconds 2

# 2. Démarrage du Frontend Vite
Write-Host "[2/2] Lancement de l'interface FasoTurf sur http://localhost:5173..." -ForegroundColor Cyan
Set-Location -Path "fasoturf"
npm run dev

# Nettoyage à la fermeture
if ($apiProcess) {
    Stop-Process -Id $apiProcess.Id -Force -ErrorAction SilentlyContinue
}
