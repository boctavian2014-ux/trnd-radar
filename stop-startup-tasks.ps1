param(
    [string[]]$TaskNames = @("SocialTrendsDashboard", "MiroFishDev")
)

$ErrorActionPreference = "Continue"

foreach ($task in $TaskNames) {
    try {
        Stop-ScheduledTask -TaskName $task -ErrorAction Stop
        Write-Host "Stopped: $task"
    } catch {
        Write-Warning "Nu am putut opri task-ul $task (poate nu ruleaza): $($_.Exception.Message)"
    }
}
