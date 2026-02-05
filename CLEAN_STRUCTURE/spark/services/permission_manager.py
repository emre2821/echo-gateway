#!/usr/bin/env python3
"""
EdenOS MCP Server Hub - Permission Manager (Tool Adapter)
Thin adapter layer that calls the permissions_engine.
No business logic here - just tool interface.
"""

from permissions_engine import permissions_engine

# Export functions that tools can call - these delegate to the engine
def is_excluded(path: str) -> bool:
    """Check if path is in exclusion zones."""
    return permissions_engine.is_excluded(path)

def is_path_allowed(path: str, operation: str = "read") -> bool:
    """Check if path is allowed based on allowed_paths."""
    return permissions_engine.is_path_allowed(path, operation)

def add_allowed_path(path: str) -> bool:
    """Add a path to the allowed paths list."""
    return permissions_engine.add_allowed_path(path)

def remove_allowed_path(path: str) -> bool:
    """Remove a path from the allowed paths list."""
    return permissions_engine.remove_allowed_path(path)

def list_allowed_paths() -> list:
    """List all allowed paths."""
    return permissions_engine.list_allowed_paths()

def audit_event(event_type: str, details: dict) -> bool:
    """Record an audit event."""
    return permissions_engine.audit(event_type, details)

def check_permission(entity: str, resource: str, action: str) -> bool:
    """Check a specific permission."""
    return permissions_engine.check_permission(entity, resource, action)

def set_permission(entity: str, resource: str, action: str, allowed: bool) -> bool:
    """Set a specific permission."""
    return permissions_engine.set_permission(entity, resource, action, allowed)
