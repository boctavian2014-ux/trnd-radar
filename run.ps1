param(
    [int]$Port = 8501
)

$ErrorActionPreference = "Stop"

$appFile = "app.py"
if (-not (Test-Path $appFile)) {
    if (Test-Path "trends.py") {
        $appFile = "trends.py"
    } else {
        Write-Error "Nu gasesc nici app.py, nici trends.py in folderul curent."
        exit 1
    }
}

Write-Host "Pornesc Streamlit: $appFile pe portul $Port..."
streamlit run $appFile --server.port $Port

# Scheduler quick setup:
# .\setup-scheduler.ps1
# .\setup-scheduler.ps1 -TaskName "SocialTrendsDaily" -Hour 8 -Minute 0 -RunNow
