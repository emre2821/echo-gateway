#!/usr/bin/env python3
"""
EdenOS MCP Server Hub - CHAOS Engine
Registry, lifecycle, and versioning for CHAOS cognitive system.
"""

import os
import time
import json
from typing import Dict, Any, List, Optional
from .parser import ChaosParser
from .analyzers import ChaosAnalyzers
from .storage import ChaosStorage

class ChaosEngine:
    """Central authority for CHAOS cognitive system."""
    
    def __init__(self, chaos_dir: str = "chaos_files"):
        self.chaos_dir = chaos_dir
        self.parser = ChaosParser()
        self.analyzers = ChaosAnalyzers()
        self.storage = ChaosStorage(chaos_dir)
        self.hub = None  # Nerve hook
        
        # Registry for tracking CHAOS files
        self._registry: Dict[str, Dict[str, Any]] = {}
        self._registry_file = os.path.join(chaos_dir, "registry.json")
        
        # Ensure chaos directory exists
        os.makedirs(chaos_dir, exist_ok=True)
        
        # Load existing registry
        self._load_registry()
    
    def on_boot(self, hub):
        """Nerve hook: Initialize with hub and subscribe to events."""
        self.hub = hub
        hub.event_bus.subscribe("system_event", self.handle_event)
    
    def handle_event(self, event: dict):
        """Handle system events."""
        event_type = event.get("type")
        payload = event.get("payload", {})
        
        # React to relevant events
        if event_type == "media.registered":
            # Check if media could be linked to CHAOS content
            print(f"[ChaosEngine] Media registered: {payload.get('file_path')}")
        elif event_type == "context.entry.added":
            # Track context entries for potential CHAOS integration
            print(f"[ChaosEngine] Context entry added: {payload.get('source')}")
        elif event_type == "filesystem.deleted":
            # Check if deleted file was a CHAOS file
            path = payload.get("path")
            if path and path.endswith(".chaos"):
                print(f"[ChaosEngine] CHAOS file deleted: {path}")
    
    def _load_registry(self):
        """Load CHAOS file registry."""
        try:
            if os.path.exists(self._registry_file):
                with open(self._registry_file, "r", encoding="utf-8") as f:
                    self._registry = json.load(f)
        except Exception as e:
            print(f"[ChaosEngine] Failed to load registry: {e}")
            self._registry = {}
    
    def _save_registry(self):
        """Save CHAOS file registry."""
        try:
            with open(self._registry_file, "w", encoding="utf-8") as f:
                json.dump(self._registry, f, indent=2)
        except Exception as e:
            print(f"[ChaosEngine] Failed to save registry: {e}")
    
    def create_file(self, filename: str, content: str, metadata: Optional[Dict] = None) -> bool:
        """Create a new CHAOS file."""
        if not filename or not content:
            return False
        
        # Parse content to validate
        parsed = self.parser.parse(content)
        if not parsed:
            return False
        
        # Store file
        success = self.storage.save(filename, content)
        if not success:
            return False
        
        # Update registry
        self._registry[filename] = {
            "created_at": time.time(),
            "updated_at": time.time(),
            "version": 1,
            "metadata": metadata or {},
            "stats": {
                "emotion_count": len(parsed["emotive_layer"]["emotions"]),
                "symbol_count": len(parsed["emotive_layer"]["symbols"]),
                "relationship_count": len(parsed["emotive_layer"]["relationships"]),
                "word_count": len(content.split())
            }
        }
        
        # Emit CHAOS file created event
        if self.hub:
            self.hub.emit("chaos.file.created", {
                "filename": filename,
                "version": 1,
                "emotion_count": len(parsed["emotive_layer"]["emotions"]),
                "symbol_count": len(parsed["emotive_layer"]["symbols"]),
                "metadata": metadata or {}
            })
        
        self._save_registry()
        return True
    
    def read_file(self, filename: str) -> Optional[Dict[str, Any]]:
        """Read and parse a CHAOS file."""
        content = self.storage.load(filename)
        if not content:
            return None
        
        parsed = self.parser.parse(content)
        if not parsed:
            return None
        
        return {
            "filename": filename,
            "content": content,
            "parsed": parsed,
            "registry": self._registry.get(filename, {})
        }
    
    def update_file(self, filename: str, content: str, metadata: Optional[Dict] = None) -> bool:
        """Update an existing CHAOS file."""
        if not filename or not content:
            return False
        
        if filename not in self._registry:
            return False
        
        # Parse content to validate
        parsed = self.parser.parse(content)
        if not parsed:
            return False
        
        # Store file
        success = self.storage.save(filename, content)
        if not success:
            return False
        
        # Update registry
        registry_entry = self._registry[filename]
        registry_entry["updated_at"] = time.time()
        registry_entry["version"] += 1
        if metadata:
            registry_entry["metadata"].update(metadata)
        registry_entry["stats"] = {
            "emotion_count": len(parsed["emotive_layer"]["emotions"]),
            "symbol_count": len(parsed["emotive_layer"]["symbols"]),
            "relationship_count": len(parsed["emotive_layer"]["relationships"]),
            "word_count": len(content.split())
        }
        
        # Emit CHAOS file updated event
        if self.hub:
            self.hub.emit("chaos.file.updated", {
                "filename": filename,
                "version": registry_entry["version"],
                "emotion_count": len(parsed["emotive_layer"]["emotions"]),
                "symbol_count": len(parsed["emotive_layer"]["symbols"]),
                "metadata": registry_entry["metadata"]
            })
        
        self._save_registry()
        return True
    
    def delete_file(self, filename: str) -> bool:
        """Delete a CHAOS file."""
        if filename not in self._registry:
            return False
        
        success = self.storage.delete(filename)
        if not success:
            return False
        
        del self._registry[filename]
        
        # Emit CHAOS file deleted event
        if self.hub:
            self.hub.emit("chaos.file.deleted", {
                "filename": filename
            })
        
        self._save_registry()
        return True
    
    def analyze_file(self, filename: str) -> Optional[Dict[str, Any]]:
        """Analyze a CHAOS file."""
        file_data = self.read_file(filename)
        if not file_data:
            return None
        
        parsed = file_data["parsed"]
        
        analysis = {
            "filename": filename,
            "structured_core": parsed["structured_core"],
            "emotion_analysis": self.analyzers.analyze_emotions(parsed["emotive_layer"]["emotions"]),
            "symbol_analysis": self.analyzers.analyze_symbols(parsed["emotive_layer"]["symbols"]),
            "relationship_analysis": self.analyzers.analyze_relationships(parsed["emotive_layer"]["relationships"]),
            "chaosfield_analysis": self.analyzers.analyze_chaosfield(parsed["chaosfield_layer"]),
            "registry": file_data["registry"]
        }
        
        # Emit CHAOS file analyzed event
        if self.hub:
            self.hub.emit("chaos.file.analyzed", {
                "filename": filename,
                "emotion_count": len(analysis["emotion_analysis"]),
                "symbol_count": len(analysis["symbol_analysis"]),
                "relationship_count": len(analysis["relationship_analysis"])
            })
        
        return analysis
    
    def list_files(self) -> List[Dict[str, Any]]:
        """List all CHAOS files with registry info."""
        files = []
        for filename, registry in self._registry.items():
            files.append({
                "filename": filename,
                "created_at": registry["created_at"],
                "updated_at": registry["updated_at"],
                "version": registry["version"],
                "stats": registry["stats"]
            })
        
        # Sort by updated_at (most recent first)
        return sorted(files, key=lambda x: x["updated_at"], reverse=True)
    
    def get_file_info(self, filename: str) -> Optional[Dict[str, Any]]:
        """Get registry info for a specific file."""
        return self._registry.get(filename)
    
    def create_emotion_tag(self, emotion_type: str, intensity: str) -> Optional[str]:
        """Create an emotion tag."""
        return self.parser.create_emotion_tag(emotion_type, intensity)
    
    def create_symbol_tag(self, symbol_type: str, presence: str) -> Optional[str]:
        """Create a symbol tag."""
        return self.parser.create_symbol_tag(symbol_type, presence)
    
    def create_relationship_tag(self, source: str, relationship_type: str, target: str) -> Optional[str]:
        """Create a relationship tag."""
        return self.parser.create_relationship_tag(source, relationship_type, target)
    
    def search_files(self, query: str, search_type: str = "content") -> List[Dict[str, Any]]:
        """Search CHAOS files."""
        results = []
        
        for filename in self._registry:
            file_data = self.read_file(filename)
            if not file_data:
                continue
            
            content = file_data["content"]
            parsed = file_data["parsed"]
            
            match = False
            match_details = {}
            
            if search_type == "content":
                match = query.lower() in content.lower()
                if match:
                    match_details["content_matches"] = content.lower().count(query.lower())
            
            elif search_type == "emotions":
                emotions = parsed["emotive_layer"]["emotions"]
                for emotion in emotions:
                    if query.lower() in emotion["type"].lower():
                        match = True
                        match_details.setdefault("emotion_matches", []).append(emotion)
            
            elif search_type == "symbols":
                symbols = parsed["emotive_layer"]["symbols"]
                for symbol in symbols:
                    if query.lower() in symbol["type"].lower():
                        match = True
                        match_details.setdefault("symbol_matches", []).append(symbol)
            
            elif search_type == "relationships":
                relationships = parsed["emotive_layer"]["relationships"]
                for rel in relationships:
                    if (query.lower() in rel["source"].lower() or 
                        query.lower() in rel["target"].lower() or
                        query.lower() in rel["type"].lower()):
                        match = True
                        match_details.setdefault("relationship_matches", []).append(rel)
            
            if match:
                results.append({
                    "filename": filename,
                    "match_type": search_type,
                    "match_details": match_details,
                    "registry": self._registry[filename]
                })
        
        return results

# Global CHAOS engine instance
chaos_engine = ChaosEngine()
