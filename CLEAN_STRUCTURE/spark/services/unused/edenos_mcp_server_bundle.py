#!/usr/bin/env python3
"""
EdenOS MCP Server Bundle
Complete MCP server with auto-discovery, permissions system, and HTTP API
"""

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

# core/logging.py
from rich.console import Console

console = Console()

def eden_log(message: str):
    console.log(f"[bold cyan]Eden-MCP[/bold cyan]: {message}")

# core/__init__.py
from .logging import eden_log

__all__ = ["eden_log"]

# mcp/server.py
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

    # if used without args
    if len(dargs) == 1 and callable(dargs[0]):
        return decorator(dargs[0])
    return decorator

# mcp/types.py
from dataclasses import dataclass
from typing import Any, Dict

@dataclass
class TextContent:
    type: str
    text: str

@dataclass
class JsonContent:
    type: str
    data: Dict[str, Any]

# mcp/__init__.py
"""Local MCP stub for development/testing.

This is a minimal implementation that provides the parts of the
`mcp` API this server expects: `mcp.server.Server`, `mcp.server.tool`
decorator and `mcp.types` content classes. This stub is intentionally
lightweight and meant for dev/testing only.
"""

from .server import Server, tool
from .types import TextContent, JsonContent

__all__ = ["Server", "tool", "TextContent", "JsonContent"]

# tools/__init__.py
"""Tools package helpers and small compatibility shims for MCP dev server.

Provides:
- eden_tool: decorator used to mark functions as MCP tools (adds _mcp_tool)
- TextContent, JsonContent: small container types used by tool functions

This file intentionally keeps the runtime behavior minimal and import-safe so
importing tools modules doesn't have side-effects.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable
import inspect

@dataclass
class TextContent:
    type: str = "text"
    text: str = ""

@dataclass
class JsonContent:
    type: str = "json"
    data: Any = None

def eden_tool(*dargs, **dkwargs) -> Callable:
    """Decorator to mark a function as an MCP tool.

    Usage:
      @eden_tool()
      def foo(...):
          ...

    or

      @eden_tool
      def foo(...):
          ...
    """

    def decorator(func: Callable) -> Callable:
        setattr(func, "_mcp_tool", True)
        func._eden_metadata = {
            "name": func.__name__,
            "doc": inspect.getdoc(func),
            "signature": str(inspect.signature(func)),
        }
        return func

    # support @eden_tool (no parens) and @eden_tool() (with parens)
    if len(dargs) == 1 and callable(dargs[0]):
        return decorator(dargs[0])
    return decorator

__all__ = ["eden_tool", "TextContent", "JsonContent"]

# tools/agent_tools.py
from . import eden_tool, JsonContent

@eden_tool()
def agent_ping(agent_name: str):
    """
    Test hook for agent-level tools.
    """
    return [JsonContent(type="json", data={
        "agent": agent_name,
        "status": "acknowledged",
        "message": f"{agent_name} is reachable through MCP."
    })]

# tools/chaos_tools.py
# chaos_tools.py

from . import eden_tool, TextContent, JsonContent
from typing import Dict, Any

@eden_tool()
def chaos_inspect(text: str):
    """
    Basic CHAOS diagnostic tool.
    Returns structural clues, tag counts, and metadata.
    This is a staging version until real parser is plugged in.
    """
    lines = text.splitlines()
    length = len(text)
    num_lines = len(lines)

    tag_counts: Dict[str, int] = {}
    for line in lines:
        if line.strip().startswith("[") and "]" in line:
            tag = line.strip().split("]")[0] + "]"
            tag_counts[tag] = tag_counts.get(tag, 0) + 1

    return [JsonContent(
        type="json",
        data={
            "length": length,
            "lines": num_lines,
            "tags_detected": tag_counts,
            "preview": text[:300]
        }
    )]

@eden_tool()
def chaos_extract_tags(text: str):
    """
    Extract all CHAOS tags in order.
    Good for debugging and tooling integration.
    """
    tags = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("[") and "]" in stripped:
            tag = stripped.split("]", 1)[0] + "]"
            tags.append(tag)

    return [JsonContent(
        type="json",
        data={
            "count": len(tags),
            "tags": tags
        }
    )]

@eden_tool()
def chaos_echo(text: str):
    """
    A simple passthrough tool.
    Useful for testing Dev Mode pipes.
    """
    return [TextContent(type="text", text=text)]

# tools/filesystem_tools.py
from . import eden_tool, TextContent, JsonContent
import os

@eden_tool()
def list_dir(path: str):
    """
    List all files + folders in a path.
    """
    try:
        files = os.listdir(path)
        return [JsonContent(type="json", data={
            "path": path,
            "items": files
        })]
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {e}")]

@eden_tool()
def read_file(path: str):
    """
    Read text content of a file.
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = f.read()
        return [TextContent(type="text", text=data)]
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {e}")]

# tools/organizer_tools.py
# organizer_tools.py

# Safe, permission-gated organizer tools for EdenOS
# Provides a persistent, revocable permission model stored in
# tools/permissions.json. All read/write/move/rename operations
# must be requested and then explicitly granted (by a human).

from . import eden_tool, TextContent, JsonContent
import os
import shutil
import json
import uuid
import time

# permissions file lives next to this module
PERMISSIONS_FILE = os.path.join(os.path.dirname(__file__), "permissions.json")

def _load_permissions():
    try:
        with open(PERMISSIONS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        data = {"permissions": {}, "requests": {}}
    return data

def _save_permissions(data):
    with open(PERMISSIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def _audit(event_type: str, details: dict):
    """Append an audit entry to permissions store."""
    data = _load_permissions()
    entry = {
        "id": _make_id(),
        "event": event_type,
        "details": details,
        "ts": time.time(),
    }
    data.setdefault("audit", []).append(entry)
    _save_permissions(data)

# -------------------------------------------------------------
# 1) HARD EXCLUSION ZONES (Windows core + user-protected folders)
# -------------------------------------------------------------
EXCLUSION_ZONES = [
    r"C:\\Windows",
    r"C:\\Program Files",
    r"C:\\Program Files (x86)",
    r"C:\\Users\\emmar\\Pictures",
    r"C:\\Users\\emmar\\OneDrive\\Pictures",
]

def is_excluded(path: str) -> bool:
    if not path:
        return True
    normalized = os.path.abspath(path)
    for ex in EXCLUSION_ZONES:
        if normalized.startswith(os.path.abspath(ex)):
            return True
    return False

# -------------------------------------------------------------
# Permission API
# - request_permission(action, target, requester)
# - grant_permission(request_id, granter, duration_seconds)
# - revoke_permission(permission_id)
# - check_permission(action, target)
# -------------------------------------------------------------

def _make_id():
    return uuid.uuid4().hex

@eden_tool()
def request_permission(action: str, target: str, requester: str = "agent"):
    """
    Create a permission request. Returns a JSON object including
    `request_id` which a human should approve by calling `grant_permission(request_id)`.
    """
    if is_excluded(target):
        return [TextContent(type="text", text="Access denied: protected folder.")]

    data = _load_permissions()
    req_id = _make_id()
    data.setdefault("requests", {})[req_id] = {
        "action": action,
        "target": target,
        "requester": requester,
        "created_at": time.time(),
    }
    _save_permissions(data)

    _audit("request_created", {"request_id": req_id, "action": action, "target": target, "requester": requester})

    return [JsonContent(type="json", data={
        "status": "requested",
        "request_id": req_id,
        "instruction": f"Call grant_permission('{req_id}', granter='emma') to approve."
    })]

@eden_tool()
def grant_permission(request_id: str, granter: str = "emma", duration_seconds: int = None):
    """Approve a pending request and create a granted permission entry."""
    data = _load_permissions()
    req = data.get("requests", {}).get(request_id)
    if not req:
        return [TextContent(type="text", text="Request not found.")]

    perm_id = _make_id()
    expires_at = None
    if duration_seconds:
        expires_at = time.time() + int(duration_seconds)

    data.setdefault("permissions", {})[perm_id] = {
        "action": req["action"],
        "target": req["target"],
        "granted_by": granter,
        "granted_at": time.time(),
        "expires_at": expires_at,
        "allowed": True,
    }

    # remove request
    data.get("requests", {}).pop(request_id, None)
    _save_permissions(data)

    _audit("permission_granted", {"permission_id": perm_id, "granted_by": granter, "request_id": request_id})

    return [JsonContent(type="json", data={
        "status": "granted",
        "permission_id": perm_id,
        "action": data["permissions"][perm_id]["action"],
        "target": data["permissions"][perm_id]["target"],
    })]

@eden_tool()
def revoke_permission(permission_id: str):
    """Revoke a previously granted permission immediately."""
    data = _load_permissions()
    perm = data.get("permissions", {}).get(permission_id)
    if not perm:
        return [TextContent(type="text", text="Permission not found.")]
    perm["allowed"] = False
    perm["revoked_at"] = time.time()
    _save_permissions(data)
    _audit("permission_revoked", {"permission_id": permission_id})
    return [TextContent(type="text", text=f"Permission {permission_id} revoked.")]

def _check_permission_for(action: str, target: str, permission_id: str = None) -> (bool, str):
    """Return (allowed: bool, permission_id_or_message: str)"""
    data = _load_permissions()

    # allow explicit permission_id check if provided
    if permission_id:
        perm = data.get("permissions", {}).get(permission_id)
        if not perm:
            return False, "permission_not_found"
        if not perm.get("allowed", False):
            return False, "permission_not_allowed"
        if perm.get("expires_at") and time.time() > perm["expires_at"]:
            return False, "permission_expired"
        # match action and target by simple prefix matching for folders
        if perm["action"] != action:
            return False, "action_mismatch"
        if not (target == perm["target"] or target.startswith(perm["target"])):
            return False, "target_mismatch"
        return True, permission_id

    # without explicit permission_id, look up any matching allowed permission
    for pid, perm in data.get("permissions", {}).items():
        if not perm.get("allowed", False):
            continue
        if perm.get("expires_at") and time.time() > perm["expires_at"]:
            continue
        if perm["action"] != action:
            continue
        if target == perm["target"] or target.startswith(perm["target"]):
            return True, pid

    return False, "no_matching_permission"

# -------------------------------------------------------------
# File operations that use the permission model
# Each `*_secure` function creates a request; each `execute_*`
# function requires a `permission_id` returned from `grant_permission`.
# -------------------------------------------------------------

@eden_tool()
def read_file_secure(path: str):
    if is_excluded(path):
        return [TextContent(type="text", text="Access denied: protected folder.")]
    # create a request
    return request_permission("read_file", path, requester="agent")

@eden_tool()
def execute_read(permission_id: str = None):
    allowed, info = _check_permission_for("read_file", "", permission_id)
    if not allowed:
        _audit("execute_read_denied", {"permission_id": permission_id, "reason": info})
        return [TextContent(type="text", text=f"Permission denied: {info}")]

    # info is permission id
    data = _load_permissions()
    perm = data["permissions"][info]
    path = perm["target"]
    if is_excluded(path):
        return [TextContent(type="text", text="Access denied: protected folder.")]

    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
            _audit("execute_read_success", {"permission_id": info, "path": path, "bytes": len(content)})
            return [TextContent(type="text", text=content)]
    except Exception as e:
        _audit("execute_read_error", {"permission_id": info, "path": path, "error": str(e)})
        return [TextContent(type="text", text=f"Error: {e}")]

@eden_tool()
def create_file(path: str, content: str = ""):
    if is_excluded(path):
        return [TextContent(type="text", text="Cannot create inside protected folder.")]
    return request_permission("create_file", path, requester="agent")

@eden_tool()
def execute_create(permission_id: str, content: str = ""):
    allowed, info = _check_permission_for("create_file", "", permission_id)
    if not allowed:
        _audit("execute_create_denied", {"permission_id": permission_id, "reason": info})
        return [TextContent(type="text", text=f"Permission denied: {info}")]

    data = _load_permissions()
    perm = data["permissions"][info]
    path = perm["target"]
    if is_excluded(path):
        return [TextContent(type="text", text="Cannot create inside protected folder.")]

    try:
        folder = os.path.dirname(path)
        if folder and not os.path.exists(folder):
            os.makedirs(folder, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        _audit("execute_create_success", {"permission_id": info, "path": path, "bytes": len(content)})
        return [TextContent(type="text", text=f"File created: {path}")]
    except Exception as e:
        _audit("execute_create_error", {"permission_id": info, "path": path, "error": str(e)})
        return [TextContent(type="text", text=f"Error: {e}")]

@eden_tool()
def move_file(source: str, destination: str):
    if is_excluded(source) or is_excluded(destination):
        return [TextContent(type="text", text="Cannot move files from/to protected folder.")]
    return request_permission("move_file", f"{source} -> {destination}", requester="agent")

@eden_tool()
def execute_move(permission_id: str):
    allowed, info = _check_permission_for("move_file", "", permission_id)
    if not allowed:
        _audit("execute_move_denied", {"permission_id": permission_id, "reason": info})
        return [TextContent(type="text", text=f"Permission denied: {info}")]

    data = _load_permissions()
    perm = data["permissions"][info]
    source, dest = perm["target"].split(" -> ")
    if is_excluded(source) or is_excluded(dest):
        return [TextContent(type="text", text="Action blocked: protected folder.")]

    try:
        folder = os.path.dirname(dest)
        if folder and not os.path.exists(folder):
            os.makedirs(folder, exist_ok=True)
        shutil.move(source, dest)
        _audit("execute_move_success", {"permission_id": info, "source": source, "dest": dest})
        return [TextContent(type="text", text=f"Moved {source} -> {dest}")]
    except Exception as e:
        _audit("execute_move_error", {"permission_id": info, "source": source, "dest": dest, "error": str(e)})
        return [TextContent(type="text", text=f"Error: {e}")]

@eden_tool()
def rename_file(path: str, new_name: str):
    if is_excluded(path):
        return [TextContent(type="text", text="Cannot rename inside protected folder.")]

    folder = os.path.dirname(path)
    new_path = os.path.join(folder, new_name)
    return request_permission("rename_file", f"{path} -> {new_path}", requester="agent")

@eden_tool()
def execute_rename(permission_id: str):
    allowed, info = _check_permission_for("rename_file", "", permission_id)
    if not allowed:
        _audit("execute_rename_denied", {"permission_id": permission_id, "reason": info})
        return [TextContent(type="text", text=f"Permission denied: {info}")]

    data = _load_permissions()
    perm = data["permissions"][info]
    source, dest = perm["target"].split(" -> ")
    if is_excluded(source) or is_excluded(dest):
        return [TextContent(type="text", text="Cannot rename inside protected folder.")]

    try:
        os.rename(source, dest)
        _audit("execute_rename_success", {"permission_id": info, "source": source, "dest": dest})
        return [TextContent(type="text", text=f"Renamed {source} -> {dest}")]
    except Exception as e:
        _audit("execute_rename_error", {"permission_id": info, "source": source, "dest": dest, "error": str(e)})
        return [TextContent(type="text", text=f"Error: {e}")]

@eden_tool()
def map_directory(path: str):
    if is_excluded(path):
        return [TextContent(type="text", text="Cannot map protected folder.")]

    structure = {}

    for root, dirs, files in os.walk(path):
        if is_excluded(root):
            continue
        structure[root] = {
            "folders": [d for d in dirs if not is_excluded(os.path.join(root, d))],
            "files": files,
        }

    return [JsonContent(type="json", data=structure)]

@eden_tool()
def find_files(path: str, keyword: str):
    if is_excluded(path):
        return [TextContent(type="text", text="Cannot search inside protected folder.")]

    results = []

    for root, dirs, files in os.walk(path):
        if is_excluded(root):
            continue
        for f in files:
            if keyword.lower() in f.lower():
                results.append(os.path.join(root, f))

    return [JsonContent(type="json", data={"matches": results})]

@eden_tool()
def list_permissions():
    data = _load_permissions()
    return [JsonContent(type="json", data=data.get("permissions", {}))]

@eden_tool()
def list_requests():
    data = _load_permissions()
    return [JsonContent(type="json", data=data.get("requests", {}))]

@eden_tool()
def list_audit(limit: int = 100):
    data = _load_permissions()
    audit = data.get("audit", [])
    # return most recent entries first
    audit_sorted = sorted(audit, key=lambda e: e.get("ts", 0), reverse=True)
    return [JsonContent(type="json", data={"audit": audit_sorted[:limit]})]

# http_api.py
"""Lightweight HTTP API to expose MCP tools for SaaS-style usage.

This is a development-oriented HTTP wrapper that exposes the registered
MCP tools over a simple JSON API. It includes a minimal API key check.

Endpoints:
- GET /health
- GET /tools
- POST /run  (json: {tool: str, args: list, kwargs: dict})

Security: for now uses a simple API key stored in `keys.json`.
This is NOT production-ready; it's a starting point for a SaaS MVP.
"""
from __future__ import annotations

import json
import os
import traceback
from flask import Flask, request, jsonify

ROOT = os.path.dirname(__file__)
KEYS_FILE = os.path.join(ROOT, "keys.json")

def _ensure_keys():
    if not os.path.exists(KEYS_FILE):
        # create a default development key
        with open(KEYS_FILE, "w", encoding="utf-8") as f:
            json.dump({"keys": ["dev-key"]}, f, indent=2)

def _load_keys():
    _ensure_keys()
    with open(KEYS_FILE, "r", encoding="utf-8") as f:
        return json.load(f).get("keys", [])

def check_api_key(req) -> bool:
    provided = req.headers.get("X-API-Key") or req.args.get("api_key")
    if not provided:
        return False
    return provided in _load_keys()

app = Flask("eden-mcp-http")

def _import_mcp_server():
    try:
        from . import server as mcp_server
    except ImportError:
        import importlib

        try:
            mcp_server = importlib.import_module("MCP_Server.server")
        except ImportError:
            mcp_server = importlib.import_module("server")
    return mcp_server

@app.route("/health")
def health():
    return jsonify({"ok": True, "service": "eden-mcp-http"})

@app.route("/tools")
def list_tools():
    if not check_api_key(request):
        return jsonify({"error": "missing_or_invalid_api_key"}), 401
    # import lazily so project can be used as a library
    mcp_server = _import_mcp_server().server

    return jsonify({"tools": mcp_server.list_tools()})

@app.route("/run", methods=["POST"])
def run_tool():
    if not check_api_key(request):
        return jsonify({"error": "missing_or_invalid_api_key"}), 401

    data = request.get_json() or {}
    tool_name = data.get("tool")
    args = data.get("args", []) or []
    kwargs = data.get("kwargs", {}) or {}

    if not tool_name:
        return jsonify({"error": "tool required"}), 400

    mcp_server = _import_mcp_server().server

    # find the tool by name
    target = None
    for func in mcp_server._tools:
        if func.__name__ == tool_name:
            target = func
            break

    if not target:
        return jsonify({"error": "tool_not_found"}), 404

    try:
        result = target(*args, **kwargs)
        # try to serialize result: commonly list of TextContent/JsonContent
        return jsonify({"ok": True, "result": result})
    except Exception as e:
        tb = traceback.format_exc()
        return jsonify({"ok": False, "error": str(e), "traceback": tb}), 500

if __name__ == "__main__":
    # ensure tools are loaded (same behavior as server.main)
    try:
        s = _import_mcp_server()
        s.load_tools()
    except Exception:
        pass

    _ensure_keys()
    app.run(host="0.0.0.0", port=8766)

# http_approval_bridge.py
"""Simple HTTP bridge to approve MCP-like file actions.

This bridge is intentionally minimal and for local development only.
It accepts POST /approve with JSON {action, target, requester} and
creates an immediate permission entry in `permissions.json`.

WARNING: This bridge will grant permissions immediately by default.
Run it only on localhost and understand the security implications.
"""
import json
import os
import uuid
import time
import logging
from flask import Flask, request, jsonify

ROOT = os.path.dirname(__file__)
PERMISSIONS_FILE = os.path.join(ROOT, 'permissions.json')

logger = logging.getLogger(__name__)

app = Flask('mcp-approval-bridge')

def _ensure_permissions_file():
    if os.path.exists(PERMISSIONS_FILE):
        return True

    try:
        os.makedirs(os.path.dirname(PERMISSIONS_FILE), exist_ok=True)
    except Exception as exc:
        logger.error('Could not ensure permissions directory exists at %s', os.path.dirname(PERMISSIONS_FILE), exc_info=exc)
        return False

    logger.warning('Permissions file not found at %s; a new file will be created on first write', PERMISSIONS_FILE)
    return True

if not _ensure_permissions_file():
    logger.error('Permissions file is not available at startup; approvals may fail until path is fixed')

def _load():
    try:
        with open(PERMISSIONS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {'permissions': {}, 'requests': {}, 'audit': []}

def _save(data):
    try:
        with open(PERMISSIONS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as exc:
        logger.error('Failed to write permissions file at %s', PERMISSIONS_FILE, exc_info=exc)
        return False

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
        'ts': time.time(),
    })
    if not _save(data):
        return jsonify({'approved': False, 'reason': 'persist_failed'}), 500

    return jsonify({'approved': True, 'permission_id': perm_id})

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8765)

# pyproject.toml
[build-system]
requires = ["setuptools>=42", "wheel"]
build-backend == "setuptools.build_meta"

[project]
name == "eden-mcp-server"
version == "0.1.0"
description == "EdenOS MCP bridge for local development"
authors == [ { name == "Dreamcatcher" } ]
requires-python == ">=3.8"
[project.optional-dependencies]
dev == ["rich==13.4.2"]
