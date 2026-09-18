#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Automatisation quotidienne complète PMU LONAB
.DESCRIPTION
    Pipeline complet sans intervention humaine :
    1. Scraper : télécharge PDFs (programmes + resultats + ecd)
    2. Parse : parse tous les PDFs bruts -> JSON structurés
    3. Load : charge JSON dans la base socle SQLite
    4. Master DB : reconstruit la base maître (identifiants UUIDv5)
    5. Site : génère le dashboard HTML statique
    6. Sync API : synchronise l'API PMU (7 derniers jours)
.NOTES
    Exécution quotidienne à 06h00 via Planificateur de tâches
    Durée estimée : 20-30 minutes
#>

param(
    [switch]$ForceRebuild
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$LogFile = Join-Path $ScriptDir "logs\auto_update_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"

# Création dossier logs
New-Item -ItemType Directory -Force -Path (Join-Path $ScriptDir "logs") | Out-Null

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $line = "[$timestamp] [$Level] $Message"
    Write-Host $line
    Add-Content -Path $LogFile -Value $line
}

function Run-Command {
    param([string]$Name, [string]$Command, [string]$WorkDir = $ScriptDir, [int]$TimeoutSec = 900)
    Write-Log ">>> $Name : $Command"
    try {
        $job = Start-Job -ScriptBlock {
            param($Cmd, $Dir)
            cd $Dir
            Invoke-Expression $Cmd
        } -ArgumentList $Command, $WorkDir
        
        $completed = Wait-Job -Job $job -Timeout $TimeoutSec
        $result = Receive-Job -Job $job
        $exitCode = $job.ChildJobs[0].ExitCode
        Remove-Job -Job $job -Force
        
        if ($completed) {
            if ($exitCode -eq 0) {
                Write-Log "[OK] $Name termine (code $exitCode)"
            } else {
                Write-Log "[ERREUR] $Name ECHEC (code $exitCode)" "ERROR"
                Write-Log $result "ERROR"
            }
        } else {
            Write-Log "[TIMEOUT] $Name depasse $TimeoutSec sec" "ERROR"
            $exitCode = -1
        }
        return $exitCode
    } catch {
        Write-Log "[EXCEPTION] $Name : $($_.Exception.Message)" "ERROR"
        return 1
    }
}

Write-Log "========== DEBUT PIPELINE QUOTIDIEN PMU LONAB =========="

# 1. Scraper LONAB - toutes les sources
Write-Log "--- ETAPE 1/6 : Scraper LONAB (programmes + resultats + ecd) ---"
$scraperDir = Join-Path $ScriptDir "pmu-lonab-scraper"
if (Test-Path $scraperDir) {
    Run-Command "Scraper LONAB (all)" "python main.py --download --source all" $scraperDir 900
} else {
    Write-Log "Dossier scraper introuvable : $scraperDir" "WARN"
}

# 2. Parser tous les PDFs bruts
Write-Log "--- ETAPE 2/6 : Parsing PDFs (tous types) ---"
Run-Command "Parse All Raw" "python parse_all_raw.py" $ScriptDir 1200

# 3. Charger JSON parsés dans la base socle
Write-Log "--- ETAPE 3/6 : Chargement JSON -> Base Socle ---"
Run-Command "Load to Socle DB" "python load_parsed_to_socle.py" $ScriptDir 300

# 4. Construire la Master DB (identifiants UUIDv5)
Write-Log "--- ETAPE 4/6 : Construction Master DB ---"
Run-Command "Build Master DB" "python scripts/phase2/build_master_db.py" $ScriptDir 300

# 5. Générer le dashboard HTML
Write-Log "--- ETAPE 5/6 : Generation Dashboard HTML ---"
Run-Command "Build Dashboard" "python scripts/phase8/build_site.py" $ScriptDir 120

# 6. Sync API PMU (7 derniers jours)
Write-Log "--- ETAPE 6/6 : Sync API PMU ---"
Run-Command "Sync API PMU" "python sync_pmu_final.py" $ScriptDir 600

Write-Log "========== FIN PIPELINE QUOTIDIEN PMU LONAB =========="
Write-Log ("Log complet : " + $LogFile)