#!/usr/bin/env python3
"""
EdenOS MCP Server Hub - Context Engine
Manages context window memory system with persistence and merging.
"""

import json
import os
import time
from typing import Dict, Any, List, Optional
from collections import deque

class ContextEngine:
    """Manages context window memory system."""
    
    def __init__(self, context_file: str = "context-window.json", max_window_size: int = 100):
        self.context_file = context_file
        self.max_window_size = max_window_size
        self.hub = None  # Nerve hook
        
        # In-memory context window (deque for efficient operations)
        self._window: deque = deque(maxlen=max_window_size)
        
        # Context metadata
        self._metadata: Dict[str, Any] = {
            "created_at": time.time(),
            "updated_at": time.time(),
            "total_entries": 0,
            "window_size": max_window_size
        }
        
        # Load existing context
        self._load_context()
    
    def on_boot(self, hub):
        """Nerve hook: Initialize with hub and subscribe to events."""
        self.hub = hub
        hub.event_bus.subscribe("system_event", self.handle_event)
    
    def handle_event(self, event: dict):
        """Handle system events."""
        event_type = event.get("type")
        payload = event.get("payload", {})
        
        # React to relevant events
        if event_type == "chaos.file.created":
            self.add_text(f"CHAOS file created: {payload.get('filename')}", "chaos_system")
        elif event_type == "chaos.file.updated":
            self.add_text(f"CHAOS file updated: {payload.get('filename')}", "chaos_system")
        elif event_type == "filesystem.deleted":
            self.add_text(f"File deleted: {payload.get('path')}", "filesystem_system")
        elif event_type == "agent.trust.changed":
            self.add_text(f"Agent trust changed: {payload.get('agent_id')} -> {payload.get('level')}", "governance_system")
        elif event_type == "media.registered":
            self.add_text(f"Media registered: {payload.get('file_path')}", "media_system")
        elif event_type == "agent.intent.proposed":
            intent = payload.get("intent")
            if intent == "add_context_note":
                self.add_text(
                    payload.get("text"),
                    source=payload.get("source", "agent")
                )
    
    def _load_context(self):
        """Load context from file."""
        try:
            if os.path.exists(self.context_file):
                with open(self.context_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                # Load window
                window_data = data.get("window", [])
                self._window = deque(window_data, maxlen=self.max_window_size)
                
                # Load metadata
                self._metadata = data.get("metadata", self._metadata)
                self._metadata["window_size"] = self.max_window_size
                
        except Exception as e:
            print(f"[ContextEngine] Failed to load context: {e}")
            self._window = deque(maxlen=self.max_window_size)
    
    def _save_context(self) -> bool:
        """Save context to file."""
        try:
            data = {
                "window": list(self._window),
                "metadata": {
                    **self._metadata,
                    "updated_at": time.time(),
                    "total_entries": len(self._window)
                }
            }
            
            with open(self.context_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            
            return True
            
        except Exception as e:
            print(f"[ContextEngine] Failed to save context: {e}")
            return False
    
    def add_entry(self, entry: Dict[str, Any], source: str = "unknown") -> bool:
        """Add an entry to the context window."""
        if not entry:
            return False
        
        # Create context entry with metadata
        context_entry = {
            "id": f"{int(time.time() * 1000)}_{len(self._window)}",
            "timestamp": time.time(),
            "source": source,
            "entry": entry
        }
        
        self._window.append(context_entry)
        self._metadata["updated_at"] = time.time()
        
        # Emit context entry added event
        if self.hub:
            self.hub.emit("context.entry.added", {
                "entry_id": context_entry["id"],
                "source": source,
                "timestamp": context_entry["timestamp"]
            })
        
        return self._save_context()
    
    def add_text(self, text: str, source: str = "unknown", metadata: Optional[Dict] = None) -> bool:
        """Add a text entry to the context window."""
        if not text:
            return False
        
        entry = {
            "type": "text",
            "content": text,
            "metadata": metadata or {}
        }
        
        return self.add_entry(entry, source)
    
    def add_event(self, event_type: str, details: Dict[str, Any], source: str = "system") -> bool:
        """Add an event entry to the context window."""
        entry = {
            "type": "event",
            "event_type": event_type,
            "details": details
        }
        
        return self.add_entry(entry, source)
    
    def add_query_response(self, query: str, response: str, source: str = "agent") -> bool:
        """Add a query-response pair to the context window."""
        entry = {
            "type": "query_response",
            "query": query,
            "response": response
        }
        
        return self.add_entry(entry, source)
    
    def get_recent_entries(self, count: int = 10) -> List[Dict[str, Any]]:
        """Get the most recent entries from the context window."""
        return list(self._window)[-count:]
    
    def get_entries_by_source(self, source: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get entries from a specific source."""
        entries = [entry for entry in self._window if entry.get("source") == source]
        
        if limit:
            return entries[-limit:]
        
        return entries
    
    def get_entries_by_type(self, entry_type: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get entries of a specific type."""
        entries = [entry for entry in self._window 
                  if entry.get("entry", {}).get("type") == entry_type]
        
        if limit:
            return entries[-limit:]
        
        return entries
    
    def search_entries(self, query: str, search_field: str = "content") -> List[Dict[str, Any]]:
        """Search entries for text content."""
        query_lower = query.lower()
        matches = []
        
        for entry in self._window:
            entry_data = entry.get("entry", {})
            
            # Search in specified field
            if search_field in entry_data:
                content = str(entry_data[search_field]).lower()
                if query_lower in content:
                    matches.append(entry)
            
            # Also search in all string fields if not found
            else:
                for key, value in entry_data.items():
                    if isinstance(value, str) and query_lower in value.lower():
                        matches.append(entry)
                        break
        
        return matches
    
    def get_window_summary(self) -> Dict[str, Any]:
        """Get a summary of the current context window."""
        if not self._window:
            return {
                "size": 0,
                "sources": [],
                "types": [],
                "time_range": None,
                "metadata": self._metadata
            }
        
        sources = set()
        types = set()
        timestamps = []
        
        for entry in self._window:
            sources.add(entry.get("source", "unknown"))
            entry_type = entry.get("entry", {}).get("type", "unknown")
            types.add(entry_type)
            timestamps.append(entry.get("timestamp", 0))
        
        return {
            "size": len(self._window),
            "max_size": self.max_window_size,
            "sources": list(sources),
            "types": list(types),
            "time_range": {
                "earliest": min(timestamps),
                "latest": max(timestamps)
            },
            "metadata": self._metadata
        }
    
    def clear_window(self) -> bool:
        """Clear the context window."""
        self._window.clear()
        self._metadata["updated_at"] = time.time()
        
        return self._save_context()
    
    def resize_window(self, new_size: int) -> bool:
        """Resize the context window."""
        if new_size <= 0:
            return False
        
        old_window = list(self._window)
        self._window = deque(old_window[-new_size:], maxlen=new_size)
        self.max_window_size = new_size
        self._metadata["window_size"] = new_size
        self._metadata["updated_at"] = time.time()
        
        return self._save_context()
    
    def export_context(self, export_path: str, format_type: str = "json") -> bool:
        """Export context to external file."""
        try:
            data = {
                "window": list(self._window),
                "metadata": self._metadata,
                "exported_at": time.time(),
                "format": format_type
            }
            
            if format_type == "json":
                with open(export_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
            
            elif format_type == "txt":
                with open(export_path, "w", encoding="utf-8") as f:
                    f.write("Context Window Export\n")
                    f.write(f"Exported: {time.ctime()}\n")
                    f.write(f"Size: {len(self._window)} entries\n\n")
                    
                    for i, entry in enumerate(self._window):
                        f.write(f"Entry {i+1}:\n")
                        f.write(f"  ID: {entry.get('id')}\n")
                        f.write(f"  Timestamp: {time.ctime(entry.get('timestamp', 0))}\n")
                        f.write(f"  Source: {entry.get('source')}\n")
                        f.write(f"  Data: {json.dumps(entry.get('entry'), indent=2)}\n\n")
            
            return True
            
        except Exception as e:
            print(f"[ContextEngine] Failed to export context: {e}")
            return False
    
    def import_context(self, import_path: str, merge_strategy: str = "append") -> bool:
        """Import context from external file."""
        try:
            with open(import_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            imported_window = data.get("window", [])
            
            if merge_strategy == "append":
                # Append imported entries
                for entry in imported_window:
                    self._window.append(entry)
            
            elif merge_strategy == "replace":
                # Replace entire window
                self._window = deque(imported_window, maxlen=self.max_window_size)
            
            elif merge_strategy == "merge":
                # Merge with deduplication by ID
                existing_ids = {entry.get("id") for entry in self._window}
                for entry in imported_window:
                    if entry.get("id") not in existing_ids:
                        self._window.append(entry)
            
            self._metadata["updated_at"] = time.time()
            return self._save_context()
            
        except Exception as e:
            print(f"[ContextEngine] Failed to import context: {e}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get detailed statistics about the context window."""
        if not self._window:
            return {"total_entries": 0}
        
        source_counts = {}
        type_counts = {}
        hourly_activity = {}
        
        for entry in self._window:
            # Count sources
            source = entry.get("source", "unknown")
            source_counts[source] = source_counts.get(source, 0) + 1
            
            # Count types
            entry_type = entry.get("entry", {}).get("type", "unknown")
            type_counts[entry_type] = type_counts.get(entry_type, 0) + 1
            
            # Hourly activity
            timestamp = entry.get("timestamp", 0)
            hour = time.strftime("%H", time.localtime(timestamp))
            hourly_activity[hour] = hourly_activity.get(hour, 0) + 1
        
        return {
            "total_entries": len(self._window),
            "source_distribution": source_counts,
            "type_distribution": type_counts,
            "hourly_activity": hourly_activity,
            "window_utilization": len(self._window) / self.max_window_size,
            "metadata": self._metadata
        }

# Global context engine instance
context_engine = ContextEngine()
