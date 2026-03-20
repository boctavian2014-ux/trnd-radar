param(
    [string[]]$TaskNames = @("SocialTrendsDashboard", "MiroFishDev")
)

$ErrorActionPreference = "Continue"

foreach ($task in $TaskNames) {
    try {
        Start-ScheduledTask -TaskName $task -ErrorAction Stop
        Write-Host "Started: $task"
    } catch {
        Write-Warning "Nu am putut porni task-ul $task: $($_.Exception.Message)"
    }
}
