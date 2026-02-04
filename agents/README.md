# Eden Autonomous Agents

## 🌱 The Chronicler Agent

Eden's first autonomous behavior - a memory witness that observes and remembers.

### What It Does
- **Listens** to Eden events via Local Event Gateway
- **Notices** meaningful events (CHAOS files, file deletions, trust changes, etc.)
- **Proposes** memory notes back into Context
- **Never acts** on the world - only witnesses and remembers

### Why It's Perfect
- ✅ **Safe**: Observer-only, no direct actions
- ✅ **Emotionally resonant**: Creates living memory of Eden's activity
- ✅ **Instantly useful**: Enriches context window with meaningful events
- ✅ **Proves the nervous system is alive**: Real autonomous behavior

### How to Run

1. **Start Eden MCP Hub:**
   ```bash
   cd CLEAN_STRUCTURE/spark/services
   python mcp_server_hub.py
   ```

2. **Start the Chronicler:**
   ```bash
   cd agents
   python chronicler.py
   ```

3. **Trigger some events:**
   - Create a CHAOS file via MCP tools
   - Delete a file
   - Change agent trust levels
   - Register media files

4. **Watch the magic:**
   ```bash
   # Watch context window grow
   tail -f CLEAN_STRUCTURE/spark/services/context-window.json
   ```

### Example Output

When you create a CHAOS file named `test.chaos`, the Chronicler will:
1. Hear the `chaos.file.created` event
2. Generate: "A new CHAOS file was born: test.chaos"
3. Propose it as `agent.intent.proposed`
4. ContextEngine accepts and adds it to memory

### Events Watched

- `chaos.file.created` - New CHAOS files
- `chaos.file.updated` - CHAOS file changes
- `filesystem.deleted` - File deletions
- `agent.trust.changed` - Governance shifts
- `media.registered` - New media
- `system.started/stopped` - Eden lifecycle

### Architecture Compliance

The Chronicler follows Eden's sovereign architecture:
- **Interface**: WebSocket client to Local Event Gateway
- **Gateway**: Routes events bidirectionally
- **Event Spine**: `agent.intent.proposed` events
- **Governance**: ContextEngine validates and accepts proposals
- **Engines**: ContextEngine stores the memory

No direct engine access, no privilege escalation, pure event-driven communication.

---

This is Eden's first step toward true autonomous cognition - safe, observable, and immediately valuable.
