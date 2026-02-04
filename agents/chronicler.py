#!/usr/bin/env python3
"""
Chronicler Agent
Listens to Eden events and proposes memory notes.
"""

import asyncio
import json
import time

try:
    import websockets
except ImportError as e:
    raise SystemExit("Install websockets: pip install websockets") from e

AGENT = {
    "id": "chron-001",
    "name": "Chronicler",
    "role": "memory_witness",
    "trust_hint": "observer"
}

WATCH = {
    "chaos.file.created": "A new CHAOS file was born: {filename}",
    "chaos.file.updated": "A CHAOS file was changed: {filename}",
    "filesystem.deleted": "A file was removed: {path}",
    "agent.trust.changed": "Governance shifted: {agent_id} → {level}",
    "media.registered": "New media registered: {file_path}",
    "system.started": "Eden woke up.",
    "system.stopped": "Eden went to sleep."
}

async def run():
    uri = "ws://127.0.0.1:8765"
    
    # Retry connection with backoff
    max_retries = 5
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            async with websockets.connect(uri) as ws:
                print("[Chronicler] connected")
                
                async for msg in ws:
                    event = json.loads(msg)
                    etype = event.get("type")
                    payload = event.get("payload", {})

                    if etype in WATCH:
                        template = WATCH[etype]
                        try:
                            text = template.format(**payload)
                        except Exception:
                            text = template

                        proposal = {
                            "type": "agent.intent.proposed",
                            "agent": AGENT,
                            "payload": {
                                "intent": "add_context_note",
                                "text": text,
                                "source": "chronicler",
                                "ts": time.time()
                            }
                        }

                        await ws.send(json.dumps(proposal))
                        print(f"[Chronicler] proposed: {text}")
                break  # Success, exit retry loop
                
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"[Chronicler] Connection attempt {attempt + 1} failed: {e}")
                print(f"[Chronicler] Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
                retry_delay *= 1.5  # Exponential backoff
            else:
                print(f"[Chronicler] Failed to connect after {max_retries} attempts: {e}")
                break

if __name__ == "__main__":
    asyncio.run(run())
