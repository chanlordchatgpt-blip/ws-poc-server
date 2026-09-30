import asyncio
import websockets
import json
from datetime import datetime
from llm import chat_completion, SYSTEM_PROMPT

# ─── In-memory chat history per client ────────────────────────
# Key:   client id (int)
# Value: list of message dicts [{role, content}, ...]
chat_histories = {}

# ──────────────────────────────────────────────────────────────


def log(msg: str):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")


async def handle_client(websocket):
    """
    Handle individual WebSocket client.

    Message protocol (JSON):
    
    Client → Server:
    {
        "type": "chat",
        "text": "user message here"
    }
    or for clearing history:
    {
        "type": "clear"
    }

    Server → Client:
    {
        "type": "response",
        "text": "assistant reply here"
    }
    or on error:
    {
        "type": "error",
        "text": "error message here"
    }
    or status:
    {
        "type": "status",
        "text": "status message here"
    }
    """

    client_id = id(websocket)
    log(f"Client connected: {client_id}")

    # Initialize empty chat history for this client
    chat_histories[client_id] = []

    # Send welcome message
    await send_message(websocket, "status", "Connected! Send a message to chat with the assistant.")

    try:
        async for raw_message in websocket:
            log(f"Received from {client_id}: {raw_message}")

            # ── Parse incoming message ──────────────────────────
            try:
                data = json.loads(raw_message)
            except json.JSONDecodeError:
                # If not JSON, treat raw text as a chat message
                # This keeps backward compatibility with your
                # existing plain-text echo test
                data = {"type": "chat", "text": raw_message}

            msg_type = data.get("type", "chat")
            msg_text = data.get("text", "").strip()

            # ── Handle message types ────────────────────────────

            if msg_type == "clear":
                # Clear chat history for this client
                chat_histories[client_id] = []
                await send_message(websocket, "status", "Chat history cleared.")
                log(f"History cleared for {client_id}")
                continue

            if msg_type == "chat" and msg_text:
                # Add user message to history
                chat_histories[client_id].append({
                    "role"   : "user",
                    "content": msg_text
                })

                # Build full message list with system prompt
                messages = [
                    {"role": "system", "content": SYSTEM_PROMPT}
                ] + chat_histories[client_id]

                # Send "thinking" status to widget
                await send_message(websocket, "status", "Thinking...")

                # ── Call LLM ────────────────────────────────────
                log(f"Calling LLM for {client_id}...")
                response_text = chat_completion(messages)
                log(f"LLM response for {client_id}: {response_text[:80]}...")

                # Add assistant response to history
                # (only if not an error)
                if not response_text.startswith("Error:"):
                    chat_histories[client_id].append({
                        "role"   : "assistant",
                        "content": response_text
                    })

                # Send response back to widget
                msg_type_out = "error" if response_text.startswith("Error:") else "response"
                await send_message(websocket, msg_type_out, response_text)

    except websockets.exceptions.ConnectionClosedOK:
        log(f"Client {client_id} disconnected cleanly")

    except websockets.exceptions.ConnectionClosedError as e:
        log(f"Client {client_id} disconnected with error: {e}")

    finally:
        # Clean up history when client disconnects
        chat_histories.pop(client_id, None)
        log(f"Cleaned up history for {client_id}")


async def send_message(websocket, msg_type: str, text: str):
    """Helper to send structured JSON message to client."""
    payload = json.dumps({
        "type": msg_type,
        "text": text
    })
    await websocket.send(payload)


async def main():
    import os
    port = int(os.environ.get("PORT", 8765))
    host = "0.0.0.0"
    log(f"Starting WebSocket server on {host}:{port}")

    async with websockets.serve(handle_client, host, port):
        log("Server running. Waiting for connections...")
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())