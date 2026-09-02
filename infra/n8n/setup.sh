#!/usr/bin/env bash
# Deja N8N corriendo y configurado desde cero en una máquina nueva: symlinks a los
# secretos (sincronizados vía sistema-eidas-datos), levanta el contenedor, e importa
# el workflow "Evaluacion EIDAS" y las credenciales de Gmail/Drive por CLI.
# Ver CLAUDE.md → "Bug real: devolución sin publicar..." para el porqué de este script.
set -e
cd "$(dirname "$0")"

DATOS_DIR="../../../sistema-eidas-datos/n8n"

if [ ! -f "$DATOS_DIR/.env" ]; then
  echo "No encuentro $DATOS_DIR/.env — ¿está clonado sistema-eidas-datos al lado de"
  echo "sistema-eidas/? (git clone git@github.com:pablopedernera0/sistema-eidas-datos.git"
  echo "en .../terciario-urquiza/)"
  exit 1
fi

for f in .env google-oauth-client.json; do
  if [ ! -e "$f" ]; then
    ln -s "$DATOS_DIR/$f" "$f"
    echo "Symlink creado: $f -> $DATOS_DIR/$f"
  fi
done

echo "Levantando N8N..."
docker compose up -d

echo -n "Esperando a que N8N responda"
for i in $(seq 1 30); do
  if curl -sf -o /dev/null http://localhost:5678/healthz; then
    echo " listo."
    break
  fi
  echo -n "."
  sleep 2
  if [ "$i" -eq 30 ]; then
    echo " nunca respondió — mirá 'docker compose logs' en infra/n8n/."
    exit 1
  fi
done

WORKFLOW_YA_ESTA=$(docker compose exec n8n n8n list:workflow 2>/dev/null | grep -c "Evaluacion EIDAS" || true)
if [ "$WORKFLOW_YA_ESTA" -gt 0 ]; then
  echo "El workflow 'Evaluacion EIDAS' ya está importado — no lo toco (re-importarlo lo"
  echo "desactivaría: esta versión de N8N no soporta activar por CLI fuera de modo queue)."
else
  echo "Importando workflow (Evaluacion EIDAS)..."
  docker compose exec n8n n8n import:workflow \
    --input=/home/node/data/infra/n8n/workflows/evaluacion-eidas.json
  echo "Importado, pero queda INACTIVO — esta versión de N8N no soporta activar workflows"
  echo "por CLI en modo standalone. Único paso manual que queda: abrí"
  echo "http://localhost:5678, entrá a 'Evaluacion EIDAS' y prendé el toggle 'Active'."
fi

CREDENCIALES_YA_ESTAN=$(docker compose exec n8n n8n export:credentials --all 2>/dev/null | grep -c "Gmail account" || true)
if [ "$CREDENCIALES_YA_ESTAN" -gt 0 ]; then
  echo "Las credenciales de Gmail/Drive ya estaban importadas — no las toco."
else
  echo "Importando credenciales de Gmail/Drive..."
  docker compose cp "$DATOS_DIR/credentials.json" n8n:/tmp/credentials-import.json
  docker compose exec n8n n8n import:credentials --input=/tmp/credentials-import.json
  docker compose exec n8n rm -f /tmp/credentials-import.json
fi

echo ""
echo "Listo. N8N corriendo en http://localhost:5678."
