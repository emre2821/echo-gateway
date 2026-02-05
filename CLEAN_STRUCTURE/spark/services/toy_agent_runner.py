#!/usr/bin/env python3
"""
Toy Agent Runner
Connects to Local Event Gateway, listens for events, and responds with a simple intent.
"""

import asyncio
import json

try:
    import websockets
except ImportError as e:
    raise SystemExit("Install websockets: pip install websockets") from e


AGENT = {"id": "toy-001", "name": "ToyAgent", "type": "local"}


async def run():
    uri = "ws://127.0.0.1:8765"
    async with websockets.connect(uri) as ws:
        print("[ToyAgent] connected")

        async for msg in ws:
            event = json.loads(msg)
            etype = event.get("type")
            payload = event.get("payload", {})

            print(f"[ToyAgent] heard: {etype}")

            # Example: when CHAOS file created, propose a memory entry
            if etype == "chaos.file.created":
                filename = payload.get("filename")
                await ws.send(json.dumps({
                    "type": "agent.intent.proposed",
                    "agent": AGENT,
                    "payload": {
                        "intent": "summarize_new_chaos_file",
                        "filename": filename,
                        "note": "I can analyze/summarize this file if allowed."
                    }
                }))


if __name__ == "__main__":
    asyncio.run(run())
