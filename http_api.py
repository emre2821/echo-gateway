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
    # import lazily so the project can be used as a library
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
