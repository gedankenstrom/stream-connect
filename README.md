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

### 3. Öffnen

Browser → `http://dein-server:5000`

### 4. Stream starten

- Kanal eingeben (z.B. `kanal`)
- Port: 🎲 Automatisch oder manuell wählen
- Modus: 🚀 Standard oder 🎛️ CQ
- Stream starten
- 🍎 TV Button klicken → Stream auf Apple TV

Fertig.

## Features

- 📺 Apple TV, VLC, Kodi – alles was HTTP kann
- 🍎 Direkter Apple TV Start – per Knopfdruck in VLC auf Apple TV
- 🔴 LIVE-Status – sieht sofort ob der Kanal online ist
- 💬 Chat – direkt im Browser öffnen
- 🎛️ Zwei Modi – Standard (low latency) oder CQ (stabil)
- 📱 Responsive – funktioniert auch am Handy
- 🎲 Automatische Port-Wahl

## Apple TV Einrichtung

### 1. VLC auf Apple TV

1. VLC-App installieren (App Store)
2. Einstellungen → Remote Playback aktivieren
3. IP notieren (z.B. `192.168.25.20`)

### 2. IP im Manager speichern

1. Auf ☰ (Menü) klicken
2. 🍎 Apple TV auswählen
3. IP-Adresse eingeben
4. Speichern

### 3. Stream senden

- Stream starten
- Auf 🍎 TV Button klicken
- Stream läuft auf Apple TV!

## Optional: Twitch Login

Das Tool funktioniert ohne Login. Mit Login (Client-ID + Token) gibt's weniger Rate-Limits und zuverlässigeren Zugriff.

**Token hinzufügen:**
1. Auf 🔐 klicken
2. Bei [twitchtokengenerator.com](https://twitchtokengenerator.com/) ein Token generieren
3. Einfügen & speichern

**Token entfernen:** Felder leer lassen → Speichern

## Update

```bash
cd /pfad/zu/twitch-github
git pull
sudo systemctl restart twitch-manager
```

## Mitmachen

[GitHub](https://github.com/gedankenstrom/twitch-manager) – Issues & Pull Requests willkommen.

---

Powered by [Streamlink](https://github.com/streamlink/streamlink)
