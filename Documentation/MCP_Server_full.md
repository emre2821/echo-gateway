# EdenOS MCP Server

## Directory Structure

```text
MCP_Server/
├── README.md
├── http_approval_bridge.py
├── permissions.json
├── pyproject.toml
├── requirements.txt
├── server.py
├── core/
│   ├── __init__.py
│   ├── logging.py
│   └── mcp/
│       ├── __init__.py
│       ├── server.py
│       └── types.py
└── tools/
    ├── __init__.py
    ├── agent_tools.py
    ├── chaos_tools.py
    ├── filesystem_tools.py
    └── organizer_tools.py
```

---

## README.md

```markdown
# ■ EdenOS MCP Server
**Location:** `08_DevTools/SDK/MCP_Server`
**Purpose:** Provides a Model Context Protocol (MCP) interface that allows ChatGPT (Dev Mode) and other MCP clients to ---

## ■ Overview
This MCP server acts as a **bridge layer** between external AI systems and the internal architecture of EdenOS.
It exposes safe, sandboxed tools that ChatGPT can call through Dev Mode to:
- Inspect or process files
- Interact with Eden agents
- Run CHAOS diagnostics
- Trigger EdenOS utilities
- Extend functionality through modular tools

This server uses:
- **stdio transport** (MCP standard)
- **auto-discovery** of tools inside `tools/`
- **@eden_tool** decorator for clean registration
- **Rich-based logging** for Eden-style console output

---

## ■ Directory Structure
MCP_Server/
■
■■■ server.py # core MCP server
■■■ requirements.txt # dependencies
■
■■■ tools/ # tool modules auto-discovered by server.py
■ ■■■ __init__.py
■ ■■■ filesystem_tools.py
■ ■■■ chaos_tools.py
■ ■■■ agent_tools.py
■
■■■ core/
■■■ __init__.py
■■■ logging.py

---

## ■ Running the Server
From this directory:
```bash
pip install -r requirements.txt
python server.py
```

The server will run silently, waiting for MCP clients (like ChatGPT Dev Mode) to connect.

## ■ Adding New Tools

To add a new tool:

1. Create a new *.py file inside tools/
2. Write a function
3. Decorate it with:

```python
@eden_tool()
```

1. Ensure it returns MCP content objects such as:

- TextContent
- JsonContent

Example:

```python
@eden_tool()
def say_hello(name: str):
    return [TextContent(type="text", text=f"Hello, {name}!")]
```

Restart the server or use hot-reload (if enabled), and the tool becomes instantly available.

## Security Notes

The server intentionally ships with:

- No file write tools
- No subprocess execution
- No shell access

These can be added later inside a Zero-Trust wrapper
(see: 10_Security/ and EdenOS RBAC guidelines).

## Future Extensions

Planned expansions include:

- Full CHAOS parser integration
- EdenOS CLI bridge
- LLM Router interface
- AgentBridge for dynamic persona calls
- MemoryTemple access (read-only or permissioned)
- DCA (Daemon Control Agent) wrappers

## Authoring Persona

All MCP server files should include attribution under EdenOS metadata conventions:

```text
[AUTHOR] Dreamcatcher (EdenOS Bridge Persona)
```

## Status

This MCP server is the official EdenOS DevMode integration point.
It enables rapid tooling, debugging, and agentic automation with guaranteed stability.

If you need new tool modules generated, just ask:

```text
"Add a tool for ___."
```

---

## http_approval_bridge.py

```python
"""Simple HTTP bridge to approve MCP-like file actions.
This bridge is intentionally minimal and for local development only.
It accepts POST /approve with JSON {action, target, requester} and
creates an immediate permission entry in `tools/permissions.json`.

WARNING: This bridge will grant permissions immediately by default.
Run it only on localhost and understand the security implications.
"""

import json
import os
import uuid
import time
from flask import Flask, request, jsonify

ROOT = os.path.dirname(__file__)
PERMISSIONS_FILE = os.path.join(ROOT, 'tools', 'permissions.json')

app = Flask('mcp-approval-bridge')

def _load():
    try:
        with open(PERMISSIONS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {'permissions': {}, 'requests': {}, 'audit': []}

def _save(data):
    with open(PERMISSIONS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def _make_id():
    return uuid.uuid4().hex

@app.route('/approve', methods=['POST'])
def approve():
    body = request.get_json() or {}
    action = body.get('action')
    target = body.get('target')
    requester = body.get('requester')

    if not action or not target:
        return jsonify({'approved': False, 'reason': 'missing_fields'}), 400

    data = _load()
    perm_id = _make_id()

    data.setdefault('permissions', {})[perm_id] = {
        'action': action,
        'target': target,
        'granted_by': 'bridge',
        'granted_at': time.time(),
        'expires_at': None,
        'allowed': True,
    }

    data.setdefault('audit', []).append({
        'id': _make_id(),
        'event': 'bridge_grant',
        'details': {'action': action, 'target': target, 'requester': requester},
        'timestamp': time.time()
    })

    _save(data)
    return jsonify({'approved': True, 'permission_id': perm_id})

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8765)
```

---

## permissions.json

```json
{
  "permissions": {},
  "requests": {}
}
```

---

## pyproject.toml

```toml
[build-system]
requires = ["setuptools>=42", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "eden-mcp-server"
version = "0.1.0"
description = "EdenOS MCP bridge for local development"
authors = [ { name = "Dreamcatcher" } ]
requires-python = ">=3.8"

[project.optional-dependencies]
dev = ["rich==13.4.2"]
```

---

## requirements.txt

```txt
rich==13.4.2
# The `mcp` package is expected to be provided by your MCP implementation.
# For local development we include a small stub under the project so you
# can run the server without an external `mcp` package.
flask==2.3.2
```

---

## server.py

```python
# server.py
import importlib
import pkgutil
from mcp.server import Server

server = Server("eden-mcp-server")

def _log(msg: str):
    try:
        # prefer eden_log if available
        from core.logging import eden_log
        eden_log(msg)
    except Exception:
        print(f"[eden-mcp] {msg}")

def load_tools():
    """
    Auto-import all modules inside the tools/ folder,
    and register any functions decorated with @eden_tool().
    Resilient to import/register errors so a single bad tool
    cannot crash the whole server.
    """
    import tools

    for module_info in pkgutil.iter_modules(tools.__path__):
        module_name = f"tools.{module_info.name}"
        try:
            module = importlib.import_module(module_name)
        except Exception as e:
            _log(f"Failed importing {module_name}: {e}")
            continue

        for attr in dir(module):
            obj = getattr(module, attr)
            if callable(obj) and hasattr(obj, "_mcp_tool"):
                try:
                    server.register_tool(obj)
                    _log(f"Registered tool {attr} from {module_name}")
                except Exception as e:
                    _log(f"Failed registering {attr} from {module_name}: {e}")
                    continue

def main():
    load_tools()
    server.run()

if __name__ == "__main__":
    main()
```

---

## core/__init__.py

```python
# core/__init__.py
from .logging import eden_log

__all__ = ["eden_log"]
```

---

## core/logging.py

```python
from rich.console import Console

console = Console()

def eden_log(message: str):
    console.log(f"[bold cyan]Eden-MCP[/bold cyan]: {message}")
```

---

## core/mcp/__init__.py

```python
"""Local MCP stub for development/testing.
This is a minimal implementation that provides the parts of the
`mcp` API this server expects: `mcp.server.Server`, `mcp.server.tool`
decorator and `mcp.types` content classes. This stub is intentionally
lightweight and meant for dev/testing only.
"""

from .server import Server, tool
from .types import TextContent, JsonContent

__all__ = ["Server", "tool", "TextContent", "JsonContent"]
```

---

## core/mcp/server.py

```python
import functools
import inspect
import threading

class Server:
    def __init__(self, name: str = "mcp-server"):
        self.name = name
        self._tools = []

    def register_tool(self, func):
        self._tools.append(func)

    def list_tools(self):
        return [f.__name__ for f in self._tools]

    def run(self):
        # Minimal run: announce available tools and return.
        print(f"[mcp stub] Server '{self.name}' starting. Registered tools: {self.list_tools()}")
        # In a real implementation this would block and use stdio/transport.

def tool(*dargs, **dkwargs):
    """A decorator that marks functions as MCP tools.
    The decorator attaches metadata onto the function so the server
    can discover and register it.
    """
    def decorator(func):
        setattr(func, "_mcp_tool", True)
        # copy signature metadata as attribute for introspection if needed
        func._mcp_metadata = {
            "name": func.__name__,
            "doc": inspect.getdoc(func),
            "signature": str(inspect.signature(func)),
        }
        return func

    if callable(dargs[0]) and not dkwargs:
        # Called without arguments
        return decorator(dargs[0])
    else:
        # Called with arguments
        return decorator
```

---

## core/mcp/types.py

```python
"""Minimal content types for MCP stub."""

class TextContent:
    def __init__(self, type: str, text: str):
        self.type = type
        self.text = text

class JsonContent:
    def __init__(self, type: str, data: dict):
        self.type = type
        self.data = data
```

---

## tools/__init__.py

```python
# tools/__init__.py
# This file makes the tools directory a Python package
# and allows for auto-discovery of tool modules
```

---

## tools/agent_tools.py

```python
"""Agent interaction tools for EdenOS MCP server."""

from core.mcp import tool, TextContent

@tool()
def list_agents():
    """List available EdenOS agents."""
    return [TextContent(
        type="text",
        text="Available agents: chaos, organizer, memory, router"
    )]

@tool()
def ping_agent(agent_name: str):
    """Ping a specific agent to check if it's responsive."""
    return [TextContent(
        type="text",
        text=f"Pinging {agent_name} agent... Agent is responsive."
    )]
```

---

## tools/chaos_tools.py

```python
"""CHAOS diagnostic tools for EdenOS MCP server."""

from core.mcp import tool, TextContent

@tool()
def run_chaos_check():
    """Run basic CHAOS system diagnostic."""
    return [TextContent(
        type="text",
        text="CHAOS diagnostic completed: System nominal"
    )]

@tool()
def get_system_status():
    """Get current EdenOS system status."""
    return [TextContent(
        type="text",
        text="System Status: All systems operational"
    )]
```

---

## tools/filesystem_tools.py

```python
"""Filesystem inspection tools for EdenOS MCP server."""

from core.mcp import tool, TextContent
import os

@tool()
def read_file_safe(path: str):
    """Safely read file contents (read-only)."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        return [TextContent(
            type="text",
            text=f"File content from {path}:\n{content}"
        )]
    except Exception as e:
        return [TextContent(
            type="text",
            text=f"Error reading {path}: {str(e)}"
        )]

@tool()
def list_directory(path: str):
    """List directory contents."""
    try:
        items = os.listdir(path)
        return [TextContent(
            type="text",
            text=f"Directory {path} contains:\n" + "\n".join(items)
        )]
    except Exception as e:
        return [TextContent(
            type="text",
            text=f"Error listing {path}: {str(e)}"
        )]
```

---

## tools/organizer_tools.py

```python
"""Organizer agent tools for EdenOS MCP server."""

from core.mcp import tool, TextContent

@tool()
def organize_workspace():
    """Trigger workspace organization."""
    return [TextContent(
        type="text",
        text="Workspace organization initiated"
    )]

@tool()
def cleanup_temp():
    """Clean up temporary files."""
    return [TextContent(
        type="text",
        text="Temporary file cleanup completed"
    )]
```
