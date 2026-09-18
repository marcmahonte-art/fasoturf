#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Installe la tache planifiee Windows pour l'automatisation quotidienne PMU
.DESCRIPTION
    Cree une tache "PMU_Auto_Update" qui s'execute tous les jours a 06h00.
    Executer en tant qu'Administrateur.
#>

# Necessite droits admin
if (-NOT ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Error "Ce script doit etre execute en tant qu'Administrateur (clic droit > Executer en tant qu'administrateur)"
    exit 1
}

$ScriptPath = "C:\Users\Lenovo\Desktop\PMU\auto_update.ps1"
$TaskName = "PMU_Auto_Update"
$RunTime = "06:00"

if (-not (Test-Path $ScriptPath)) {
    Write-Error "Script introuvable : $ScriptPath"
    exit 1
}

# Supprimer l'ancienne tache si existe
if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
    Write-Host "Suppression de l'ancienne tache..."
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

$Action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$ScriptPath`""

$Trigger = New-ScheduledTaskTrigger -Daily -At $RunTime

$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Hours 2)

$Principal = New-ScheduledTaskPrincipal -UserId (Get-CimInstance Win32_ComputerSystem).UserName -LogonType Interactive -RunLevel Highest

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $Action `
    -Trigger $Trigger `
    -Settings $Settings `
    -Principal $Principal `
    -Description "Mise a jour quotidienne PMU LONAB : Scraper + Sync API + Dashboard" `
    -Force

Write-Host "OK Tache '$TaskName' creee avec succes"
Write-Host "  Execution : Tous les jours a $RunTime"
Write-Host "  Script : $ScriptPath"
Write-Host ""
Write-Host "Pour tester maintenant :"
Write-Host "  Start-ScheduledTask -TaskName '$TaskName'"
Write-Host ""
Write-Host "Pour voir les logs :"
Write-Host "  Get-Content C:\Users\Lenovo\Desktop\PMU\logs\auto_update_*.log -Tail 50"