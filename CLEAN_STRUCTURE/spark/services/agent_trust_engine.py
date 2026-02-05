#!/usr/bin/env python3
"""
EdenOS MCP Server Hub - Agent Trust Engine
Manages agent trust levels and enforces access controls.
"""

import json
import os
import time
import hashlib
from typing import Dict, Any, List, Optional
from enum import Enum
from permissions_engine import permissions_engine

class TrustLevel(Enum):
    """Agent trust levels."""
    UNKNOWN = "unknown"
    UNTRUSTED = "untrusted"
    LIMITED = "limited"
    TRUSTED = "trusted"
    PRIVILEGED = "privileged"
    SYSTEM = "system"

class AgentTrustEngine:
    """Manages agent trust levels and enforces access controls."""
    
    def __init__(self, trust_file: str = "agent_trust.json"):
        self.trust_file = trust_file
        self.hub = None  # Nerve hook
        
        # Trust registry
        self._trust_registry: Dict[str, Dict[str, Any]] = {}
        
        # Default trust policies
        self._default_policies = {
            TrustLevel.UNKNOWN: {
                "filesystem": {"read": False, "write": False, "delete": False},
                "chaos": {"create": False, "read": False, "update": False, "delete": False},
                "context": {"read": False, "write": False, "clear": False},
                "media": {"register": False, "read": False, "update": False, "delete": False},
                "permissions": {"read": False, "write": False}
            },
            TrustLevel.UNTRUSTED: {
                "filesystem": {"read": False, "write": False, "delete": False},
                "chaos": {"create": False, "read": False, "update": False, "delete": False},
                "context": {"read": False, "write": False, "clear": False},
                "media": {"register": False, "read": False, "update": False, "delete": False},
                "permissions": {"read": False, "write": False}
            },
            TrustLevel.LIMITED: {
                "filesystem": {"read": True, "write": False, "delete": False},
                "chaos": {"create": False, "read": True, "update": False, "delete": False},
                "context": {"read": True, "write": False, "clear": False},
                "media": {"register": False, "read": True, "update": False, "delete": False},
                "permissions": {"read": False, "write": False}
            },
            TrustLevel.TRUSTED: {
                "filesystem": {"read": True, "write": True, "delete": False},
                "chaos": {"create": True, "read": True, "update": True, "delete": False},
                "context": {"read": True, "write": True, "clear": False},
                "media": {"register": True, "read": True, "update": True, "delete": False},
                "permissions": {"read": True, "write": False}
            },
            TrustLevel.PRIVILEGED: {
                "filesystem": {"read": True, "write": True, "delete": True},
                "chaos": {"create": True, "read": True, "update": True, "delete": True},
                "context": {"read": True, "write": True, "clear": True},
                "media": {"register": True, "read": True, "update": True, "delete": True},
                "permissions": {"read": True, "write": True}
            },
            TrustLevel.SYSTEM: {
                "filesystem": {"read": True, "write": True, "delete": True},
                "chaos": {"create": True, "read": True, "update": True, "delete": True},
                "context": {"read": True, "write": True, "clear": True},
                "media": {"register": True, "read": True, "update": True, "delete": True},
                "permissions": {"read": True, "write": True}
            }
        }
        
        # Load existing trust registry
        self._load_trust_registry()
    
    def on_boot(self, hub):
        """Nerve hook: Initialize with hub and subscribe to events."""
        self.hub = hub
        hub.event_bus.subscribe("system_event", self.handle_event)
    
    def handle_event(self, event: dict):
        """Handle system events."""
        event_type = event.get("type")
        payload = event.get("payload", {})
        
        # React to relevant events
        if event_type == "permissions.denied":
            # Log permission denials for trust assessment
            print(f"[AgentTrustEngine] Permission denied: {payload}")
        elif event_type == "system.warning":
            # Log system warnings for trust assessment
            print(f"[AgentTrustEngine] System warning: {payload}")
        elif event_type == "chaos.file.created":
            # Track CHAOS activity for trust assessment
            print(f"[AgentTrustEngine] CHAOS activity: {payload.get('filename')}")
    
    def _load_trust_registry(self):
        """Load trust registry from file."""
        try:
            if os.path.exists(self.trust_file):
                with open(self.trust_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                self._trust_registry = data.get("agents", {})
                
                # Convert string trust levels back to enums
                for agent_id, agent_data in self._trust_registry.items():
                    if "trust_level" in agent_data:
                        agent_data["trust_level"] = TrustLevel(agent_data["trust_level"])
                        
        except Exception as e:
            print(f"[AgentTrustEngine] Failed to load trust registry: {e}")
            self._trust_registry = {}
    
    def _save_trust_registry(self) -> bool:
        """Save trust registry to file."""
        try:
            # Convert enum trust levels to strings for JSON serialization
            serializable_registry = {}
            for agent_id, agent_data in self._trust_registry.items():
                serializable_data = agent_data.copy()
                if "trust_level" in serializable_data:
                    serializable_data["trust_level"] = serializable_data["trust_level"].value
                serializable_registry[agent_id] = serializable_data
            
            data = {
                "agents": serializable_registry,
                "updated_at": time.time()
            }
            
            with open(self.trust_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            
            return True
            
        except Exception as e:
            print(f"[AgentTrustEngine] Failed to save trust registry: {e}")
            return False
    
    def _generate_agent_id(self, agent_info: Dict[str, Any]) -> str:
        """Generate unique agent ID."""
        # Create hash from agent identifying information
        identifier = f"{agent_info.get('name', '')}{agent_info.get('type', '')}{agent_info.get('version', '')}"
        return hashlib.sha256(identifier.encode()).hexdigest()[:16]
    
    def register_agent(self, agent_info: Dict[str, Any], initial_trust: TrustLevel = TrustLevel.UNKNOWN) -> str:
        """Register a new agent."""
        agent_id = self._generate_agent_id(agent_info)
        
        self._trust_registry[agent_id] = {
            "agent_id": agent_id,
            "agent_info": agent_info,
            "trust_level": initial_trust,
            "created_at": time.time(),
            "updated_at": time.time(),
            "access_log": [],
            "custom_policies": {}
        }
        
        # Emit agent registered event
        if self.hub:
            self.hub.emit("agent.registered", {
                "agent_id": agent_id,
                "agent_name": agent_info.get("name"),
                "agent_type": agent_info.get("type"),
                "initial_trust": initial_trust.value
            })
        
        self._save_trust_registry()
        return agent_id
    
    def set_trust_level(self, agent_id: str, trust_level: TrustLevel, reason: str = None) -> bool:
        """Set trust level for an agent."""
        if agent_id not in self._trust_registry:
            return False
        
        old_level = self._trust_registry[agent_id]["trust_level"]
        self._trust_registry[agent_id]["trust_level"] = trust_level
        self._trust_registry[agent_id]["updated_at"] = time.time()
        
        # Log trust level change
        self._trust_registry[agent_id]["access_log"].append({
            "timestamp": time.time(),
            "event": "trust_level_changed",
            "old_level": old_level.value,
            "new_level": trust_level.value,
            "reason": reason
        })
        
        # Emit agent trust changed event
        if self.hub:
            self.hub.emit("agent.trust.changed", {
                "agent_id": agent_id,
                "old_level": old_level.value,
                "new_level": trust_level.value,
                "reason": reason
            })
        
        return self._save_trust_registry()
    
    def get_trust_level(self, agent_id: str) -> Optional[TrustLevel]:
        """Get trust level for an agent."""
        agent_data = self._trust_registry.get(agent_id)
        return agent_data["trust_level"] if agent_data else None
    
    def get_agent_info(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get agent information."""
        return self._trust_registry.get(agent_id)
    
    def list_agents(self, trust_level: TrustLevel = None) -> List[Dict[str, Any]]:
        """List all agents, optionally filtered by trust level."""
        agents = []
        
        for agent_id, agent_data in self._trust_registry.items():
            if trust_level is None or agent_data["trust_level"] == trust_level:
                agents.append({
                    "agent_id": agent_id,
                    **agent_data
                })
        
        return agents
    
    def check_permission(self, agent_id: str, resource: str, action: str) -> bool:
        """Check if agent has permission for resource/action."""
        agent_data = self._trust_registry.get(agent_id)
        if not agent_data:
            return False
        
        trust_level = agent_data["trust_level"]
        
        # Check custom policies first
        custom_policies = agent_data.get("custom_policies", {})
        if resource in custom_policies:
            return custom_policies[resource].get(action, False)
        
        # Fall back to default policies
        default_policy = self._default_policies.get(trust_level, {})
        resource_policy = default_policy.get(resource, {})
        
        return resource_policy.get(action, False)
    
    def set_custom_policy(self, agent_id: str, resource: str, action: str, allowed: bool) -> bool:
        """Set custom policy for an agent."""
        if agent_id not in self._trust_registry:
            return False
        
        custom_policies = self._trust_registry[agent_id].setdefault("custom_policies", {})
        if resource not in custom_policies:
            custom_policies[resource] = {}
        
        custom_policies[resource][action] = allowed
        self._trust_registry[agent_id]["updated_at"] = time.time()
        
        return self._save_trust_registry()
    
    def remove_custom_policy(self, agent_id: str, resource: str, action: str = None) -> bool:
        """Remove custom policy for an agent."""
        if agent_id not in self._trust_registry:
            return False
        
        custom_policies = self._trust_registry[agent_id].get("custom_policies", {})
        
        if resource in custom_policies:
            if action is None:
                # Remove all actions for resource
                del custom_policies[resource]
            else:
                # Remove specific action
                if action in custom_policies[resource]:
                    del custom_policies[resource][action]
                
                # Clean up empty resource policy
                if not custom_policies[resource]:
                    del custom_policies[resource]
            
            self._trust_registry[agent_id]["updated_at"] = time.time()
            return self._save_trust_registry()
        
        return False
    
    def log_access(self, agent_id: str, resource: str, action: str, path: str = None, success: bool = True, details: str = None):
        """Log agent access attempt."""
        if agent_id not in self._trust_registry:
            return
        
        log_entry = {
            "timestamp": time.time(),
            "resource": resource,
            "action": action,
            "path": path,
            "success": success,
            "details": details
        }
        
        self._trust_registry[agent_id]["access_log"].append(log_entry)
        
        # Keep only last 1000 log entries per agent
        if len(self._trust_registry[agent_id]["access_log"]) > 1000:
            self._trust_registry[agent_id]["access_log"] = self._trust_registry[agent_id]["access_log"][-1000:]
        
        # Save periodically (every 10 accesses)
        if len(self._trust_registry[agent_id]["access_log"]) % 10 == 0:
            self._save_trust_registry()
    
    def get_access_log(self, agent_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get access log for an agent."""
        if agent_id not in self._trust_registry:
            return []
        
        access_log = self._trust_registry[agent_id].get("access_log", [])
        return access_log[-limit:]
    
    def revoke_agent(self, agent_id: str, reason: str = None) -> bool:
        """Revoke agent access (set to UNTRUSTED)."""
        return self.set_trust_level(agent_id, TrustLevel.UNTRUSTED, reason)
    
    def delete_agent(self, agent_id: str) -> bool:
        """Delete agent from registry."""
        if agent_id not in self._trust_registry:
            return False
        
        del self._trust_registry[agent_id]
        return self._save_trust_registry()
    
    def get_trust_statistics(self) -> Dict[str, Any]:
        """Get trust level statistics."""
        stats = {
            "total_agents": len(self._trust_registry),
            "trust_levels": {},
            "recent_registrations": [],
            "access_attempts": 0
        }
        
        # Count trust levels
        for agent_data in self._trust_registry.values():
            trust_level = agent_data["trust_level"].value
            stats["trust_levels"][trust_level] = stats["trust_levels"].get(trust_level, 0) + 1
            
            # Count recent registrations (last 24 hours)
            if time.time() - agent_data.get("created_at", 0) < 86400:
                stats["recent_registrations"].append({
                    "agent_id": agent_data.get("agent_id"),
                    "trust_level": trust_level,
                    "created_at": agent_data.get("created_at")
                })
            
            # Count total access attempts
            stats["access_attempts"] += len(agent_data.get("access_log", []))
        
        return stats
    
    def enforce_filesystem_access(self, agent_id: str, path: str, action: str) -> bool:
        """Enforce filesystem access for agent."""
        if not self.check_permission(agent_id, "filesystem", action):
            self.log_access(agent_id, "filesystem", action, path, False, "Permission denied")
            return False
        
        # Also check permissions engine
        if not permissions_engine.is_path_allowed(path, action):
            self.log_access(agent_id, "filesystem", action, path, False, "Path not allowed")
            return False
        
        self.log_access(agent_id, "filesystem", action, path, True)
        return True
    
    def enforce_chaos_access(self, agent_id: str, action: str, filename: str = None) -> bool:
        """Enforce CHAOS access for agent."""
        if not self.check_permission(agent_id, "chaos", action):
            self.log_access(agent_id, "chaos", action, filename, False, "Permission denied")
            return False
        
        self.log_access(agent_id, "chaos", action, filename, True)
        return True
    
    def enforce_context_access(self, agent_id: str, action: str) -> bool:
        """Enforce context access for agent."""
        if not self.check_permission(agent_id, "context", action):
            self.log_access(agent_id, "context", action, None, False, "Permission denied")
            return False
        
        self.log_access(agent_id, "context", action, None, True)
        return True
    
    def enforce_media_access(self, agent_id: str, action: str, media_id: str = None) -> bool:
        """Enforce media access for agent."""
        if not self.check_permission(agent_id, "media", action):
            self.log_access(agent_id, "media", action, media_id, False, "Permission denied")
            return False
        
        self.log_access(agent_id, "media", action, media_id, True)
        return True
    
    def enforce_permissions_access(self, agent_id: str, action: str) -> bool:
        """Enforce permissions access for agent."""
        if not self.check_permission(agent_id, "permissions", action):
            self.log_access(agent_id, "permissions", action, None, False, "Permission denied")
            return False
        
        self.log_access(agent_id, "permissions", action, None, True)
        return True

# Global agent trust engine instance
agent_trust_engine = AgentTrustEngine()
