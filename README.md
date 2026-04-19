# Twitch Stream Manager

Wandelt Twitch-Livestreams in HTTP-Streams um – zum Abspielen auf **Apple TV**, in **VLC** und anderen Playern.

> 💡 **Wie es funktioniert:** Diese Software läuft auf einem Server (z.B. NAS, Raspberry Pi, VPS) und stellt Twitch-Streams als HTTP-URL bereit. Du öffnest dann die generierte URL auf deinem Apple TV, in VLC oder einem anderen Player.

## Schnellstart

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
      - HOST_IP=auto  # Deine lokale IP: `ip addr` oder `ifconfig` zeigt sie
    volumes:
      - twitch-data:/data
      - /var/run/docker.sock:/var/run/docker.sock:ro

volumes:
  twitch-data:
```

> 💡 **Tipp:** `HOST_IP=auto` erkennt die IP automatisch. Alternativ kannst du eine feste IP eintragen, z.B. `HOST_IP=192.168.1.100`

### 2. Web-UI öffnen

Öffne `http://dein-host:5000` im Browser.

### 3. Stream starten

1. **Kanal eingeben** – Name oder Twitch-URL (z.B. `twitch.tv/kanal`)
2. **Port wählen** – freien Port aus der Liste
3. **Modus wählen**:
   - 🚀 **Standard** – Segment-Filterung, geringe Latenz
   - 🎛️ **CQ** – Automatische Qualitätsanpassung
4. **Stream starten** – URL wird erzeugt
5. **Im Player öffnen** – Die URL auf Apple TV, VLC oder anderen Geräten eingeben

### 4. Chat öffnen (optional)

Auf den 💬 **Chat**-Button klicken – öffnet Twitch-Chat im Pop-up.

---

## Features

- 🎬 **Segment-Filterung** – Automatische Filterung nicht-Stream-Inhalte
- 🔓 **Optionaler Login** – Funktioniert mit oder ohne Twitch-Account
- 🎛️ **Zwei Modi** – Standard (Low-Latency) oder CQ (Qualitätsanpassung)
- 💬 **Integrierter Chat** – Direkter Zugriff auf Twitch-Chat
- 🌍 **Multi-Arch** – AMD64 + ARM64 (Raspberry Pi)
- 🐳 **Portainer-ready** – Ein Stack, fertig deployen

---

## OAuth-Token (optional)

Das Tool funktioniert ohne Anmeldung. Ein Token verbessert aber die Zuverlässigkeit:

| Mit Token | Ohne Token |
|-----------|-----------|
| Zuverlässigerer Zugriff | Funktioniert für meiste Streams |
| Weniger Rate-Limits | Kann bei manchen Kanälen Probleme haben |
| Sub-only Streams | Nur öffentliche Streams |

**Token hinzufügen:**
1. Auf 🔐 **Token** klicken
2. Token von [twitchtokengenerator.com](https://twitchtokengenerator.com/) einfügen
3. Speichern

**Token entfernen:** Feld leer lassen → Speichern

---

## Modi im Vergleich

| | Standard | CQ |
|---|----------|-----|
| **Buffer** | Klein (2) | Groß (500) |
| **Low-Latency** | ✅ Ja | ❌ Nein |
| **Segment-Handling** | Filterung | Automatische Anpassung |

---

## Automatische Updates

Der Stream-Runner enthält Streamlink und wird wöchentlich (Sonntag 3 Uhr) automatisch aktualisiert.

**Manuell updaten:**
```bash
docker pull ghcr.io/gedankenstrom/twitch-stream-runner:latest
docker restart twitch_manager
```

---

## Technische Details

### Images
- `ghcr.io/gedankenstrom/twitch-manager:latest` – Web-UI & Steuerung
- `ghcr.io/gedankenstrom/twitch-stream-runner:latest` – Streamlink-Container

### Architektur
```
Browser → Twitch Manager → Stream Container → Twitch API
```

### Ports
- `5000` – Web-UI
- `8090-8111` – Stream-Ports (konfigurierbar)

---

## Credits

- [Streamlink](https://github.com/streamlink/streamlink) – Stream-Extraktion
