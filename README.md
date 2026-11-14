# Stream Connect

Stream Connect startet Twitch-Streams als normale HTTP-Streams für VLC, Apple TV und andere Player.

## Installation mit Portainer

Lege in Portainer unter **Stacks → stream-connect → Environment variables** diese Werte an:

| Variable | Wert |
|---|---|
| `AUTH_USERNAME` | Dein gewünschter Benutzername |
| `AUTH_PASSWORD` | Ein starkes, nur hierfür verwendetes Passwort |
| `SECRET_KEY` | Ein zufälliger Sitzungsschlüssel |
| `SESSION_COOKIE_SECURE` | `true`, wenn du den Manager über HTTPS mit deinem Reverse Proxy öffnest |

Sitzungsschlüssel erzeugen:

```bash
python3 -c 'import secrets; print(secrets.token_urlsafe(48))'
```

Füge den ausgegebenen Wert als `SECRET_KEY` in Portainer ein. Benutzername und Passwort legst du dort direkt fest; einen Passwort-Hash musst du nicht erzeugen.

Verwende anschließend diesen Stack:

```yaml
services:
  stream-connect:
    image: ghcr.io/gedankenstrom/stream-connect:latest
    container_name: stream-connect
    restart: unless-stopped
    ports:
      - "5000:5000"
    environment:
      HOST_IP: auto
      DATA_DIR: /data
      AUTH_USERNAME: ${AUTH_USERNAME:?In Portainer setzen}
      AUTH_PASSWORD: ${AUTH_PASSWORD:?In Portainer setzen}
      SECRET_KEY: ${SECRET_KEY:?In Portainer setzen}
      SESSION_COOKIE_SECURE: "true"
    volumes:
      - stream-connect-data:/data
      - /var/run/docker.sock:/var/run/docker.sock:ro

volumes:
  stream-connect-data:
```

Deploye den Stack und öffne den Manager über die **HTTPS-Adresse deines Reverse Proxys**. Wenn du den Manager nur über HTTP verwendest, muss `SESSION_COOKIE_SECURE` auf `false` stehen; dabei werden Passwort und Sitzung unverschlüsselt übertragen. Das Manager-Passwort liegt als Docker-Umgebungsvariable vor und ist für Personen mit Zugriff auf Docker oder Portainer auslesbar.

## Streams starten

1. Im Browser den Manager öffnen und anmelden.
2. Einen Twitch-Kanal auswählen und **Stream starten**.
3. Die angezeigte Stream-URL in VLC oder einem anderen Player öffnen.
4. Für Apple TV die VLC-Fernsteuerung aktivieren, die Apple-TV-IP in den Manager-Einstellungen eintragen und den TV-Button verwenden.

Die Anmeldung schützt nur den Manager. Stream-URLs auf den Ports 8090–8110 bleiben für VLC und Apple TV direkt per HTTP erreichbar.

## Funktionen

- Twitch-Streams mit Standard- oder CQ-Modus
- Live-Status und Stream-Informationen
- Direktstart auf Apple TV mit VLC
- Optionaler Home-Assistant-Webhook

---

[GitHub](https://github.com/gedankenstrom/stream-connect) · Powered by [Streamlink](https://github.com/streamlink/streamlink)
