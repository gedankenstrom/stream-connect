from flask import Flask, render_template, request, jsonify
import docker
import socket
import os
import sqlite3
import secrets
import requests

app = Flask(__name__)
client = docker.from_env()

# Konfiguration
DATA_DIR = os.environ.get("DATA_DIR", "/data")
DB_PATH = os.path.join(DATA_DIR, "tokens.db")
SPORT_PORTS = list(range(8090, 8111))

def check_twitch_live(channel):
    """Prüft ob ein Twitch-Kanal aktuell live ist via Twitch API."""
    try:
        # Einfacher Check: Twitch URL mit HEAD request
        response = requests.head(
            f"https://www.twitch.tv/{channel}",
            timeout=5,
            allow_redirects=True
        )
        # Prüfe auf Live-Indikatoren im Content (vereinfacht)
        return None  # Zunächst unbekannt, da komplexer Check nötig
    except:
        return None

def init_db():
    """Initialisiert SQLite-Datenbank für OAuth-Tokens."""
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS tokens (
        id INTEGER PRIMARY KEY,
        token TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    conn.commit()
    conn.close()

def save_token(token):
    """Speichert OAuth-Token (einfache Verschlüsselung via XOR mit zufälligem Key)."""
    # Auto-add oauth: prefix if missing
    token = token.strip()
    if token and not token.startswith('oauth:'):
        token = 'oauth:' + token
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM tokens")
    key = secrets.token_hex(32)
    obfuscated = ''.join(chr(ord(c) ^ ord(k)) for c, k in zip(token, key * (len(token) // len(key) + 1)))
    c.execute("INSERT INTO tokens (token) VALUES (?)", [key + obfuscated])
    conn.commit()
    conn.close()

def get_token():
    """Liest OAuth-Token zurück."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT token FROM tokens ORDER BY id DESC LIMIT 1")
    row = c.fetchone()
    conn.close()
    if not row:
        return None
    data = row[0]
    key = data[:64]
    obfuscated = data[64:]
    return ''.join(chr(ord(c) ^ ord(k)) for c, k in zip(obfuscated, key * (len(obfuscated) // len(key) + 1)))

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

        # Prüfe ob Stream wirklich live (via Logs)
        is_live = False
        if c.status == "running":
            try:
                # Container-Logs der letzten 10 Sekunden prüfen
                logs = c.logs(tail=5, timestamps=False).decode('utf-8', errors='ignore')
                # Wenn Stream Daten liefert, sieht man das in den Logs
                if '[cli][info] Opening stream:' in logs or 'Starting server' in logs:
                    is_live = True
            except:
                is_live = False

        stream_data.append({
            "name": c.name,
            "channel": name,
            "status": c.status,
            "port": host_port,
            "controller": controller,
            "is_live": is_live,
        })

    available_ports = [p for p in SPORT_PORTS if p not in used_ports]
    return stream_data, available_ports

@app.route('/')
def index():
    streams, available_ports = get_streams()
    token = get_token()
    return render_template(
        'index.html',
        streams=streams,
        host_ip=get_host_ip(),
        sport_ports=available_ports,
        has_token=bool(token),
        token_preview=token[:10] + "..." if token else None
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
    """Speichert OAuth-Token aus Web-UI (oder löscht bei leerem Feld)."""
    token = request.form.get('token', '').strip()
    
    if not token:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("DELETE FROM tokens")
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "Token gelöscht"})
    
    if not token.startswith('oauth:'):
        return jsonify({"error": "Token muss mit 'oauth:' beginnen"}), 400
    
    save_token(token)
    return jsonify({"success": True})

@app.route('/start', methods=['POST'])
def start():
    """Startet einen neuen Stream-Container."""
    channel = request.form.get('channel', '').strip()
    port = request.form.get('port', '').strip()
    controller_type = request.form.get('controller_type', 'standard')

    if not channel:
        return jsonify({"error": "Kanal darf nicht leer sein."}), 400
        
    if not port or not port.isdigit():
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

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)
