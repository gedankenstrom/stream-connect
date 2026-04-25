from flask import Flask, render_template, request, jsonify
import docker
import socket
import os
import sqlite3
import secrets
import requests
import time
import asyncio
import base64
import json
import struct
import random

app = Flask(__name__)
client = docker.from_env()

# Konfiguration
DATA_DIR = os.environ.get("DATA_DIR", "/data")
DB_PATH = os.path.join(DATA_DIR, "tokens.db")
SPORT_PORTS = list(range(8090, 8111))

# Einfacher Cache für Twitch-Status und User-Infos
CACHE = {}
CACHE_TTL = 30  # Sekunden
USER_CACHE = {}
USER_CACHE_TTL = 3600  # 1 Stunde für User-Daten (selten ändernd)

def get_twitch_user_info(channel):
    """Holt Twitch-User-Daten (Profilbild, Display-Name)."""
    now = time.time()
    
    # Prüfe Cache
    if channel in USER_CACHE:
        cached_time, cached_result = USER_CACHE[channel]
        if now - cached_time < USER_CACHE_TTL:
            return cached_result
    
    try:
        creds = get_credentials()
        client_id = creds['client_id'] or 'kimne78kx3ncx6brgo4mv6wki5h1ko'
        oauth_token = creds['token']
        
        headers = {'Client-ID': client_id}
        if oauth_token:
            headers['Authorization'] = f'Bearer {oauth_token.replace("oauth:", "")}'
        
        response = requests.get(
            f"https://api.twitch.tv/helix/users?login={channel.lower()}",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('data') and len(data['data']) > 0:
                user = data['data'][0]
                result = {
                    'display_name': user.get('display_name', channel),
                    'profile_image_url': user.get('profile_image_url', ''),
                    'login': user.get('login', channel)
                }
                USER_CACHE[channel] = (now, result)
                return result
        
        # Fallback
        result = {'display_name': channel, 'profile_image_url': '', 'login': channel}
        USER_CACHE[channel] = (now, result)
        return result
        
    except Exception as e:
        print(f"[manager] User-Info fetch failed for {channel}: {e}")
        return {'display_name': channel, 'profile_image_url': '', 'login': channel}

def get_cached_live_status(channel):
    """Holt Live-Status aus Cache oder API."""
    now = time.time()
    
    # Prüfe Cache
    if channel in CACHE:
        cached_time, cached_result = CACHE[channel]
        if now - cached_time < CACHE_TTL:
            return cached_result
    
    # Cache miss oder abgelaufen - neu abfragen
    result = check_twitch_live(channel)
    CACHE[channel] = (now, result)
    return result

def check_twitch_live(channel):
    """Prüft ob ein Twitch-Kanal aktuell live ist via Twitch API und gibt Stream-Details zurück."""
    try:
        # Credentials laden
        creds = get_credentials()
        client_id = creds['client_id'] or 'kimne78kx3ncx6brgo4mv6wki5h1ko'  # Public fallback
        oauth_token = creds['token']
        
        # Twitch API Helix - Streams endpoint
        headers = {
            'Client-ID': client_id,
        }
        
        if oauth_token:
            headers['Authorization'] = f'Bearer {oauth_token.replace("oauth:", "")}'
        
        response = requests.get(
            f"https://api.twitch.tv/helix/streams?user_login={channel.lower()}",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('data') and len(data['data']) > 0:
                stream = data['data'][0]
                return {
                    'live': True,
                    'title': stream.get('title', ''),
                    'game': stream.get('game_name', ''),
                    'viewers': stream.get('viewer_count', 0),
                    'started_at': stream.get('started_at', '')
                }
            return {'live': False, 'title': '', 'game': '', 'viewers': 0, 'started_at': ''}
        
        # Fallback: Prüfe via Streamlink (kein Token nötig)
        return check_streamlink_live(channel)
        
    except Exception as e:
        print(f"[manager] Twitch API check failed for {channel}: {e}")
        return check_streamlink_live(channel)

def check_streamlink_live(channel):
    """Fallback: Prüft Live-Status via Streamlink (kein Token nötig)."""
    try:
        import subprocess
        result = subprocess.run(
            ['streamlink', '--json', f'https://twitch.tv/{channel}', 'best'],
            capture_output=True,
            text=True,
            timeout=10
        )
        # Wenn Streamlink Streams findet, ist der Kanal live
        if result.returncode == 0 and 'streams' in result.stdout:
            return {'live': True}
        return {'live': False}
    except:
        return {'live': False}

def init_db():
    """Initialisiert SQLite-Datenbank für Twitch Credentials."""
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Neue Tabelle mit Client-ID und Token
    c.execute('''CREATE TABLE IF NOT EXISTS twitch_credentials (
        id INTEGER PRIMARY KEY,
        client_id TEXT,
        token TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Alte Tabelle migrieren falls vorhanden
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tokens'")
    if c.fetchone():
        # Migration: Token aus alter Tabelle holen
        try:
            c.execute("SELECT token FROM tokens ORDER BY id DESC LIMIT 1")
            row = c.fetchone()
            if row:
                c.execute("INSERT INTO twitch_credentials (token) VALUES (?)", (row[0],))
            c.execute("DROP TABLE tokens")
        except:
            pass
    
    # Neue Tabelle für allgemeine Einstellungen
    c.execute('''CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )''')
    
    conn.commit()
    conn.close()

def save_credentials(client_id, token):
    """Speichert Twitch Client-ID und OAuth-Token."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM twitch_credentials")
    c.execute("INSERT INTO twitch_credentials (client_id, token) VALUES (?, ?)", (client_id, token))
    conn.commit()
    conn.close()
    # Invalidate user cache to fetch profile images with new credentials
    global USER_CACHE
    USER_CACHE.clear()
    print("[manager] User cache cleared due to credential change")

def get_credentials():
    """Liest Twitch Client-ID und OAuth-Token zurück."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT client_id, token FROM twitch_credentials ORDER BY id DESC LIMIT 1")
    row = c.fetchone()
    conn.close()
    if row:
        return {'client_id': row[0], 'token': row[1]}
    return {'client_id': None, 'token': None}

def get_token():
    """Liest OAuth-Token zurück (für Kompatibilität)."""
    creds = get_credentials()
    return creds['token']

def save_setting(key, value):
    """Speichert eine Einstellung."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()

def get_setting(key, default=None):
    """Liest eine Einstellung zurück."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = c.fetchone()
    conn.close()
    if row:
        return row[0]
    return default

def get_host_ip():
    """Ermittelt die lokale IP-Adresse."""
    env_ip = os.environ.get("HOST_IP")
    if env_ip and env_ip != "auto":
        return env_ip
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "localhost"

def get_streams():
    """Listet alle Twitch-Stream-Container auf."""
    containers = client.containers.list(all=True, filters={"name": "twitch_stream_"})
    stream_data = []
    used_ports = []

    for c in containers:
        host_port = "?"
        try:
            bindings = c.attrs.get("HostConfig", {}).get("PortBindings", {}) or {}
            if bindings:
                first_key = list(bindings.keys())[0]
                host_port = int(bindings[first_key][0].get("HostPort", "?"))
                used_ports.append(host_port)
        except Exception:
            host_port = "?"

        # Parse Container-Name (entferne twitch_stream_ und Controller-Suffix)
        full_name = c.name.replace("twitch_stream_", "", 1)
        controller = "Standard"
        
        # Extrahiere Controller-Typ und bereinige Kanalnamen
        if "_cq" in full_name:
            controller = "CQ"
            name = full_name.replace("_cq", "")
        elif "_standard" in full_name:
            controller = "Standard"
            name = full_name.replace("_standard", "")
        else:
            name = full_name

        # Prüfe Live-Status via Twitch API (mit Cache)
        is_live = False
        stream_info = {}
        user_info = {}
        if c.status == "running":
            try:
                status = get_cached_live_status(name)
                is_live = status.get('live', False)
                stream_info = status
                user_info = get_twitch_user_info(name)
            except:
                is_live = False

        stream_data.append({
            "name": c.name,
            "channel": name,
            "display_name": user_info.get('display_name', name),
            "profile_image": user_info.get('profile_image_url', ''),
            "status": c.status,
            "port": host_port,
            "controller": controller,
            "is_live": is_live,
            "stream_info": stream_info,
        })

    # Sortiere Streams: LIVE zuerst, dann Container-Status, dann Name
    stream_data.sort(key=lambda x: (-int(x['is_live']), -int(x['status'] == 'running'), x['channel'].lower()))
    
    available_ports = [p for p in SPORT_PORTS if p not in used_ports]
    return stream_data, available_ports

@app.route('/')
def index():
    streams, available_ports = get_streams()
    creds = get_credentials()
    return render_template(
        'index.html',
        streams=streams,
        host_ip=get_host_ip(),
        sport_ports=available_ports,
        has_credentials=bool(creds['token']),
        client_id_preview=creds['client_id'][:10] + "..." if creds['client_id'] else None,
        token_preview=creds['token'][:10] + "..." if creds['token'] else None,
        apple_tv_ip=get_setting('apple_tv_ip', ''),
        homeassistant_webhook=get_setting('homeassistant_webhook', ''),
        apple_tv_delay=get_setting('apple_tv_delay', '3')
    )

@app.route('/api/stream-status/<channel>')
def stream_status(channel):
    """API Endpoint für Live-Status eines Streams."""
    # Hier könnte ein echter Twitch API Call hin
    return jsonify({"live": None, "message": "Status-Check kommt im nächsten Update"})

@app.route('/api/streams')
def api_streams():
    """API Endpoint für alle Streams mit Live-Status (für UI-Updates)."""
    streams, _ = get_streams()
    return jsonify({"streams": streams})

@app.route('/save-token', methods=['POST'])
def save_token_route():
    """Speichert Twitch Credentials (Client-ID und OAuth-Token) oder löscht bei leerem Feld."""
    client_id = request.form.get('client_id', '').strip()
    token = request.form.get('token', '').strip()
    
    # Beide leer = löschen
    if not client_id and not token:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("DELETE FROM twitch_credentials")
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "Credentials gelöscht"})
    
    # Token validieren
    if token and not token.startswith('oauth:'):
        token = 'oauth:' + token
    
    # Teste Credentials gegen Twitch API
    if token:
        try:
            test_headers = {'Client-ID': client_id or 'kimne78kx3ncx6brgo4mv6wki5h1ko'}
            test_headers['Authorization'] = f'Bearer {token.replace("oauth:", "")}'
            response = requests.get(
                'https://api.twitch.tv/helix/users',
                headers=test_headers,
                timeout=5
            )
            if response.status_code == 401:
                return jsonify({"success": False, "error": "Ungültige Credentials (401)"}), 400
        except Exception as e:
            print(f"[manager] Credential-Test fehlgeschlagen: {e}")
            # Trotzdem speichern (API könnte kurzzeitig down sein)
    
    save_credentials(client_id or '', token or '')
    return jsonify({"success": True})

@app.route('/start', methods=['POST'])
def start():
    """Startet einen neuen Stream-Container."""
    channel = request.form.get('channel', '').strip()
    port = request.form.get('port', '').strip()
    controller_type = request.form.get('controller_type', 'standard')

    if not channel:
        return jsonify({"error": "Kanal darf nicht leer sein."}), 400
    
    # Wenn kein Port angegeben, automatisch den ersten freien wählen
    if not port:
        streams, available_ports = get_streams()
        if not available_ports:
            return jsonify({"error": "Keine freien Ports verfügbar (max. 20 Streams)."}), 400
        port = str(available_ports[0])
        print(f"[manager] Auto-Port gewählt: {port}")
    
    if not port.isdigit():
        return jsonify({"error": "Port muss eine Zahl sein."}), 400

    port = int(port)
    
    oauth_token = get_token()
    if not oauth_token:
        print(f"[manager] Kein OAuth-Token gesetzt, starte Stream anonym für {channel}")

    name = f"twitch_stream_{channel}_{controller_type}"
    existing = client.containers.list(all=True, filters={"name": name})
    if existing:
        return jsonify({"error": f"Container {name} existiert bereits."}), 400

    script_filename = "stream_controller.py" if controller_type == "standard" else "stream_controller_cq.py"

    try:
        client.containers.run(
            "ghcr.io/gedankenstrom/twitch-stream-runner:latest",
            name=name,
            detach=True,
            restart_policy={"Name": "unless-stopped"},
            working_dir="/app",
            environment={
                "TWITCH_OAUTH_TOKEN": oauth_token,
                "CHANNEL": channel,
                "PORT": str(port),
                "QUALITY": "best",
                "CONTROLLER_TYPE": controller_type
            },
            ports={f"{port}/tcp": port},
            dns=["8.8.8.8", "8.8.4.4"]
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    return jsonify({
        "success": True,
        "channel": channel,
        "port": port,
        "host_ip": get_host_ip(),
        "controller_type": controller_type,
        "name": name
    })

@app.route('/stop/<name>', methods=['POST'])
def stop(name):
    """Stoppt und entfernt einen Stream-Container."""
    try:
        container = client.containers.get(name)
        bindings = container.attrs.get("HostConfig", {}).get("PortBindings", {})
        port = None
        if bindings:
            first_key = list(bindings.keys())[0]
            port = int(first_key.split("/")[0])
        container.stop()
        container.remove()
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    return jsonify({"success": True, "port": port})


# ===== APPLE TV VLC INTEGRATION =====

async def send_url_to_vlc_apple_tv(tv_ip, stream_url):
    """Sendet Stream-URL per WebSocket an VLC auf Apple TV."""
    key = base64.b64encode(bytes(random.getrandbits(8) for _ in range(16))).decode()
    
    request = (
        f"GET / HTTP/1.1\r\n"
        f"Host: {tv_ip}\r\n"
        f"Upgrade: websocket\r\n"
        f"Connection: Upgrade\r\n"
        f"Sec-WebSocket-Key: {key}\r\n"
        f"Sec-WebSocket-Version: 13\r\n"
        f"\r\n"
    )
    
    reader, writer = await asyncio.open_connection(tv_ip, 80)
    writer.write(request.encode())
    await writer.drain()
    
    response = b""
    while b"\r\n\r\n" not in response:
        response += await reader.read(1)
    
    # Build WebSocket text frame
    message = json.dumps({"type": "openURL", "url": stream_url})
    payload = message.encode('utf-8')
    
    frame = bytearray()
    frame.append(0x81)  # FIN=1, opcode=text
    length = len(payload)
    if length < 126:
        frame.append(length)
    elif length < 65536:
        frame.append(126)
        frame.extend(struct.pack('>H', length))
    else:
        frame.append(127)
        frame.extend(struct.pack('>Q', length))
    frame.extend(payload)
    
    writer.write(frame)
    await writer.drain()
    
    try:
        data = await asyncio.wait_for(reader.read(1024), timeout=2.0)
        if data:
            return {"success": True, "response_bytes": len(data)}
    except asyncio.TimeoutError:
        pass
    finally:
        writer.close()
        await writer.wait_closed()
    
    return {"success": True}


@app.route('/save-setting', methods=['POST'])
def save_setting_route():
    """Speichert eine allgemeine Einstellung."""
    data = request.get_json() or request.form
    key = data.get('key', '').strip()
    value = data.get('value', '').strip()
    if not key:
        return jsonify({"success": False, "error": "Key fehlt"}), 400
    save_setting(key, value)
    return jsonify({"success": True, "key": key, "value": value})

@app.route('/get-setting/<key>')
def get_setting_route(key):
    """Liest eine allgemeine Einstellung zurück."""
    value = get_setting(key, '')
    return jsonify({"success": True, "key": key, "value": value})


@app.route('/send-to-apple-tv', methods=['POST'])
def send_to_apple_tv():
    """Sendet aktuellen Stream an Apple TV (VLC)."""
    data = request.get_json() or request.form
    tv_ip = data.get('tv_ip', '').strip()
    if not tv_ip:
        tv_ip = get_setting('apple_tv_ip', '192.168.25.20')
    stream_url = data.get('stream_url', '').strip()
    
    if not stream_url:
        # Versuche aktiven Stream zu finden
        streams, _ = get_streams()
        running = [s for s in streams if s['status'] == 'running']
        if running:
            stream_url = f"http://{get_host_ip()}:{running[0]['port']}/{running[0]['channel']}"
        else:
            return jsonify({"success": False, "error": "Kein aktiver Stream gefunden"}), 400
    
    # Webhook an Home Assistant senden (optional)
    webhook_url = get_setting('homeassistant_webhook', '')
    if webhook_url:
        try:
            requests.post(webhook_url, json={"event": "twitch_apple_tv", "channel": stream_url.split('/')[-1], "action": "start"}, timeout=5)
            print(f"[manager] Webhook an Home Assistant gesendet: {webhook_url}")
        except Exception as e:
            print(f"[manager] Webhook fehlgeschlagen: {e}")
    
    # Verzögerung einstellbar (Standard: 3 Sekunden)
    delay = int(get_setting('apple_tv_delay', '3'))
    if delay > 0:
        time.sleep(delay)
    
    try:
        result = asyncio.run(send_url_to_vlc_apple_tv(tv_ip, stream_url))
        return jsonify({
            "success": True,
            "tv_ip": tv_ip,
            "stream_url": stream_url,
            "message": "Stream an Apple TV gesendet"
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)
