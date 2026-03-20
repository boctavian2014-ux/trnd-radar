param(
    [string[]]$TaskNames = @("SocialTrendsDashboard", "MiroFishDev")
)

$ErrorActionPreference = "Continue"

foreach ($task in $TaskNames) {
    try {
        $taskInfo = Get-ScheduledTask -TaskName $task -ErrorAction Stop
        $taskState = $taskInfo.State
        $taskData = Get-ScheduledTaskInfo -TaskName $task -ErrorAction Stop

        Write-Host "========================================"
        Write-Host "Task: $task"
        Write-Host "State: $taskState"
        Write-Host "Last Run Time: $($taskData.LastRunTime)"
        Write-Host "Last Task Result: $($taskData.LastTaskResult)"
        Write-Host "Next Run Time: $($taskData.NextRunTime)"
    } catch {
        Write-Warning "Task inexistent sau inaccesibil: $task"
    }
}
