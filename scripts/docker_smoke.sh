#!/usr/bin/env bash
# Container smoke-test for Anomyze.
#
# Builds the image, starts it with the local HF-cache overlay, waits
# for /health, fires one request per channel, scrapes /metrics, and
# tears the stack down. Intended for a developer laptop, not CI.

set -euo pipefail

cd "$(dirname "$0")/.."

COMPOSE="docker compose -f docker-compose.yml -f docker-compose.local.yml"

echo "==> build"
$COMPOSE build

echo "==> up (detached)"
$COMPOSE up -d

echo "==> wait for /health (up to 6 min)"
ok=0
for i in $(seq 1 72); do
    if curl -fsS -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/api/v1/health 2>/dev/null | grep -q 200; then
        echo "ready after $((i * 5))s"
        ok=1
        break
    fi
    sleep 5
done
if [ "$ok" -ne 1 ]; then
    echo "health-check timeout; container logs:" >&2
    $COMPOSE logs --tail=40 anomyze >&2
    $COMPOSE down
    exit 1
fi

BESCHEID='{"text":"BESCHEID, GZ 2024/4567-III/2. Herr Dr. Maximilian Huber, geboren am 04.03.1978, wohnhaft Kaerntner Strasse 12, 1010 Wien. UID: ATU13585627. Diagnose: F32.1. Kontakt: maximilian.huber@example.at, IBAN AT61 1904 3002 3457 3201.","channel":"CHANNEL","document_id":"docker-smoke-CHANNEL"}'

for channel in govgpt ifg kapa; do
    echo "==> POST /anonymize channel=$channel"
    payload="${BESCHEID//CHANNEL/$channel}"
    curl -fsS -X POST http://127.0.0.1:8000/api/v1/anonymize \
         -H 'content-type: application/json' \
         -d "$payload" | python3 -c "import json,sys; r=json.load(sys.stdin); print(f\"  entity_count={r['entity_count']} text={r['text'][:180]!r}\")"
done

echo "==> metrics"
curl -fsS http://127.0.0.1:8000/metrics \
    | grep -E '^anomyze_(channel_requests_total|model_loaded)' \
    | head -10

echo "==> down"
$COMPOSE down

echo "Docker smoke OK"
