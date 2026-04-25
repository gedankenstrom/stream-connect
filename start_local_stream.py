#!/usr/bin/env python3
"""
Startet Streamlink lokal und sendet den Stream an Apple TV (VLC).
"""
import subprocess
import sys
import time
import asyncio
import base64
import json
import struct
import random
import os

# Konfiguration
VENV_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "venv-local")
STREAMLINK_BIN = os.path.join(VENV_DIR, "bin", "streamlink")
STREAM_PORT = 8095
TV_IP = "192.168.25.20"
TV_PORT = 80

# Hole Channel aus Kommandozeile oder frage
if len(sys.argv) > 1:
    channel = sys.argv[1]
else:
    channel = input("Twitch-Kanal (z.B. fustler): ").strip()

if not channel:
    print("Kein Kanal angegeben!")
    sys.exit(1)

# Entferne twitch.tv/ Präfix falls vorhanden
channel = channel.replace("https://", "").replace("http://", "").replace("twitch.tv/", "").replace("www.twitch.tv/", "").strip("/")

stream_url = f"https://www.twitch.tv/{channel}"
print(f"[+] Starte Stream für: {channel}")
print(f"[+] Stream-URL: {stream_url}")
print(f"[+] Lokaler Port: {STREAM_PORT}")
print(f"[+] Apple TV: {TV_IP}")

# Starte Streamlink als Subprocess
cmd = [
    STREAMLINK_BIN,
    stream_url,
    "best",
    "--player-external-http",
    f"--player-external-http-port={STREAM_PORT}",
    "--twitch-low-latency",
    "--hls-live-edge", "2",
    "--retry-streams", "3",
    "--loglevel", "info"
]

# OAuth Token falls vorhanden
creds_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "tokens.db")
if os.path.exists(creds_file):
    try:
        import sqlite3
        conn = sqlite3.connect(creds_file)
        c = conn.cursor()
        c.execute("SELECT token FROM tokens WHERE id = 1")
        row = c.fetchone()
        if row and row[0]:
            token = row[0].replace("oauth:", "")
            cmd.extend(["--twitch-api-header", f"Authorization=OAuth {token}"])
            print("[+] Verwende gespeicherten OAuth-Token")
        conn.close()
    except Exception as e:
        print(f"[-] Token-Fehler: {e}")

print(f"[+] Streamlink startet...")
process = subprocess.Popen(
    cmd,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    bufsize=1
)

# Warte kurz bis Streamlink den Port öffnet
print("[+] Warte 5 Sekunden auf Streamlink...")
time.sleep(5)

# Prüfe ob Port erreichbar
import socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
result = sock.connect_ex(("127.0.0.1", STREAM_PORT))
sock.close()

if result != 0:
    print("[-] FEHLER: Streamlink konnte Port nicht öffnen!")
    process.terminate()
    sys.exit(1)

local_stream = f"http://192.168.25.140:{STREAM_PORT}/{channel}"
print(f"[+] Stream läuft auf {local_stream}")

# Sende an Apple TV
async def send_to_apple_tv():
    # WebSocket handshake
    key = base64.b64encode(bytes(random.getrandbits(8) for _ in range(16))).decode()
    
    request = (
        f"GET / HTTP/1.1\r\n"
        f"Host: {TV_IP}\r\n"
        f"Upgrade: websocket\r\n"
        f"Connection: Upgrade\r\n"
        f"Sec-WebSocket-Key: {key}\r\n"
        f"Sec-WebSocket-Version: 13\r\n"
        f"\r\n"
    )
    
    reader, writer = await asyncio.open_connection(TV_IP, TV_PORT)
    writer.write(request.encode())
    await writer.drain()
    
    response = b""
    while b"\r\n\r\n" not in response:
        response += await reader.read(1)
    
    # Build WebSocket text frame
    message = json.dumps({"type": "openURL", "url": local_stream})
    payload = message.encode('utf-8')
    
    frame = bytearray()
    frame.append(0x81)
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
            print(f"[+] Apple TV Antwort: {len(data)} bytes")
    except asyncio.TimeoutError:
        pass
    
    writer.close()
    await writer.wait_closed()
    print(f"[+] Stream an Apple TV gesendet: {local_stream}")

asyncio.run(send_to_apple_tv())

print("\n[+] Stream läuft! Drücke STRG+C zum Beenden.")
print("[+] Streamlink Output:")

try:
    for line in process.stdout:
        print(f"  | {line.rstrip()}")
except KeyboardInterrupt:
    print("\n[+] Beende Stream...")
    process.terminate()
    process.wait()
    print("[+] Fertig.")
