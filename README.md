# Twitch Stream Manager

Twitch-Streams auf Apple TV, VLC & Co. – ohne Zusatz-Apps.

## Was macht das?

Läuft auf deinem Server und macht Twitch-Streams zu normalen HTTP-URLs. Die URL einfach in VLC, Apple TV oder einen anderen Player eintragen – fertig.

**Neu:** Direkter Apple TV Start per Knopfdruck aus dem Manager.

## Schnellstart

### Docker (empfohlen)

```yaml
version: "3.8"
services:
  twitch-manager:
    image: ghcr.io/gedankenstrom/twitch-manager:latest
    container_name: twitch_manager
    restart: unless-stopped
    ports:
      - "5000:5000"
    environment:
      - HOST_IP=auto
    volumes:
      - twitch-data:/data
      - /var/run/docker.sock:/var/run/docker.sock:ro
volumes:
  twitch-data:
```

### Lokal (Entwicklung)

```bash
# Python 3 + venv
python3 -m venv venv
source venv/bin/activate
pip install streamlink flask docker

# Starten
cd /pfad/zu/twitch-github
DATA_DIR=/tmp/twitch-data python3 src/manager/manager.py
```

### Browser öffnen

`http://dein-server:5000`

### Stream starten

1. Kanal eingeben (z.B. `kanal`)
2. Port: 🎲 Automatisch oder manuell wählen
3. Modus: 🚀 Standard oder 🎛️ CQ
4. Stream starten
5. 🍎 TV Button klicken → Stream auf Apple TV

Fertig.

## Features

| Feature | Beschreibung |
|---------|-------------|
| 📺 Multi-Player | Apple TV, VLC, Kodi – alles was HTTP kann |
| 🍎 Apple TV Direktstart | Per Knopfdruck in VLC auf Apple TV starten |
| 🔗 Home Assistant Webhook | VLC stoppen bevor neuer Stream startet |
| 🔴 LIVE-Status | Sieht sofort ob der Kanal online ist |
| 💬 Chat | Direkt im Browser öffnen |
| 🎛️ Zwei Modi | Standard (low latency) oder CQ (stabil) |
| 🎲 Auto-Port | Ersten freien Port automatisch wählen |
| 📱 Responsive | Funktioniert auch am Handy |

## Apple TV Einrichtung

### 1. VLC auf Apple TV vorbereiten

1. VLC-App installieren (App Store)
2. Einstellungen → **Remote Playback** aktivieren
3. IP notieren (z.B. `192.168.25.20`)

### 2. Manager konfigurieren

1. Auf ☰ (Menü) klicken
2. 🍎 **Apple TV** auswählen
3. Einstellungen vornehmen:
   - **IP-Adresse** des Apple TV
   - **Webhook URL** (optional, für Home Assistant)
   - **Verzögerung** in Sekunden (nach Webhook, bevor Stream startet)
4. Speichern

### 3. Stream senden

- Stream starten
- Auf 🍎 **TV** Button klicken
- Stream läuft auf Apple TV!

## Home Assistant Integration (optional)

Mit dem Webhook kann Home Assistant VLC stoppen, bevor der neue Stream startet.

**Ablauf:**
1. 🍎 TV Button klicken
2. Webhook an Home Assistant
3. Verzögerung (z.B. 3 Sekunden)
4. Stream an Apple TV senden

**Beispiel-Webhook in Home Assistant:**
```yaml
alias: "Twitch: VLC stoppen"
trigger:
  - platform: webhook
    webhook_id: twitch_apple_tv
action:
  - service: media_player.media_stop
    target:
      entity_id: media_player.apple_tv_vlc
```

## Optional: Twitch Login

Das Tool funktioniert ohne Login. Mit Login (Client-ID + Token) gibt's weniger Rate-Limits.

**Token hinzufügen:**
1. Auf 🔐 klicken
2. Bei [twitchtokengenerator.com](https://twitchtokengenerator.com/) ein Token generieren
3. Einfügen & speichern

**Token entfernen:** Felder leer lassen → Speichern

## Update

```bash
cd /pfad/zu/twitch-github
git pull
docker pull ghcr.io/gedankenstrom/twitch-manager:latest
docker restart twitch_manager
```

## Mitmachen

[GitHub](https://github.com/gedankenstrom/twitch-manager) – Issues & Pull Requests willkommen.

---

Powered by [Streamlink](https://github.com/streamlink/streamlink)
