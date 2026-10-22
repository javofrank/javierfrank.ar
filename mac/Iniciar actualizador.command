#!/bin/bash
# Doble clic desde el Finder: se asegura de que el runner de GitHub esté corriendo
# en esta Mac para que la web se actualice sola. Ver RUNNER.md.

RUNNER_DIR="$HOME/actions-runner"

cd "$RUNNER_DIR" 2>/dev/null || {
    echo "No se encontró el actualizador en $RUNNER_DIR."
    echo "Pedile a Jorge que lo instale (ver RUNNER.md)."
    read -r -p "Presioná Enter para cerrar..."
    exit 1
}

./svc.sh start >/dev/null 2>&1

if ./svc.sh status | grep -q "Started"; then
    echo "✅ El actualizador de propiedades está funcionando."
    echo "   Ya podés cerrar esta ventana."
else
    echo "⚠️  El actualizador no pudo arrancar. Avisale a Jorge."
    ./svc.sh status
    read -r -p "Presioná Enter para cerrar..."
fi
