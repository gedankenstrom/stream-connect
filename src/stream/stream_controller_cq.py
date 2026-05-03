import subprocess
import sys
import time
import re
import threading
import socket
import os

# Parameter aus Umgebungsvariablen
channel = os.environ.get("CHANNEL", sys.argv[1] if len(sys.argv) > 1 else "")
port = int(os.environ.get("PORT", sys.argv[2] if len(sys.argv) > 2 else "8090"))
oauth_token = os.environ.get("TWITCH_OAUTH_TOKEN", "")

# Grundeinstellungen
default_quality = "best"  # normale Qualität
current_quality = default_quality
streamlink_process = None
monitor_thread = None
restart_needed = False
ad_active = False  # erkennt, ob gerade Werbung läuft
advert_re = re.compile(r"Detected advertisement break of (\d+) seconds")


def wait_for_port_release(port, timeout=5):
    start = time.time()
    while time.time() - start < timeout:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('127.0.0.1', port)) != 0:
                return True
        time.sleep(0.1)
    return False


def start_stream(quality):
    global streamlink_process, monitor_thread

    if not wait_for_port_release(port, timeout=5):
        print(f"[controller] Warnung: Port {port} immer noch belegt, warte 2 Sekunden ...", flush=True)
        time.sleep(2)
        if not wait_for_port_release(port, timeout=5):
            print(f"[controller] Fehler: Port {port} weiterhin belegt, Neustart überspringen!", flush=True)
            return None

    cmd = [
        "streamlink",
        f"https://www.twitch.tv/{channel}",
        quality,
        "--player-external-http",
        f"--player-external-http-port={port}",
        "--hls-live-edge", "500",
        "--retry-open", "3",
        "--retry-streams", "1",
        "--loglevel", "info"
    ]

    # OAuth-Token hinzufügen falls vorhanden
    if oauth_token:
        cmd.append("--twitch-api-header")
        cmd.append(f"Authorization=OAuth {oauth_token.replace('oauth:', '')}")
        print(f"[controller] Verwende OAuth-Token für {channel}", flush=True)

    print(f"[controller] Starte Streamlink mit Qualität: {quality}, Port: {port}", flush=True)

    streamlink_process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=sys.stderr,
        text=True,
        bufsize=1,
        universal_newlines=True
    )

    monitor_thread = threading.Thread(target=monitor_stream_output, daemon=True)
    monitor_thread.start()
    return streamlink_process


def monitor_stream_output():
    """Überwacht Streamlink-Ausgabe, erkennt Werbung ≥60s und passt die Qualität an."""
    global streamlink_process, restart_needed, current_quality, ad_active
    if not streamlink_process or not streamlink_process.stdout:
        return

    try:
        for line in iter(streamlink_process.stdout.readline, ""):
            line = line.strip()
            if not line:
                continue
            print(line, flush=True)

            # Werbung erkannt
            m = advert_re.search(line)
            if m:
                duration = int(m.group(1))
                if duration >= 60:  # nur Werbung ab 60 Sekunden
                    if not ad_active:  # Werbung startet jetzt
                        print(f"[controller] Werbung erkannt ({duration}s) → Qualität auf 360p wechseln!", flush=True)
                        current_quality = "360p"
                        restart_needed = True
                        ad_active = True
                else:
                    print(f"[controller] Werbung erkannt ({duration}s) → Ignoriere (<60s)", flush=True)
            else:
                # Werbung vorbei → ggf. auf best zurücksetzen
                if ad_active:
                    print("[controller] Werbeblock beendet → Qualität zurück auf best", flush=True)
                    current_quality = default_quality
                    restart_needed = True
                    ad_active = False

    finally:
        if streamlink_process and streamlink_process.stdout:
            streamlink_process.stdout.close()


def stop_stream():
    global streamlink_process, monitor_thread
    if streamlink_process and streamlink_process.poll() is None:
        print("[controller] Beende alten Streamlink-Prozess ...", flush=True)
        streamlink_process.terminate()
        try:
            streamlink_process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            print("[controller] Erzwinge Kill, Prozess reagiert nicht ...", flush=True)
            streamlink_process.kill()
            streamlink_process.wait()

        if monitor_thread and monitor_thread.is_alive() and threading.current_thread() != monitor_thread:
            monitor_thread.join(timeout=1)

        if streamlink_process.stdout:
            streamlink_process.stdout.close()

        time.sleep(1)
        if not wait_for_port_release(port, timeout=5):
            print(f"[controller] Warnung: Port {port} immer noch belegt!", flush=True)

        streamlink_process = None
        print("[controller] Streamlink gestoppt.", flush=True)


def main():
    global streamlink_process, restart_needed, current_quality
    print(f"[controller] Starte Twitch-Stream-Controller für Kanal: {channel}", flush=True)
    print(f"[controller] HTTP-Port: {port}", flush=True)
    print(f"[controller] Anfangsqualität: {current_quality}", flush=True)

    streamlink_process = start_stream(current_quality)

    try:
        while True:
            # Neustart erforderlich oder Prozess beendet
            if restart_needed or (streamlink_process and streamlink_process.poll() is not None):
                restart_needed = False

                # Stream stoppen
                stop_stream()

                # Sicherstellen, dass Port frei ist
                for _ in range(10):
                    if wait_for_port_release(port, timeout=1):
                        break
                    time.sleep(0.5)
                else:
                    print(f"[controller] Fehler: Port {port} immer noch belegt, Neustart überspringen!", flush=True)
                    continue

                # Stream neu starten mit aktueller Qualität
                streamlink_process = start_stream(current_quality)

                # Nach Neustart wieder default_quality setzen, falls keine Werbung
                if not ad_active:
                    current_quality = default_quality

            time.sleep(1)
    except KeyboardInterrupt:
        print("[controller] Manuell beendet.", flush=True)
        stop_stream()
    except Exception as e:
        print(f"[controller] Fehler: {e}", flush=True)
        stop_stream()
    finally:
        stop_stream()
        print("[controller] Controller beendet.", flush=True)


if __name__ == "__main__":
    main()
