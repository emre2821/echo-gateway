Title: Eden Nerve Layer Integration (Cross-System Wiring)

Objective:
Connect all sovereign engines (CHAOS, Context, Filesystem, Media, Permissions, Agent Trust, Utility) into a message-driven nervous system using the Event Spine. Extend the same wiring so the DCA, AoE, CHAOS Backbone, and EdenOS can participate without entanglement.

Phase A: Add the Nerve Hooks to Every Engine

Each engine must implement:

def on_boot(self, hub):
    self.hub = hub
    hub.event_bus.subscribe("system_event", self.handle_event)

def handle_event(self, event: dict):
    pass


No engine may import another engine.

Phase B: Hub Emits Reality

In hub-core.py, add:

def emit(event_type: str, payload: dict):
    event_bus.emit("system_event", {
        "type": event_type,
        "payload": payload
    })


This is the only broadcast path.

Phase C: Engines Announce Themselves
Replace internal side-effects with signals:

CHAOS:
- emit CHAOS_FILE_CREATED, UPDATED, ANALYZED

Context:
- emit CONTEXT_ENTRY_ADDED

Filesystem:
- emit FS_WRITTEN, FS_DELETED

Media:
- emit MEDIA_REGISTERED

Agent Trust:
- emit AGENT_TRUST_CHANGED, AGENT_REGISTERED

Permissions:
- emit PERMISSION_GRANTED, DENIED

Utility:
- emit ARCHIVE_CREATED, CHECKSUM_CALCULATED

Phase D: Cross-Reactivity (Examples)
- When CHAOS_FILE_CREATED → Context auto-adds a memory entry.
- When FS_DELETED → Context logs a loss event.
- When AGENT_TRUST_CHANGED → Context records governance shift.
- When MEDIA_REGISTERED → CHAOS may tag or link symbolically.

Phase E: Backbone Integration

Create a Backbone Adapter that listens and emits:
- DCA events → DCA_EVENT
- AoE lifecycle events → AOE_EVENT
- CHAOS backbone pings → CHAOS_BACKBONE_PING
- These must flow through the same event bus, not direct calls.

Phase F: Auto-Wiring at Boot

In mcp-server-hub.py:

for engine in [
    permissions_engine, context_engine, filesystem_engine,
    media_engine, agent_trust_engine, utility_engine, chaos_engine
]:
    engine.on_boot(hub_core)

Acceptance Criteria
- No engine imports another.
- All cross-system effects occur via events.
- Removing any engine does not crash the hub.
- DCA/AoE/Backbone can emit and receive events without touching internals.