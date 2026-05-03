#!/bin/sh
# Entrypoint für Stream-Container: Erstellt .streamlinkrc und startet Controller

set -e

# OAuth-Token aus Umgebungsvariable
if [ -n "$TWITCH_OAUTH_TOKEN" ]; then
    echo "Erstelle .streamlinkrc mit OAuth-Token..."
    mkdir -p /root
    echo "twitch-oauth-token=${TWITCH_OAUTH_TOKEN}" > /root/.streamlinkrc
    chmod 600 /root/.streamlinkrc
else
    echo "WARNUNG: Kein TWITCH_OAUTH_TOKEN gesetzt, Stream läuft anonym."
fi

# Controller-Typ auswählen
if [ "$CONTROLLER_TYPE" = "cq" ]; then
    echo "Starte CQ-Controller (Custom Quality)..."
    python /app/stream_controller_cq.py
else
    echo "Starte Standard-Controller (Low-Latency)..."
    python /app/stream_controller.py
fi
