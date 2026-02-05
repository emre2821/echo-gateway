#!/usr/bin/env python3
"""
EdenOS MCP Server Hub - Core Module
Pure server initialization and event bus only.
No business logic, no shared state, no storage.
"""

import os
from typing import Dict, Any, List, Optional, Callable
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
server = FastMCP("eden-mcp-server-hub")

# Configuration constants only
CONTEXT_FILE = "context-window.json"
PERMISSIONS_FILE = "permissions.json"
CHAOS_FILES_DIR = "chaos_files"
MEDIA_FILES_DIR = "media_files"

# Ensure directories exist
os.makedirs(CHAOS_FILES_DIR, exist_ok=True)
os.makedirs(MEDIA_FILES_DIR, exist_ok=True)

# Event bus for dependency injection
class EventBus:
    def __init__(self):
        self._handlers: Dict[str, List[Callable]] = {}
    
    def subscribe(self, event: str, handler: Callable):
        if event not in self._handlers:
            self._handlers[event] = []
        self._handlers[event].append(handler)
    
    def emit(self, event: str, data: Any = None):
        if event in self._handlers:
            for handler in self._handlers[event]:
                try:
                    handler(data)
                except Exception as e:
                    print(f"[EventBus] Handler error for {event}: {e}")

# Global event bus instance
event_bus = EventBus()

# Module registry
registered_modules: Dict[str, Any] = {}

def get_server():
    """Get the FastMCP server instance."""
    return server

def register(name: str, module: Any):
    """Register a module with the hub."""
    registered_modules[name] = module
    event_bus.emit("module_registered", {"name": name, "module": module})

def get_module(name: str) -> Optional[Any]:
    """Get a registered module by name."""
    return registered_modules.get(name)

def emit(event_type: str, payload: dict):
    """Emit system event through event bus."""
    event_bus.emit("system_event", {
        "type": event_type,
        "payload": payload
    })
