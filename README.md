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

## Mitmachen

[GitHub](https://github.com/gedankenstrom/twitch-manager) – Issues & Pull Requests willkommen.

---

Powered by [Streamlink](https://github.com/streamlink/streamlink)
