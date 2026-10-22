#!/bin/bash
# Doble clic desde el Finder: abre la página del workflow en GitHub para lanzar
# una actualización en el momento con el botón "Run workflow".

"$(dirname "$0")/Iniciar actualizador.command" >/dev/null 2>&1
open "https://github.com/javofrank/javierfrank.ar/actions/workflows/scrape.yml"
