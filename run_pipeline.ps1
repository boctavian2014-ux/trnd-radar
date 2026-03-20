param(
    [ValidateSet("exports", "dashboard", "both")]
    [string]$OutputTarget = "exports",
    [int]$DashboardPort = 8501,
    [switch]$SkipPipeline,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonExe = (Get-Command python -ErrorAction Stop).Source

$clusterScript = Join-Path $projectRoot "src/topics/cluster_topics.py"
$scoreScript = Join-Path $projectRoot "src/influencers/influencer_scores.py"
$dashboardScript = Join-Path $projectRoot "src/dashboards/influencers_app.py"

function Invoke-Step {
    param(
        [string]$Name,
        [string]$FilePath
    )

    if (-not (Test-Path $FilePath)) {
        throw "Lipseste scriptul pentru pasul '$Name': $FilePath"
    }

    Write-Host "[$Name] Rulez: $FilePath"
    if ($DryRun) {
        return
    }

    & $pythonExe $FilePath
    if ($LASTEXITCODE -ne 0) {
        throw "Pasul '$Name' a esuat cu codul $LASTEXITCODE."
    }
}

Write-Host "Pipeline social-radar pornit."
Write-Host "OutputTarget: $OutputTarget | DashboardPort: $DashboardPort"

if (-not $SkipPipeline) {
    Invoke-Step -Name "Clustering" -FilePath $clusterScript
    Invoke-Step -Name "Scoring influenceri" -FilePath $scoreScript
} else {
    Write-Host "Pipeline ETL a fost sarit (-SkipPipeline)."
}

if ($OutputTarget -in @("dashboard", "both")) {
    if (-not (Test-Path $dashboardScript)) {
        throw "Lipseste dashboard script: $dashboardScript"
    }

    $streamlitCmd = "streamlit run `"$dashboardScript`" --server.port $DashboardPort"
    Write-Host "[Dashboard] Rulez: $streamlitCmd"
    if (-not $DryRun) {
        & streamlit run $dashboardScript --server.port $DashboardPort
    }
} else {
    Write-Host "Exporturi generate. Dashboard nepornit (OutputTarget=exports)."
}
