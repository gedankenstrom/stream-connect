# Twitch Stream Manager

Web-basierter Twitch-Stream-Manager für Apple TV, VLC und andere Player. Konvertiert Twitch-Streams zu HTTP-Streams mit automatischer Qualitätsanpassung.

## Features

- 🎬 **Segment-Filterung** – Filtert nicht-Stream-Inhalte
- 🔓 **Optionaler Login** – Funktioniert mit oder ohne Twitch OAuth-Token
- 🎛️ **Zwei Modi:**
  - **Standard:** Segment-Filterung mit Low-Latency
  - **CQ:** Automatische Qualitätsanpassung
- 🔐 **Dezente Token-Verwaltung** – Eingeklappt wenn gesetzt, optional immer bearbeitbar
- 🐳 **Portainer-ready** – Ein Docker Compose Stack
- 🌍 **Multi-Arch:** AMD64 + ARM64 (für Raspberry Pi)

## Quick Start

### 1. In Portainer deployen

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
      - HOST_IP=auto  # oder feste IP: 192.168.1.100
    volumes:
      - twitch-data:/data
      - /var/run/docker.sock:/var/run/docker.sock:ro

volumes:
  twitch-data:
```

### 2. Web-UI öffnen

`http://dein-host:5000`

### 3. Optional: OAuth-Token hinzufügen

- Auf "OAuth-Token (Optional)" klicken
- Token eingeben und speichern
- **Oder leer lassen** für anonymes Streaming

**Token holen:** [twitchtokengenerator.com](https://twitchtokengenerator.com/)

### 4. Stream starten

- Kanalnamen eingeben
- Port wählen
- Modus auswählen (Standard oder CQ)
- URL in VLC/Apple TV einfügen

## Modi im Vergleich

| Feature | Standard | CQ (Custom Quality) |
|---------|----------|---------------------|
| **Buffer** | Klein (2) | Groß (500) |
| **Low-Latency** | ✅ Ja | ❌ Nein |
| **Segment-Handling** | Filterung | Automatische Qualitätsanpassung |
| **Empfohlen für** | Live-Action | Talkshows, AFK-Streams |

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

## OAuth-Token (Optional)

| Mit Token | Ohne Token |
|-----------|-----------|
| Zuverlässigerer Zugriff | Funktioniert für meiste Streams |
| Weniger Rate-Limits | Kann bei manchen Kanälen Probleme haben |
| Sub-only Streams möglich | Nur öffentliche Streams |

**Token löschen:** Formular öffnen → Feld leer lassen → Speichern

## Images

- `ghcr.io/gedankenstrom/twitch-manager:latest` – Web-UI & Steuerung
- `ghcr.io/gedankenstrom/twitch-stream-runner:latest` – Streamlink-Container

## Automatische Updates

Das Stream-Runner Image enthält Streamlink und wird automatisch aktualisiert:

- **Wöchentlich** (Sonntag 3 Uhr) prüft ein GitHub Action Workflow auf neue Streamlink-Versionen
- Bei neuer Version: Automatischer Build und Push zu GHCR
- Das Manager-Image bleibt stabil – nur Streamlink wird aktualisiert

### Manuelles Update erzwingen

In Portainer den Stack **neu deployen** oder Container neu starten:

```bash
docker pull ghcr.io/gedankenstrom/twitch-stream-runner:latest
docker restart twitch_manager
```

### Update-Status prüfen

GitHub → Actions → "Update Streamlink" zeigt den letzten Check an.

## Entwicklung

### Lokal bauen

```bash
docker build -t twitch-manager .
docker run -v /var/run/docker.sock:/var/run/docker.sock:ro -p 5000:5000 twitch-manager
```

### Stream-Runner bauen

```bash
cd stream
docker build -t twitch-stream-runner .
```

## Credits

- [Streamlink](https://github.com/streamlink/streamlink) – Twitch-Stream-Extraktion
