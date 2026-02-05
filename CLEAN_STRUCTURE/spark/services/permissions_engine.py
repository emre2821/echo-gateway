#!/usr/bin/env python3
"""
EdenOS MCP Server Hub - Permissions Engine
Single authoritative source for all permission, audit, and access control logic.
"""

import json
import os
import time
import uuid
from typing import Dict, Any, List, Optional

class PermissionsEngine:
    """Single authority for permissions, audit, and access control."""
    
    def __init__(self, permissions_file: str = "permissions.json"):
        self.permissions_file = permissions_file
        self._cache: Optional[Dict[str, Any]] = None
        self._cache_timestamp = 0
        self.hub = None  # Nerve hook
        
        # Exclusion zones for file operations
        self.exclusion_zones = [
            r"C:\Windows",
            r"C:\Program Files", 
            r"C:\Program Files (x86)",
        ]
    
    def _make_id(self) -> str:
        """Generate unique ID."""
        return uuid.uuid4().hex
    
    def on_boot(self, hub):
        """Nerve hook: Initialize with hub and subscribe to events."""
        self.hub = hub
        hub.event_bus.subscribe("system_event", self.handle_event)
    
    def handle_event(self, event: dict):
        """Handle system events."""
        event_type = event.get("type")
        payload = event.get("payload", {})
        
        # React to relevant events
        if event_type == "agent.trust.changed":
            self._audit("trust_change_reacted", {"agent": payload.get("agent_id"), "level": payload.get("level")})
        elif event_type == "filesystem.deleted":
            self._audit("file_deletion_noted", {"path": payload.get("path")})
        elif event_type == "chaos.file.created":
            self._audit("chaos_creation_noted", {"filename": payload.get("filename")})
    
    def _load_permissions(self) -> Dict[str, Any]:
        """Load permissions from file with caching."""
        current_time = time.time()
        
        # Cache for 5 seconds to avoid excessive file reads
        if self._cache and (current_time - self._cache_timestamp) < 5:
            return self._cache
        
        try:
            if os.path.exists(self.permissions_file):
                with open(self.permissions_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
            else:
                data = {
                    "permissions": {},
                    "requests": {}, 
                    "audit": [],
                    "allowed_paths": [],
                    "exclusion_zones": self.exclusion_zones
                }
                self._save_permissions(data)
            
            self._cache = data
            self._cache_timestamp = current_time
            return data
            
        except Exception:
            # Fallback to safe defaults
            self._cache = {
                "permissions": {},
                "requests": {},
                "audit": [],
                "allowed_paths": [],
                "exclusion_zones": self.exclusion_zones
            }
            self._cache_timestamp = current_time
            return self._cache
    
    def _save_permissions(self, data: Dict[str, Any]) -> bool:
        """Save permissions to file."""
        try:
            with open(self.permissions_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            
            # Invalidate cache
            self._cache = None
            self._cache_timestamp = 0
            return True
            
        except Exception as e:
            print(f"[PermissionsEngine] Failed to save permissions: {e}")
            return False
    
    def audit(self, event_type: str, details: Dict[str, Any]) -> bool:
        """Append an audit entry to permissions store."""
        try:
            data = self._load_permissions()
            entry = {
                "id": self._make_id(),
                "event": event_type,
                "details": details,
                "ts": time.time(),
            }
            data.setdefault("audit", []).append(entry)
            return self._save_permissions(data)
            
        except Exception as e:
            print(f"[PermissionsEngine] Audit failed: {e}")
            return False
    
    def is_excluded(self, path: str) -> bool:
        """Check if path is in exclusion zones."""
        if not path:
            return True
        
        normalized = os.path.abspath(path)
        for ex in self.exclusion_zones:
            if normalized.startswith(os.path.abspath(ex)):
                return True
        return False
    
    def is_path_allowed(self, path: str, operation: str = "read") -> bool:
        """Check if path is allowed based on allowed_paths."""
        if not path:
            return False
        
        if self.is_excluded(path):
            return False
        
        try:
            data = self._load_permissions()
            allowed_paths = data.get("allowed_paths", [])
            
            for allowed_path in allowed_paths:
                if os.path.abspath(path).startswith(os.path.abspath(allowed_path)):
                    return True
            
            return False
            
        except Exception as e:
            print(f"[PermissionsEngine] Path check failed: {e}")
            return False
    
    def add_allowed_path(self, path: str) -> bool:
        """Add a path to the allowed paths list."""
        if not path or not os.path.exists(path):
            return False
        
        try:
            data = self._load_permissions()
            allowed_paths = data.setdefault("allowed_paths", [])
            abs_path = os.path.abspath(path)
            
            if abs_path not in allowed_paths:
                allowed_paths.append(abs_path)
                success = self._save_permissions(data)
                
                if success:
                    self.audit("path_allowed", {"path": path})
                
                return success
            
            return True  # Already exists
            
        except Exception as e:
            print(f"[PermissionsEngine] Failed to add path: {e}")
            return False
    
    def remove_allowed_path(self, path: str) -> bool:
        """Remove a path from the allowed paths list."""
        if not path:
            return False
        
        try:
            data = self._load_permissions()
            allowed_paths = data.get("allowed_paths", [])
            abs_path = os.path.abspath(path)
            
            if abs_path in allowed_paths:
                allowed_paths.remove(abs_path)
                success = self._save_permissions(data)
                
                if success:
                    self.audit("path_removed", {"path": path})
                
                return success
            
            return True  # Already removed
            
        except Exception as e:
            print(f"[PermissionsEngine] Failed to remove path: {e}")
            return False
    
    def list_allowed_paths(self) -> List[str]:
        """List all allowed paths."""
        try:
            data = self._load_permissions()
            return data.get("allowed_paths", [])
        except Exception as e:
            print(f"[PermissionsEngine] Failed to list paths: {e}")
            return []
    
    def get_audit_log(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent audit entries."""
        try:
            data = self._load_permissions()
            audit = data.get("audit", [])
            # Return most recent entries first
            return sorted(audit, key=lambda x: x.get("ts", 0), reverse=True)[:limit]
        except Exception as e:
            print(f"[PermissionsEngine] Failed to get audit log: {e}")
            return []
    
    def set_permission(self, entity: str, resource: str, action: str, allowed: bool) -> bool:
        """Set a specific permission."""
        try:
            data = self._load_permissions()
            permissions = data.setdefault("permissions", {})
            
            entity_perms = permissions.setdefault(entity, {})
            entity_perms[f"{resource}:{action}"] = allowed
            
            success = self._save_permissions(data)
            
            if success:
                self._audit("permission_set", {
                    "entity": entity,
                    "resource": resource,
                    "action": action,
                    "allowed": allowed
                })
                
                # Emit permission event
                if self.hub:
                    event_type = "permissions.granted" if allowed else "permissions.revoked"
                    self.hub.emit(event_type, {
                        "entity": entity,
                        "resource": resource,
                        "action": action
                    })
            
            return success
            
        except Exception as e:
            print(f"[PermissionsEngine] Failed to set permission: {e}")
            return False
    
    def check_permission(self, entity: str, resource: str, action: str) -> bool:
        """Check a specific permission."""
        try:
            data = self._load_permissions()
            permissions = data.get("permissions", {})
            
            entity_perms = permissions.get(entity, {})
            return entity_perms.get(f"{resource}:{action}", False)
            
        except Exception as e:
            print(f"[PermissionsEngine] Failed to check permission: {e}")
            return False

# Global permissions engine instance
permissions_engine = PermissionsEngine()
