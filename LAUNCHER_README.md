# 🚪 Eden Launcher - Start Eden with One Double-Click

## Quick Start

**Windows Users:**
- Double-click `Eden.bat` (easiest)
- Or double-click `Eden.ps1`
- Or double-click `eden_start.py` (if Python is associated)

**Mac/Linux Users:**
- Double-click `eden_start.py`
- Or run `python eden_start.py` in terminal

## What Happens

When you double-click:

1. 🌱 **Eden MCP Hub starts** - Core server with all engines
2. 🔌 **Local Event Gateway spins up** - WebSocket server on ws://127.0.0.1:8765  
3. 🧠 **Sovereign engines boot-wire** - All engines connect via event bus
4. 📝 **Chronicler agent connects** - Starts observing and remembering
5. ✨ **Eden is LIVE** - Event nervous system breathing

## What You'll See

```
🌱 Eden System Starting...
==================================================
[Eden] Starting MCP Hub...
[Eden] Starting Chronicler...

🌟 Eden is ONLINE
🧠 Event nervous system active
🔌 Local Event Gateway listening on ws://127.0.0.1:8765
📝 Chronicler observing and remembering

[Eden] Close this window to stop everything.
```

## Stop Eden

Just close the window or press `Ctrl+C`

## Requirements

- Python 3.7+ installed
- All dependencies from `requirements.txt`

## Optional: Desktop Shortcut

1. Right-click `eden_start.py` → Create shortcut
2. Rename shortcut to "Eden"
3. Right-click shortcut → Properties → Change Icon
4. Choose an Eden-ish icon 🌱

## Next Steps

Once Eden is running:

- **Connect MCP clients** to the hub
- **Watch the Chronicler** add memories to `context-window.json`
- **Create more agents** in the `agents/` folder
- **Build web interfaces** that connect to ws://127.0.0.1:8765

Eden is now a living local system you can start like Spotify! 🌟
