# Stream Connect
Streams auf Apple TV, VLC und Co. - ohne Zusatz-Apps.

Läuft auf deinem Server und macht Streams zu normalen HTTP-URLs. Einfach in den Player eintragen - fertig.

## Schnellstart

## Manager-Anmeldung (ab der Sicherheitsversion)

Der Manager startet nur, wenn drei Werte gesetzt sind. Es gibt keine eingebauten Zugangsdaten:

- `AUTH_USERNAME`: frei gewählter Benutzername.
- `AUTH_PASSWORD_HASH`: Werkzeug-Passworthash; das Passwort selbst wird nicht als Umgebungsvariable gespeichert.
- `SECRET_KEY`: zufälliger Schlüssel zum Signieren der Sitzung.

Hash und Schlüssel einmalig auf einem vertrauenswürdigen Rechner erzeugen:

```bash
python3 -c 'from getpass import getpass; from werkzeug.security import generate_password_hash; print(generate_password_hash(getpass("Neues Manager-Passwort: "), method="pbkdf2:sha256:600000"))'
python3 -c 'import secrets; print(secrets.token_urlsafe(48))'
```

Das Passwort beim ersten Befehl wird verdeckt eingegeben. Die beiden Ausgaben als `AUTH_PASSWORD_HASH` und `SECRET_KEY` in Portainers Stack-Umgebung eintragen; `AUTH_USERNAME` ebenfalls dort setzen. Diese Werte sicher aufbewahren. Bei Verlust des `SECRET_KEY` werden bestehende Anmeldesitzungen ungültig.

Für `http://192.168.25.101:5000` im Heimnetz `SESSION_COOKIE_SECURE=false` lassen. Das Cookie ist trotzdem `HttpOnly` und `SameSite=Lax`; Anmeldung und Managerzugriff werden jedoch über unverschlüsseltes HTTP übertragen. Ein Passwort-Hash schützt nur die Speicherung, nicht die Übertragung. Für eine stärkere Lösung den Manager nur aus dem vertrauenswürdigen LAN erreichbar machen und HTTPS über einen Reverse Proxy mit internem Zertifikat verwenden (zum Beispiel Caddy mit einer lokalen CA). Dann `SESSION_COOKIE_SECURE=true` setzen und die Oberfläche über HTTPS öffnen. Der Proxy muss TLS terminieren; Stream-URLs auf 8090–8110 bleiben HTTP und direkt für Apple TV/VLC erreichbar.

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
      - AUTH_PASSWORD_HASH=${AUTH_PASSWORD_HASH:?Set in Portainer}
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
  -v stream-connect-data:/data \
  ghcr.io/gedankenstrom/stream-connect:latest
```

### Lokal

```bash
pip install streamlink flask docker
DATA_DIR=/tmp/stream-data python3 src/manager/manager.py
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
