$ErrorActionPreference = "Stop"

$mirofishRoot = "C:\Users\octav\Desktop\MiroFish"
if (-not (Test-Path $mirofishRoot)) {
    throw "Nu exista folderul MiroFish: $mirofishRoot"
}

Set-Location $mirofishRoot
npm run dev
