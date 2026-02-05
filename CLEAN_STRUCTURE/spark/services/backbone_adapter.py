#!/usr/bin/env python3
"""
EdenOS MCP Server Hub - Backbone Adapter
Connects DCA, AoE, CHAOS Backbone, and EdenOS to the event bus.
No direct calls - all communication through events.
"""

import time
from typing import Dict, Any

class BackboneAdapter:
    """Adapter for backbone systems to participate in event nervous system."""
    
    def __init__(self):
        self.hub = None
        self.active_connections = {}
        
    def on_boot(self, hub):
        """Nerve hook: Initialize with hub and subscribe to events."""
        self.hub = hub
        hub.event_bus.subscribe("system_event", self.handle_event)
        
        # Register as backbone system
        self.active_connections["backbone_adapter"] = {
            "name": "Eden Backbone Adapter",
            "connected_at": time.time(),
            "status": "active"
        }
        
        print("[BackboneAdapter] Backbone adapter initialized")
    
    def handle_event(self, event: dict):
        """Handle system events and forward to backbone systems."""
        event_type = event.get("type")
        payload = event.get("payload", {})
        
        # Forward relevant events to backbone systems
        if self._should_forward_to_backbone(event_type):
            self._emit_to_backbone("backbone.dca.event", {
                "original_event": event_type,
                "payload": payload,
                "timestamp": time.time()
            })
    
    def _should_forward_to_backbone(self, event_type: str) -> bool:
        """Determine if event should be forwarded to backbone."""
        # Forward critical system events and cognitive events
        backbone_relevant_events = {
            "chaos.file.created",
            "chaos.file.updated", 
            "chaos.file.analyzed",
            "agent.trust.changed",
            "permissions.denied",
            "system.warning",
            "system.error"
        }
        return event_type in backbone_relevant_events
    
    def _emit_to_backbone(self, backbone_event: str, payload: Dict[str, Any]):
        """Emit event to backbone systems."""
        if self.hub:
            self.hub.emit(backbone_event, payload)
    
    # DCA Integration Methods
    def emit_dca_event(self, event_name: str, data: Dict[str, Any]):
        """Emit DCA lifecycle event."""
        self._emit_to_backbone("backbone.dca.event", {
            "dca_event": event_name,
            "data": data,
            "source": "dca_adapter",
            "timestamp": time.time()
        })
    
    def handle_dca_response(self, response: Dict[str, Any]):
        """Handle response from DCA system."""
        self._emit_to_backbone("backbone.dca.response", {
            "response": response,
            "timestamp": time.time()
        })
    
    # AoE Integration Methods  
    def emit_aoe_event(self, event_name: str, data: Dict[str, Any]):
        """Emit AoE lifecycle event."""
        self._emit_to_backbone("backbone.aoe.event", {
            "aoe_event": event_name,
            "data": data,
            "source": "aoe_adapter", 
            "timestamp": time.time()
        })
    
    def handle_aoe_lifecycle(self, lifecycle_data: Dict[str, Any]):
        """Handle AoE lifecycle changes."""
        self._emit_to_backbone("backbone.aoe.lifecycle", {
            "lifecycle_data": lifecycle_data,
            "timestamp": time.time()
        })
    
    # CHAOS Backbone Integration
    def emit_chaos_backbone_ping(self, chaos_data: Dict[str, Any]):
        """Emit CHAOS backbone ping."""
        self._emit_to_backbone("backbone.chaos.ping", {
            "chaos_data": chaos_data,
            "source": "chaos_backbone_adapter",
            "timestamp": time.time()
        })
    
    def handle_chaos_backbone_response(self, response: Dict[str, Any]):
        """Handle response from CHAOS backbone."""
        self._emit_to_backbone("backbone.chaos.response", {
            "response": response,
            "timestamp": time.time()
        })
    
    # EdenOS Integration
    def emit_eden_heartbeat(self, system_status: Dict[str, Any]):
        """Emit EdenOS heartbeat."""
        self._emit_to_backbone("backbone.eden.heartbeat", {
            "system_status": system_status,
            "source": "edenos_adapter",
            "timestamp": time.time()
        })
    
    def handle_edenos_command(self, command: Dict[str, Any]):
        """Handle command from EdenOS."""
        self._emit_to_backbone("backbone.eden.command", {
            "command": command,
            "timestamp": time.time()
        })
    
    # Connection Management
    def register_backbone_system(self, system_name: str, system_info: Dict[str, Any]):
        """Register a backbone system."""
        self.active_connections[system_name] = {
            **system_info,
            "connected_at": time.time(),
            "status": "active"
        }
        
        self._emit_to_backbone("backbone.system.registered", {
            "system_name": system_name,
            "system_info": system_info
        })
    
    def unregister_backbone_system(self, system_name: str):
        """Unregister a backbone system."""
        if system_name in self.active_connections:
            self.active_connections[system_name]["status"] = "disconnected"
            self.active_connections[system_name]["disconnected_at"] = time.time()
            
            self._emit_to_backbone("backbone.system.unregistered", {
                "system_name": system_name
            })
    
    def get_active_connections(self) -> Dict[str, Any]:
        """Get list of active backbone connections."""
        return {
            "connections": self.active_connections,
            "total_active": len([c for c in self.active_connections.values() if c.get("status") == "active"]),
            "timestamp": time.time()
        }
    
    # Health Monitoring
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on backbone connections."""
        healthy_connections = []
        unhealthy_connections = []
        
        for name, info in self.active_connections.items():
            if info.get("status") == "active":
                # Check if connection is stale (older than 5 minutes)
                if time.time() - info.get("connected_at", 0) < 300:
                    healthy_connections.append(name)
                else:
                    unhealthy_connections.append(name)
            else:
                unhealthy_connections.append(name)
        
        return {
            "healthy": healthy_connections,
            "unhealthy": unhealthy_connections,
            "total": len(self.active_connections),
            "health_score": len(healthy_connections) / max(len(self.active_connections), 1),
            "timestamp": time.time()
        }

# Global backbone adapter instance
backbone_adapter = BackboneAdapter()
