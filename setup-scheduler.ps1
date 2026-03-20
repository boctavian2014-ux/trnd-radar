param(
    [string]$TaskName = "SocialTrendsDaily",
    [int]$Hour = 8,
    [int]$Minute = 0,
    [switch]$RunNow
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonExe = (Get-Command python -ErrorAction Stop).Source
$scriptPath = Join-Path $projectRoot "collect_trends.py"

if (-not (Test-Path $scriptPath)) {
    throw "Nu exista scriptul: $scriptPath"
}

$triggerBase = Get-Date -Hour $Hour -Minute $Minute -Second 0
if ($triggerBase -le (Get-Date)) {
    $triggerBase = $triggerBase.AddDays(1)
}

$action = New-ScheduledTaskAction -Execute $pythonExe -Argument "`"$scriptPath`"" -WorkingDirectory $projectRoot
$trigger = New-ScheduledTaskTrigger -Daily -At $triggerBase
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Description "Daily social trends collector (Twitter Romania + Reddit)." `
    -Force | Out-Null

Write-Host "Task creat/actualizat: $TaskName"
Write-Host "Programat zilnic la $($Hour.ToString('00')):$($Minute.ToString('00')) (ora locala Windows)."
Write-Host "Script rulat: $scriptPath"

if ($RunNow) {
    Start-ScheduledTask -TaskName $TaskName
    Write-Host "Task pornit manual acum."
}
