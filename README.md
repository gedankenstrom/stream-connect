# Twitch Stream Manager

Twitch-Streams auf Apple TV, VLC & Co. – ohne Zusatz-Apps.

## Was macht das?

Läuft auf deinem Server (NAS, Raspberry Pi, etc.) und macht Twitch-Streams zu normalen HTTP-URLs. Die URL einfach in VLC, Apple TV oder einen anderen Player eintragen – fertig.

## Schnellstart

### 1. Deployen

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

### 2. Öffnen

Browser → `http://dein-server:5000`

### 3. Stream starten

- Kanal eingeben (z.B. `twitch.tv/kanal`)
- Port wählen
- Modus wählen: 🚀 Standard (schnell) oder 🎛️ CQ (stabil)
- Stream starten
- URL im Player öffnen

Fertig.

## Features

- 📺 Apple TV, VLC, Kodi – alles was HTTP kann
- 🔴 LIVE-Status – sieht sofort ob der Kanal online ist
- 💬 Chat – direkt im Browser öffnen
- 🎛️ Zwei Modi – Standard (low latency) oder CQ (stabil)
- 📱 Responsive – funktioniert auch am Handy
- 🌍 Multi-Arch – läuft auf AMD64 und ARM64 (Raspberry Pi)
- 🚀 Direkter Apple TV Start – Stream automatisch auf Apple TV (VLC) starten per Skript

## Optional: Twitch Login

Das Tool funktioniert ohne Login. Mit Login (Client-ID + Token) gibt's weniger Rate-Limits und zuverlässigeren Zugriff.

**Token hinzufügen:**
1. Auf 🔐 klicken
2. Bei [twitchtokengenerator.com](https://twitchtokengenerator.com/) ein Token generieren
3. Einfügen & speichern

**Token entfernen:** Felder leer lassen → Speichern

## Update

Automatisch: Jeden Sonntag um 3 Uhr

Manuell:
```bash
docker pull ghcr.io/gedankenstrom/twitch-manager:latest
docker restart twitch_manager
```

## Apple TV Direktstart

Stream automatisch auf Apple TV (VLC) starten – ohne manuelles Eintippen der URL.

### Voraussetzung
- Apple TV mit VLC-App
- VLC Remote Playback aktiviert (Einstellungen → Remote Playback)
- Python 3 auf dem Server

### Nutzung

```bash
# Stream direkt an Apple TV senden
python3 send_to_vlc.py
```

**Was passiert:** Das Skript verbindet sich per WebSocket mit VLC auf dem Apple TV und startet den aktuellen Stream sofort.

**Anpassen:** IP-Adressen in `send_to_vlc.py` editieren:
- `tv_ip = "192.168.25.20"` (Apple TV)
- `stream_url = "http://192.168.25.101:8095/fustler"` (Stream-Server)

### Automatisierung

Crontab (jede Stunde prüfen und starten falls online):
```bash
0 * * * * cd /pfad/zu/twitch-github && python3 send_to_vlc.py
```

## Mitmachen

[GitHub](https://github.com/gedankenstrom/twitch-manager) – Issues & Pull Requests willkommen.

---

Powered by [Streamlink](https://github.com/streamlink/streamlink)
