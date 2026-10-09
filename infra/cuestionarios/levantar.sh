#!/usr/bin/env bash
# Levanta N8N + el stack de cuestionarios e importa/publica el flujo "Procesar
# cuestionario" si todavía no está. Se puede correr las veces que haga falta.
set -e
cd "$(dirname "$0")"

echo "[1/3] N8N (infra/n8n)..."
(cd ../n8n && docker compose up -d)
for i in $(seq 1 30); do
  curl -sf -o /dev/null http://localhost:5678/healthz && break
  sleep 2
  [ "$i" -eq 30 ] && { echo "N8N no responde: mirá 'docker compose logs' en infra/n8n/."; exit 1; }
done

echo "[2/3] Flujo 'Procesar cuestionario'..."
if (cd ../n8n && docker compose exec -T n8n n8n list:workflow 2>/dev/null) | grep -q "Procesar cuestionario"; then
  echo "      ya estaba importado."
else
  (cd ../n8n && docker compose exec -T n8n n8n import:workflow \
      --input=/home/node/data/sistema-eidas/infra/cuestionarios/workflows/procesar-cuestionario.json \
    && docker compose exec -T n8n n8n publish:workflow --id=CuestMail0000001 \
    && docker compose restart n8n)
  for i in $(seq 1 30); do
    curl -sf -o /dev/null http://localhost:5678/healthz && break
    sleep 2
  done
  echo "      importado y publicado."
fi

echo "[3/3] API + dashboard..."
docker compose up -d
for i in $(seq 1 30); do
  curl -sf -o /dev/null http://127.0.0.1:8430/api/cuestionarios && break
  sleep 1
done
echo ""
echo "Listo: http://localhost:8430"
echo "Para apagar: docker compose down (acá y en infra/n8n)."
