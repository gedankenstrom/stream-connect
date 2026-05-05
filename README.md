# Stream Connect
Streams auf Apple TV, VLC & Co. – ohne Zusatz-Apps.

## 🚀 Schnellstart

### Docker
```bash
docker run -d \
  --name stream-connect \
  -p 5000:5000 \
  -v stream-connect-data:/data \
  ghcr.io/gedankenstrom/stream-connect:latest
```
Oder `docker-compose.yml` aus dem Repo verwenden.

### Lokal
```bash
pip install streamlink flask docker
DATA_DIR=/tmp/stream-data python3 src/manager/manager.py
```

### Nutzung
1. Browser öffnen: `http://dein-server:5000`
2. Kanal eingeben → Stream starten
3. TV-Button → Direkt auf Apple TV

## 🛠 Wichtigste Features
- **Apple TV Direktstart** – per Knopfdruck in VLC
- **Multi-Player** – jeder HTTP-fähige Player
- **Zwei Modi** – Standard (low latency) oder CQ (stabil)
- **Home Assistant Webhook** – VLC stoppen vor neuem Stream
- **LIVE-Status** – sieht sofort ob Kanal online ist

## 📺 Apple TV Einrichtung
1. VLC installieren → **Remote Playback** aktivieren → IP notieren
2. Manager → Menü → **Apple TV** → IP eintragen → Speichern
3. Stream starten → **TV** klicken → fertig

---
[GitHub](https://github.com/gedankenstrom/stream-connect) | Powered by [Streamlink](https://github.com/streamlink/streamlink)
