#!/bin/sh
set -eu

log="${SURICATA_EVE_LOG:-/var/log/suricata/eve.json}"
api_url="${SURICATA_ALERT_API_URL:-}"

while [ ! -f "$log" ]; do
  echo "waiting for $log"
  sleep 1
done

tail -n 0 -F "$log" | while IFS= read -r line; do
  echo "$line" | grep -q '"event_type":"alert"' || continue

  if [ -z "$api_url" ]; then
    echo "SURICATA_ALERT_API_URL is not set; dropping alert"
    continue
  fi

  printf "%s" "$line" | curl -sS -m 5 -X POST "$api_url" \
    -H "Content-Type: application/json" --data-binary @- \
    >/tmp/suricata-forwarder.out 2>&1 || cat /tmp/suricata-forwarder.out
done
