#!/bin/bash
# Corre el scraper desde una Mac y publica docs/data/propiedades.json.
# Uso: ./scrape-local.sh             (scrapea, commitea y pushea)
#      ./scrape-local.sh --no-push   (solo scrapea, sin commit ni push)
#
# Para cronearlo (todos los días a las 8:00), agregar con `crontab -e`:
#   0 8 * * * /ruta/al/repo/javierfrank.ar/scrape-local.sh >> /ruta/al/repo/javierfrank.ar/scrape.log 2>&1
#
# Requisitos: Google Chrome instalado, python3, y git autenticado sin prompts
# (clave SSH o el helper osxkeychain), porque cron no puede pedir credenciales.

set -euo pipefail

# cron arranca con un PATH mínimo: sumar Homebrew y las rutas habituales
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:$PATH"
export PYTHONIOENCODING=utf-8

cd "$(dirname "$0")"
echo "=== $(date '+%Y-%m-%d %H:%M:%S') ==="

no_push=false
if [[ "${1:-}" == "--no-push" ]]; then
    no_push=true
fi

# Crear el entorno virtual la primera vez
python=".venv/bin/python"
if [[ ! -x "$python" ]]; then
    echo "Creando entorno virtual..."
    python3 -m venv .venv
    "$python" -m pip install -q -r requirements.txt
fi

# Traer lo último antes de generar el JSON
if ! $no_push; then
    git pull --rebase origin main
fi

"$python" actionscraping.py

if $no_push; then
    exit 0
fi

git add docs/data/propiedades.json
if git diff --staged --quiet; then
    echo "Sin cambios en propiedades.json, nada que publicar."
    exit 0
fi

git commit -m "Update propiedades.json (local)"
git push origin HEAD:main
echo "propiedades.json publicado."
