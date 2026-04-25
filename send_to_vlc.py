#!/usr/bin/env python3
import asyncio
import hashlib
import base64
import json
import struct
import random

async def send_url_to_vlc(tv_ip, stream_url):
    # WebSocket handshake
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
    
    # Read response until \r\n\r\n
    response = b""
    while b"\r\n\r\n" not in response:
        response += await reader.read(1)
    
    print(f"Handshake response: {response.decode().split(chr(10))[0]}")
    
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
    
    # Read response (optional)
    try:
        data = await asyncio.wait_for(reader.read(1024), timeout=2.0)
        if data:
            print(f"Response received: {len(data)} bytes")
    except asyncio.TimeoutError:
        pass
    
    writer.close()
    await writer.wait_closed()
    print(f"Sent to VLC on {tv_ip}: {stream_url}")

if __name__ == "__main__":
    asyncio.run(send_url_to_vlc("192.168.25.20", "http://192.168.25.101:8095/fustler"))
