# Twitch Stream Manager

Web-basierter Twitch-Stream-Manager für Apple TV und andere Geräte. Konvertiert Twitch-Streams zu HTTP-Streams, die direkt in VLC oder andere Player abgespielt werden können – ohne Werbung.

## Features

- 🎬 **Werbe-freie Streams** – Automatische Werbe-Filterung seit Streamlink 7.5.0
- 🎛️ **Zwei Modi:**
  - **Standard:** Automatisches Werbe-Überspringen mit Low-Latency
  - **CQ (Custom Quality):** Bei langen Werbeblöcken → 360p, danach zurück auf Best
- 🔐 **OAuth-Token-Verwaltung** – Einfach in Web-UI eingeben, sicher gespeichert
- 🐳 **Portainer-ready** – Ein Docker Compose Stack, automatischer Build via GitHub Actions
- 🌍 **Multi-Arch:** AMD64 + ARM64 (für Raspberry Pi)

## Quick Start

### 1. OAuth-Token holen

1. Twitch.tv im Browser öffnen und einloggen
2. DevTools (F12) → Netzwerk-Tab
3. Beliebigen Stream öffnen
4. Nach `access_token` suchen → Token kopieren (beginnt mit `oauth:`)

### 2. Portainer Stack deployen

```yaml
version: "3.8"

services:
  twitch-manager:
    image: ghcr.io/gedankenstrom/twitch-stream-manager:latest
    container_name: twitch_manager
    restart: unless-stopped
    ports:
      - "5000:5000"
    environment:
      - HOST_IP=auto  # oder feste IP: 192.168.1.100
    volumes:
      - twitch-data:/data
      - /var/run/docker.sock:/var/run/docker.sock:ro
    networks:
      - twitch-net

volumes:
  twitch-data:

networks:
  twitch-net:
```

### 3. Web-UI nutzen

1. `http://dein-host:5000` öffnen
2. OAuth-Token eingeben und speichern
3. Kanalnamen eingeben, Port wählen, Modus auswählen
4. Stream starten → URL kopieren → in VLC auf Apple TV einfügen

## Architektur

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────┐
│   Web Browser   │────▶│  Twitch Manager  │────▶│   Stream    │
│   (Port 5000)   │     │   (Flask + UI)   │     │  Container  │
└─────────────────┘     └──────────────────┘     └──────┬──────┘
                                                        │
                              ┌────────────────────────┘
                              ▼
                        ┌──────────────┐
                        │  Twitch API  │
                        └──────────────┘
```

## Entwicklung

### Lokal bauen

```bash
docker build -t twitch-manager .
docker run -v /var/run/docker.sock:/var/run/docker.sock:ro -p 5000:5000 twitch-manager
```

### GitHub Actions

Automatisch bei Push zu `main` oder Tags:
- Multi-Arch Build (AMD64 + ARM64)
- Push zu GHCR
- Tags: `latest`, `v1.0.0`, etc.

## Credits

- [Streamlink](https://github.com/streamlink/streamlink) – Das Herzstück für Twitch-Stream-Extraktion
