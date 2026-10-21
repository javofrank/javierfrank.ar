# Corre el scraper desde esta PC y publica docs/data/propiedades.json.
# Uso: .\scrape-local.ps1            (scrapea, commitea y pushea)
#      .\scrape-local.ps1 -NoPush    (solo scrapea, sin commit ni push)
param([switch]$NoPush)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

# Crear el entorno virtual la primera vez
$python = ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    Write-Host "Creando entorno virtual..."
    python -m venv .venv
    & $python -m pip install -q -r requirements.txt
}

# Traer lo último antes de generar el JSON
if (-not $NoPush) {
    git pull --rebase origin main
    if ($LASTEXITCODE -ne 0) { throw "git pull falló" }
}

$env:PYTHONIOENCODING = "utf-8"
& $python actionscraping.py
if ($LASTEXITCODE -ne 0) { throw "El scraper falló" }

if ($NoPush) { exit 0 }

git add docs/data/propiedades.json
git diff --staged --quiet
if ($LASTEXITCODE -eq 0) {
    Write-Host "Sin cambios en propiedades.json, nada que publicar."
    exit 0
}

git commit -m "Update propiedades.json (local)"
git push origin HEAD:main
if ($LASTEXITCODE -ne 0) { throw "git push falló" }
Write-Host "propiedades.json publicado."
