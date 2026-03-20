param(
    [int]$Port = 8501
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot

$appFile = "app.py"
if (-not (Test-Path $appFile)) {
    if (Test-Path "trends.py") {
        $appFile = "trends.py"
    } else {
        throw "Nu gasesc nici app.py, nici trends.py in: $projectRoot"
    }
}

streamlit run $appFile --server.port $Port --server.headless true
