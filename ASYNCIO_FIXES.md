# AsyncIO Fixes for Eden Gateway

## 🐛 Problem
Local Event Gateway was trying to create asyncio tasks during engine boot, but no event loop was running yet, causing:
```
RuntimeError: no running event loop
RuntimeWarning: coroutine 'LocalEventGateway.start' was never awaited
```

## 🔧 Solution

### 1. Defer Gateway Startup
Instead of starting immediately during `on_boot()`, the gateway now:
- Stores hub reference
- Subscribes to events immediately
- Tries to start when async loop is available
- Uses threading to run gateway in separate async context

### 2. Thread-Based Gateway
```python
def run_gateway():
    asyncio.run(self._run_gateway())

thread = threading.Thread(target=run_gateway, daemon=True)
thread.start()
```

### 3. Pending Events Queue
Events that occur before gateway starts are stored in `_pending_events` and broadcasted when gateway is ready.

## ✅ Expected Behavior

1. **Engines boot** → No asyncio errors
2. **Gateway starts** → In background thread with own event loop
3. **WebSocket server** → Listens on ws://127.0.0.1:8765
4. **Events flow** → From Eden to agents seamlessly

## 🚀 Test Again

Double-click `Eden.bat` - should now start without:
- ✅ No RuntimeError
- ✅ No RuntimeWarning  
- ✅ Gateway listening on ws://127.0.0.1:8765
- ✅ Chronicler connecting successfully

Eden's event nervous system should be fully operational! 🌱✨
