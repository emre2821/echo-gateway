#!/usr/bin/env python3
"""
Local Event Gateway (LEG)
Bridges Eden's internal event bus <-> external local agents via WebSocket.

- Subscribes to hub.event_bus "system_event" and broadcasts to all connected clients.
- Accepts messages from agents and re-emits into Eden via hub.emit(...).
- Local-only by default (127.0.0.1).
"""

import asyncio
import json
from typing import Any, Dict, Set, Optional

try:
    import websockets
except ImportError as e:
    raise SystemExit(
        "Missing dependency: websockets\n"
        "Install with: pip install websockets\n"
    ) from e


class LocalEventGateway:
    def __init__(self, host: str = "127.0.0.1", port: int = 8765):
        self.host = host
        self.port = port
        self.hub: Optional[Dict[str, Any]] = None
        self.clients: Set[Any] = set()
        self._server = None

    # ----- Eden nerve hooks -----
    def on_boot(self, hub):
        """
        hub is expected to look like:
        {
          "event_bus": <EventBus>,
          "emit": <callable>,
        }
        """
        self.hub = hub
        hub.event_bus.subscribe("system_event", self.handle_event)
        
        # Store hub for later use when server starts
        self._hub = hub
        self._started = False
        
        # Try to start immediately if possible
        self.start_when_ready()

    def start_when_ready(self):
        """Start the gateway when async loop is available."""
        if not self._started:
            import threading
            import time
            
            def run_gateway():
                try:
                    print("[LocalEventGateway] Starting WebSocket server in background thread...")
                    # Create our own event loop for this thread
                    asyncio.run(self._run_gateway())
                    print("[LocalEventGateway] WebSocket server started successfully")
                except Exception as e:
                    print(f"[LocalEventGateway] Error starting gateway: {e}")
            
            thread = threading.Thread(target=run_gateway, daemon=True)
            thread.start()
            self._started = True
            
            # Give the server a moment to start
            time.sleep(2)
            
            # Announce gateway online
            self._hub.emit("system.started", {
                "component": "local_event_gateway",
                "host": self.host,
                "port": self.port
            })
            print(f"[LocalEventGateway] Gateway startup initiated on ws://{self.host}:{self.port}")

    async def _run_gateway(self):
        """Run the gateway in its own async context."""
        await self.start()
        
        # Broadcast any pending events that occurred before startup
        if hasattr(self, '_pending_events'):
            for event in self._pending_events:
                await self.broadcast(event)
            self._pending_events = []

    def handle_event(self, event: dict):
        """Receive Eden events and broadcast them out to agents."""
        # Store event for broadcasting when gateway is running
        if hasattr(self, '_pending_events'):
            self._pending_events.append(event)
        else:
            self._pending_events = [event]
        
        # Try to broadcast if gateway is running
        if self._started:
            try:
                asyncio.get_running_loop()
                asyncio.create_task(self.broadcast(event))
            except RuntimeError:
                pass  # No event loop, will broadcast later

    # ----- WebSocket server -----
    async def start(self):
        self._server = await websockets.serve(self._handler, self.host, self.port)
        print(f"[LocalEventGateway] listening on ws://{self.host}:{self.port}")

    async def _handler(self, websocket):
        self.clients.add(websocket)
        try:
            # handshake banner
            await websocket.send(json.dumps({
                "type": "gateway.hello",
                "payload": {"status": "connected"}
            }))

            async for message in websocket:
                await self._handle_agent_message(websocket, message)

        finally:
            self.clients.discard(websocket)

    async def _handle_agent_message(self, websocket, raw: str):
        """
        Expected agent message format:
        {
          "type": "agent.intent.proposed",
          "payload": {...},
          "agent": {"id": "...", "name": "..."}   # optional but recommended
        }
        """
        try:
            data = json.loads(raw)
        except Exception:
            await websocket.send(json.dumps({
                "type": "gateway.error",
                "payload": {"error": "Invalid JSON"}
            }))
            return

        event_type = data.get("type")
        payload = data.get("payload", {})
        agent = data.get("agent", {})

        if not event_type:
            await websocket.send(json.dumps({
                "type": "gateway.error",
                "payload": {"error": "Missing 'type' field"}
            }))
            return

        # Re-emit into Eden
        if self.hub:
            # You can enforce policy here later (or inside AgentTrust/Permissions)
            self.hub.emit(event_type, {
                **payload,
                "_agent": agent
            })

        await websocket.send(json.dumps({
            "type": "gateway.ack",
            "payload": {"received": event_type}
        }))

    async def broadcast(self, event: dict):
        """Broadcast an Eden event to all connected agent clients."""
        if not self.clients:
            return

        msg = json.dumps(event, ensure_ascii=False)
        dead = set()

        for ws in self.clients:
            try:
                await ws.send(msg)
            except Exception:
                dead.add(ws)

        for ws in dead:
            self.clients.discard(ws)


# singleton-style instance (like your other engines)
local_event_gateway = LocalEventGateway()
