FROM python:3.11-slim

WORKDIR /app

# Installiere Streamlink
RUN pip install --no-cache-dir streamlink

# Kopiere Controller-Skripte
COPY stream_controller.py stream_controller_cq.py ./

# Entrypoint erstellt .streamlinkrc aus ENV
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
