# Stream Connect
Streams auf Apple TV, VLC und Co. - ohne Zusatz-Apps.

Läuft auf deinem Server und macht Streams zu normalen HTTP-URLs. Einfach in den Player eintragen - fertig.

## Schnellstart

## Manager-Anmeldung (ab der Sicherheitsversion)

Der Manager startet nur, wenn drei Werte gesetzt sind. Es gibt keine eingebauten Zugangsdaten. In Portainer unter **Stacks → stream-connect → Environment variables** setzt du:

- `AUTH_USERNAME`: frei gewählter Benutzername.
- `AUTH_PASSWORD`: frei gewähltes Manager-Passwort.
- `SECRET_KEY`: zufälliger Schlüssel zum Signieren der Sitzung.

Einen Sitzungsschlüssel einmalig erzeugen:

```bash
python3 -c 'import secrets; print(secrets.token_urlsafe(48))'
```

Die Ausgabe als `SECRET_KEY` eintragen. Wähle dein eigenes Passwort und trage es zusammen mit dem Benutzernamen direkt in Portainers Stack-Umgebungsvariablen ein. Die Anwendung bildet beim Start daraus intern einen Passwort-Hash; die Hash-Erzeugung auf dem Mac entfällt. Bei Verlust des `SECRET_KEY` werden bestehende Anmeldesitzungen ungültig.

**Sicherheitshinweis:** `AUTH_PASSWORD` wird von Docker als Umgebungsvariable in der Container-Konfiguration gespeichert und kann von Personen mit Zugriff auf Docker oder Portainer ausgelesen werden. Beschränke diesen Zugriff und verwende ein starkes, nur hierfür genutztes Passwort. Der Passwort-Hash wird in der Anwendung zur Prüfung verwendet; das entfernt das Klartext-Passwort nicht aus Dockers Container-Konfiguration.

Da der Manager bei dir über einen Reverse Proxy mit HTTPS erreichbar ist, setze `SESSION_COOKIE_SECURE=true` und öffne die Oberfläche über die HTTPS-Adresse des Proxys. Das Cookie ist zusätzlich `HttpOnly` und `SameSite=Lax`. Die direkte HTTP-Adresse `http://192.168.25.101:5000` ist dann nicht für die Anmeldung geeignet. Stream-URLs auf 8090–8110 bleiben HTTP und direkt für Apple TV/VLC erreichbar.

Vor dem Aktualisieren einer bestehenden Installation müssen die drei Variablen gesetzt sein; andernfalls beendet sich der Manager absichtlich mit einer klaren Fehlermeldung. Der Login schützt nur die Manager-Weboberfläche. Stream-Endpunkte und Apple-TV/VLC-Funktion werden nicht an Browser-Sitzungen gebunden.

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
      - AUTH_USERNAME=${AUTH_USERNAME:?Set in Portainer}
      - AUTH_PASSWORD=${AUTH_PASSWORD:?Set in Portainer}
      - SECRET_KEY=${SECRET_KEY:?Set in Portainer}
      - SESSION_COOKIE_SECURE=${SESSION_COOKIE_SECURE:-false}
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
  -e AUTH_USERNAME=streamadmin \
  -e AUTH_PASSWORD='choose-a-strong-unique-password' \
  -e SECRET_KEY='paste-a-random-key-here' \
  -e SESSION_COOKIE_SECURE=false \
  -v stream-connect-data:/data \
  ghcr.io/gedankenstrom/stream-connect:latest
```

### Lokal

```bash
pip install streamlink flask docker
AUTH_USERNAME=streamadmin AUTH_PASSWORD='choose-a-strong-unique-password' SECRET_KEY='paste-a-random-key-here' DATA_DIR=/tmp/stream-data python3 src/manager/manager.py
```

## Nutzung

1. Browser öffnen: `http://dein-server:5000` und mit dem zuvor konfigurierten Konto anmelden.
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
