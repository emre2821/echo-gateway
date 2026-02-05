#!/usr/bin/env python3
"""
EdenOS MCP Server Hub - CHAOS Parser
Parses CHAOS file format into structured data.
"""

from typing import Dict, Any, List, Optional

class ChaosParser:
    """Parses CHAOS file format into structured data."""
    
    def parse(self, content: str) -> Optional[Dict[str, Any]]:
        """Parse a CHAOS file into structured data."""
        if not content:
            return None
        
        lines = content.split('\n')
        
        result = {
            "structured_core": {},
            "emotive_layer": {
                "emotions": [],
                "symbols": [],
                "relationships": []
            },
            "chaosfield_layer": ""
        }
        
        current_section = "structured_core"
        chaosfield_content = []
        
        for line in lines:
            line = line.strip()
            
            if line.startswith("---EMOTIVE_LAYER---"):
                current_section = "emotive_layer"
            elif line.startswith("---CHAOSFIELD_LAYER---"):
                current_section = "chaosfield_layer"
            elif line.startswith("[EMOTION:"):
                # Parse emotion tag: [EMOTION:joy:HIGH]
                parts = line[1:-1].split(':')
                if len(parts) >= 3:
                    emotion_type = parts[1]
                    intensity = parts[2]
                    result["emotive_layer"]["emotions"].append({
                        "type": emotion_type,
                        "intensity": intensity
                    })
            elif line.startswith("[SYMBOL:"):
                # Parse symbol tag: [SYMBOL:fire:STRONG]
                parts = line[1:-1].split(':')
                if len(parts) >= 3:
                    symbol_type = parts[1]
                    presence = parts[2]
                    result["emotive_layer"]["symbols"].append({
                        "type": symbol_type,
                        "presence": presence
                    })
            elif line.startswith("[RELATIONSHIP:"):
                # Parse relationship tag: [RELATIONSHIP:user:loves:eden]
                parts = line[1:-1].split(':')
                if len(parts) >= 4:
                    source = parts[1]
                    rel_type = parts[2]
                    target = parts[3]
                    result["emotive_layer"]["relationships"].append({
                        "source": source,
                        "type": rel_type,
                        "target": target
                    })
            elif current_section == "chaosfield_layer":
                chaosfield_content.append(line)
                result["chaosfield_layer"] = "\n".join(chaosfield_content)
            elif line.startswith('[') and ']:' in line and current_section == "structured_core":
                key = line[1:line.index(']')]
                value = line[line.index(']:') + 2:].strip()
                result["structured_core"][key] = value
        
        return result
    
    def create_emotion_tag(self, emotion_type: str, intensity: str) -> Optional[str]:
        """Create an emotion tag for a CHAOS file."""
        if not emotion_type or not intensity:
            return None
        
        valid_intensities = ["EXTREME", "HIGH", "MEDIUM", "LOW", "MINIMAL"]
        if intensity.upper() not in valid_intensities:
            return None
        
        return f"[EMOTION:{emotion_type.upper()}:{intensity.upper()}]"
    
    def create_symbol_tag(self, symbol_type: str, presence: str) -> Optional[str]:
        """Create a symbol tag for a CHAOS file."""
        if not symbol_type or not presence:
            return None
        
        valid_presences = ["STRONG", "PRESENT", "WEAK"]
        if presence.upper() not in valid_presences:
            return None
        
        return f"[SYMBOL:{symbol_type.upper()}:{presence.upper()}]"
    
    def create_relationship_tag(self, source: str, relationship_type: str, target: str) -> Optional[str]:
        """Create a relationship tag for a CHAOS file."""
        if not source or not relationship_type or not target:
            return None
        
        return f"[RELATIONSHIP:{source.upper()}:{relationship_type.upper()}:{target.upper()}]"
    
    def validate_tag(self, tag: str) -> Optional[Dict[str, Any]]:
        """Validate and parse a CHAOS tag."""
        if not tag.startswith('[') or not tag.endswith(']'):
            return None
        
        content = tag[1:-1]
        parts = content.split(':')
        
        if len(parts) < 2:
            return None
        
        tag_type = parts[0]
        
        if tag_type == "EMOTION":
            if len(parts) >= 3:
                return {
                    "type": "EMOTION",
                    "emotion_type": parts[1],
                    "intensity": parts[2],
                    "valid": parts[2].upper() in ["EXTREME", "HIGH", "MEDIUM", "LOW", "MINIMAL"]
                }
        
        elif tag_type == "SYMBOL":
            if len(parts) >= 3:
                return {
                    "type": "SYMBOL",
                    "symbol_type": parts[1],
                    "presence": parts[2],
                    "valid": parts[2].upper() in ["STRONG", "PRESENT", "WEAK"]
                }
        
        elif tag_type == "RELATIONSHIP":
            if len(parts) >= 4:
                return {
                    "type": "RELATIONSHIP",
                    "source": parts[1],
                    "relationship_type": parts[2],
                    "target": parts[3],
                    "valid": True
                }
        
        return {"type": "UNKNOWN", "valid": False}
    
    def extract_tags(self, content: str) -> List[Dict[str, Any]]:
        """Extract all tags from CHAOS content."""
        tags = []
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if line.startswith('[') and ']' in line:
                tag_end = line.find(']')
                tag = line[:tag_end + 1]
                parsed = self.validate_tag(tag)
                if parsed:
                    tags.append(parsed)
        
        return tags
