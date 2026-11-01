FROM python:3.11-slim

WORKDIR /app

# Installiere Streamlink (Version wird automatisch aktualisiert)
RUN pip install --no-cache-dir streamlink==8.4.0

# Kopiere Controller-Skripte
COPY stream_controller.py stream_controller_cq.py ./

# Entrypoint erstellt .streamlinkrc aus ENV
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
