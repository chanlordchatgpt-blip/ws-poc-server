import asyncio
import websockets
import json
from datetime import datetime

# Store connected clients (useful for future broadcast features)
connected_clients = set()

async def handle_client(websocket):
    """
    Handle individual WebSocket client connection.
    Currently: echo server
    Future: replace echo with LLM call
    """
    client_id = id(websocket)
    connected_clients.add(websocket)
    print(f"[{datetime.now()}] Client connected: {client_id}")
    print(f"[{datetime.now()}] Total clients: {len(connected_clients)}")

    try:
        async for message in websocket:
            print(f"[{datetime.now()}] Received from {client_id}: {message}")

            # ─── ECHO LOGIC (replace this block with LLM call later) ───
            response = message
            # ─── Future LLM block will look like: ───────────────────────
            # response = await call_llm(message)
            # ────────────────────────────────────────────────────────────

            await websocket.send(response)
            print(f"[{datetime.now()}] Sent back: {response}")

    except websockets.exceptions.ConnectionClosedOK:
        print(f"[{datetime.now()}] Client {client_id} disconnected cleanly")
    except websockets.exceptions.ConnectionClosedError as e:
        print(f"[{datetime.now()}] Client {client_id} disconnected with error: {e}")
    finally:
        connected_clients.discard(websocket)
        print(f"[{datetime.now()}] Total clients remaining: {len(connected_clients)}")


async def main():
    """
    Start WebSocket server.
    Host 0.0.0.0 is required for cloud deployment (Render/Railway).
    Port is read from environment variable for cloud compatibility.
    """
    import os
    port = int(os.environ.get("PORT", 8765))
    host = "0.0.0.0"

    print(f"[{datetime.now()}] Starting WebSocket server on {host}:{port}")

    async with websockets.serve(handle_client, host, port):
        print(f"[{datetime.now()}] Server running. Waiting for connections...")
        await asyncio.Future()  # Run forever


if __name__ == "__main__":
    asyncio.run(main())