# Stream Connect
Streams auf Apple TV, VLC und Co. - ohne Zusatz-Apps.

Läuft auf deinem Server und macht Streams zu normalen HTTP-URLs. Einfach in den Player eintragen - fertig.

## Schnellstart

### Portainer Stack

```yaml
version: "3.8"
services:
  stream-connect:
    image: ghcr.io/gedankenstrom/stream-connect:latest
    container_name: stream-connect
    restart: unless-stopped
    ports:
      - "5000:5000"
    environment:
      - HOST_IP=auto
    volumes:
      - stream-connect-data:/data
      - /var/run/docker.sock:/var/run/docker.sock:ro
volumes:
  stream-connect-data:
```

### Docker Run

```bash
docker run -d \
  --name stream-connect \
  -p 5000:5000 \
  -v stream-connect-data:/data \
  ghcr.io/gedankenstrom/stream-connect:latest
```

### Lokal

```bash
pip install streamlink flask docker
DATA_DIR=/tmp/stream-data python3 src/manager/manager.py
```

## Nutzung

1. Browser offnen: `http://dein-server:5000`
2. Kanal eingeben - Stream starten
3. TV-Button - Direkt auf Apple TV

## Features

- Apple TV Direktstart - per Knopfdruck in VLC
- Multi-Player - jeder HTTP-fahige Player
- Zwei Modi - Standard (low latency) oder CQ (stabil)
- Home Assistant Webhook - VLC stoppen vor neuem Stream
- LIVE-Status - sieht sofort ob Kanal online ist

## Apple TV Einrichtung

1. VLC installieren - Remote Playback aktivieren - IP notieren
2. Manager - Menu - Apple TV - IP eintragen - Speichern
3. Stream starten - TV klicken - fertig

---

[GitHub](https://github.com/gedankenstrom/stream-connect) | Powered by [Streamlink](https://github.com/streamlink/streamlink)
