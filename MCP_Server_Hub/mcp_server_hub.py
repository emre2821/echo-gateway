#!/usr/bin/env python3
"""
EdenOS MCP Server Hub
Unified MCP server aggregating tools from multiple Eden ecosystem servers.

Combines tools from:
- Eden Context Window MCP (context management)
- CHAOS MCP Server (CHAOS file processing)
- EdenOS MCP Server (filesystem, permissions, organizer)
- Additional filesystem and utility tools

Author: Cascade AI Assistant
"""

import datetime
import json
import os
import random
import sys
import shutil
import uuid
import time
import inspect
from pathlib import Path
from typing import Dict, Any, List, Optional
import hashlib
import git
import tarfile
import zipfile

from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
server = FastMCP("eden-mcp-server-hub")

# Configuration
CONTEXT_FILE = "context-window.json"
PERMISSIONS_FILE = "permissions.json"
CHAOS_FILES_DIR = "chaos_files"
MEDIA_FILES_DIR = "media_files"

# Ensure directories exist
os.makedirs(CHAOS_FILES_DIR, exist_ok=True)
os.makedirs(MEDIA_FILES_DIR, exist_ok=True)

# Mock databases (in production, these would be persistent storage)
chaos_files = {}
media_files = {}

# Exclusion zones for file operations
EXCLUSION_ZONES = [
    r"C:\Windows",
    r"C:\Program Files",
    r"C:\Program Files (x86)",
]

def is_excluded(path: str) -> bool:
    """Check if path is in exclusion zones."""
    if not path:
        return True
    normalized = os.path.abspath(path)
    for ex in EXCLUSION_ZONES:
        if normalized.startswith(os.path.abspath(ex)):
            return True
    return False

def _make_id():
    return uuid.uuid4().hex

def _load_permissions():
    try:
        if os.path.exists(PERMISSIONS_FILE):
            with open(PERMISSIONS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = {"permissions": {}, "requests": {}, "audit": [], "allowed_paths": [], "exclusion_zones": EXCLUSION_ZONES}
            _save_permissions(data)
    except Exception:
        data = {"permissions": {}, "requests": {}, "audit": [], "allowed_paths": [], "exclusion_zones": EXCLUSION_ZONES}
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

def is_path_allowed(path: str, operation: str = "read") -> bool:
    """Check if path is allowed based on allowed_paths."""
    if not path:
        return False
    
    data = _load_permissions()
    allowed_paths = data.get("allowed_paths", [])
    
    normalized_path = os.path.abspath(path)
    
    for allowed in allowed_paths:
        if isinstance(allowed, str):
            allowed_path = os.path.abspath(allowed)
            if normalized_path.startswith(allowed_path):
                return True
        elif isinstance(allowed, dict):
            allowed_path = os.path.abspath(allowed["path"])
            if normalized_path.startswith(allowed_path):
                if operation == "read" or not allowed.get("read_only", False):
                    return True
    
    return False

# Context Window Management (translated from JS)
def load_context():
    try:
        if os.path.exists(CONTEXT_FILE):
            with open(CONTEXT_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        else:
            context = {
                "windows": {},
                "activeWindow": None,
                "metadata": {
                    "created": datetime.datetime.now().isoformat(),
                    "lastModified": datetime.datetime.now().isoformat()
                }
            }
            save_context(context)
            return context
    except Exception:
        return {"windows": {}, "activeWindow": None}

def save_context(context):
    context["metadata"]["lastModified"] = datetime.datetime.now().isoformat()
    with open(CONTEXT_FILE, "w", encoding="utf-8") as f:
        json.dump(context, f, indent=2)

# CHAOS Processing Helpers
def parse_chaos_file(content):
    """Simple parser for CHAOS files."""
    result = {
        "structured_core": {},
        "emotive_layer": {
            "emotions": [],
            "symbols": [],
            "relationships": []
        },
        "chaosfield_layer": ""
    }

    lines = content.strip().split('\n')
    current_section = "structured_core"

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if line.startswith('[EMOTION:'):
            current_section = "emotive_layer"
            parts = line.strip('[]').split(':')
            if len(parts) >= 3:
                result["emotive_layer"]["emotions"].append({
                    "type": parts[1],
                    "intensity": parts[2]
                })
        elif line.startswith('[SYMBOL:'):
            current_section = "emotive_layer"
            parts = line.strip('[]').split(':')
            if len(parts) >= 3:
                result["emotive_layer"]["symbols"].append({
                    "type": parts[1],
                    "presence": parts[2]
                })
        elif line.startswith('[RELATIONSHIP:'):
            current_section = "emotive_layer"
            parts = line.strip('[]').split(':')
            if len(parts) >= 4:
                result["emotive_layer"]["relationships"].append({
                    "source": parts[1],
                    "type": parts[2],
                    "target": parts[3]
                })
        elif line.startswith('{'):
            current_section = "chaosfield_layer"
            chaosfield_content = []
            chaosfield_index = lines.index(line)
            for i in range(chaosfield_index + 1, len(lines)):
                if lines[i].strip().startswith('}'):
                    break
                chaosfield_content.append(lines[i].strip())
            result["chaosfield_layer"] = "\n".join(chaosfield_content)
        elif line.startswith('[') and ']:' in line and current_section == "structured_core":
            key = line[1:line.index(']')]
            value = line[line.index(']:') + 2:].strip()
            result["structured_core"][key] = value

    return result

def analyze_emotions(emotions):
    if not emotions:
        return "No emotions detected."

    intensity_counts = {"EXTREME": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "MINIMAL": 0}
    emotion_types = []

    for emotion in emotions:
        emotion_types.append(emotion["type"])
        if emotion["intensity"] in intensity_counts:
            intensity_counts[emotion["intensity"]] += 1

    dominant_emotion = None
    if emotion_types:
        for emotion in emotions:
            if emotion["intensity"] == "EXTREME":
                dominant_emotion = emotion["type"]
                break
        if not dominant_emotion:
            for emotion in emotions:
                if emotion["intensity"] == "HIGH":
                    dominant_emotion = emotion["type"]
                    break
        if not dominant_emotion and emotions:
            dominant_emotion = emotions[0]["type"]

    intensity_score = 0
    intensity_weights = {"EXTREME": 10, "HIGH": 7, "MEDIUM": 5, "LOW": 3, "MINIMAL": 1}
    for emotion in emotions:
        if emotion["intensity"] in intensity_weights:
            intensity_score += intensity_weights[emotion["intensity"]]
    if emotions:
        intensity_score = min(100, (intensity_score / (len(emotions) * 10)) * 100)

    return {
        "emotion_count": len(emotions),
        "emotion_types": emotion_types,
        "intensity_distribution": intensity_counts,
        "dominant_emotion": dominant_emotion,
        "emotional_intensity_score": intensity_score
    }

def analyze_symbols(symbols):
    if not symbols:
        return "No symbols detected."

    presence_counts = {"STRONG": 0, "PRESENT": 0, "WEAK": 0}
    symbol_types = []

    for symbol in symbols:
        symbol_types.append(symbol["type"])
        if symbol["presence"] in presence_counts:
            presence_counts[symbol["presence"]] += 1

    dominant_symbol = None
    if symbol_types:
        for symbol in symbols:
            if symbol["presence"] == "STRONG":
                dominant_symbol = symbol["type"]
                break
        if not dominant_symbol and symbols:
            dominant_symbol = symbols[0]["type"]

    return {
        "symbol_count": len(symbols),
        "symbol_types": symbol_types,
        "presence_distribution": presence_counts,
        "dominant_symbol": dominant_symbol
    }

def analyze_relationships(relationships):
    if not relationships:
        return "No relationships detected."

    entities = set()
    relationship_types = set()

    for rel in relationships:
        entities.add(rel["source"])
        entities.add(rel["target"])
        relationship_types.add(rel["type"])

    graph = {}
    for entity in entities:
        graph[entity] = {"outgoing": [], "incoming": []}

    for rel in relationships:
        source = rel["source"]
        target = rel["target"]
        rel_type = rel["type"]

        graph[source]["outgoing"].append({
            "target": target,
            "type": rel_type
        })

        graph[target]["incoming"].append({
            "source": source,
            "type": rel_type
        })

    return {
        "relationship_count": len(relationships),
        "entity_count": len(entities),
        "entities": list(entities),
        "relationship_types": list(relationship_types),
        "graph": graph
    }

def analyze_chaosfield(content):
    if not content:
        return "No chaosfield content detected."

    words = content.split()
    word_count = len(words)

    positive_words = ["joy", "happy", "love", "beautiful", "wonderful", "good", "great", "excellent"]
    negative_words = ["sad", "angry", "fear", "hate", "terrible", "bad", "awful", "horrible"]

    positive_count = sum(1 for w in words if w.lower() in positive_words)
    negative_count = sum(1 for w in words if w.lower() in negative_words)

    if positive_count > negative_count:
        sentiment = "Positive"
    elif negative_count > positive_count:
        sentiment = "Negative"
    else:
        sentiment = "Neutral"

    return {
        "word_count": word_count,
        "sentiment": sentiment,
        "positive_words": positive_count,
        "negative_words": negative_count
    }

# Load initial CHAOS files from directory
def load_chaos_files():
    global chaos_files
    chaos_files = {}
    if os.path.exists(CHAOS_FILES_DIR):
        for file in os.listdir(CHAOS_FILES_DIR):
            if file.endswith('.chaosincarnet'):
                filepath = os.path.join(CHAOS_FILES_DIR, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        chaos_files[file] = f.read()
                except Exception:
                    pass

# Save CHAOS file to directory
def save_chaos_file(filename, content):
    filepath = os.path.join(CHAOS_FILES_DIR, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

# Load media files
def load_media_files():
    global media_files
    media_files = {}
    if os.path.exists(MEDIA_FILES_DIR):
        for file in os.listdir(MEDIA_FILES_DIR):
            if file.endswith(('.jpg', '.png', '.mp3', '.json')):
                filepath = os.path.join(MEDIA_FILES_DIR, file)
                try:
                    if file.endswith('.json'):
                        with open(filepath, 'r', encoding='utf-8') as f:
                            media_files[file] = json.load(f)
                    else:
                        # Mock analysis for media files
                        media_files[file] = {
                            "type": "image" if file.endswith(('.jpg', '.png')) else "audio",
                            "description": f"Media file: {file}",
                            "size": os.path.getsize(filepath)
                        }
                except Exception:
                    pass

load_chaos_files()
load_media_files()

# Tool implementations start here

# Context Window Tools
@server.tool()
async def create_context_window(name: str, description: str = "", symbols: List[str] = None) -> str:
    """Create a new context window with symbolic memory capabilities."""
    if symbols is None:
        symbols = []

    context = load_context()
    window_id = _make_id()

    new_window = {
        "id": window_id,
        "name": name,
        "description": description,
        "symbols": symbols,
        "content": [],
        "created": datetime.datetime.now().isoformat(),
        "lastModified": datetime.datetime.now().isoformat()
    }

    context["windows"][window_id] = new_window
    context["activeWindow"] = window_id
    save_context(context)

    return f"Created context window '{name}' with ID: {window_id}"

@server.tool()
async def add_context(content: str, type: str, window_id: str = None, symbols: List[str] = None) -> str:
    """Add context information to active window."""
    if symbols is None:
        symbols = []

    context = load_context()
    target_window_id = window_id or context.get("activeWindow")

    if not target_window_id or target_window_id not in context["windows"]:
        return "Invalid window ID"

    context_entry = {
        "id": _make_id(),
        "content": content,
        "type": type,
        "symbols": symbols,
        "timestamp": datetime.datetime.now().isoformat()
    }

    context["windows"][target_window_id]["content"].append(context_entry)
    context["windows"][target_window_id]["lastModified"] = datetime.datetime.now().isoformat()
    save_context(context)

    return f"Added {type} context to window {target_window_id}"

@server.tool()
async def query_context(query: str, window_id: str = None, symbols: List[str] = None, limit: int = 10) -> str:
    """Query context windows with symbolic reasoning."""
    if symbols is None:
        symbols = []

    context = load_context()
    target_window_id = window_id or context.get("activeWindow")

    if not target_window_id or target_window_id not in context["windows"]:
        return "Invalid window ID"

    window = context["windows"][target_window_id]
    results = window["content"]

    # Filter by symbols if provided
    if symbols:
        results = [item for item in results if any(s in item["symbols"] for s in symbols)]

    # Simple text search
    if query:
        query_lower = query.lower()
        results = [item for item in results if query_lower in item["content"].lower()]

    # Limit results
    results = results[:limit]

    return json.dumps(results, indent=2)

@server.tool()
async def list_windows() -> str:
    """List all available context windows."""
    context = load_context()
    windows = []
    for window in context["windows"].values():
        windows.append({
            "id": window["id"],
            "name": window["name"],
            "description": window["description"],
            "symbols": window["symbols"],
            "contentCount": len(window["content"]),
            "created": window["created"],
            "lastModified": window["lastModified"],
            "isActive": window["id"] == context.get("activeWindow")
        })

    return json.dumps(windows, indent=2)

@server.tool()
async def set_active_window(window_id: str) -> str:
    """Set active context window."""
    context = load_context()

    if window_id not in context["windows"]:
        return "Window ID not found"

    context["activeWindow"] = window_id
    save_context(context)

    window = context["windows"][window_id]
    return f"Set active window to: {window['name']} ({window_id})"

@server.tool()
async def merge_windows(source_windows: List[str], target_window: str, strategy: str = "union") -> str:
    """Merge multiple context windows with symbolic reasoning."""
    context = load_context()

    # Validate source windows exist
    valid_sources = [wid for wid in source_windows if wid in context["windows"]]
    if not valid_sources:
        return "No valid source windows found"

    new_window_id = _make_id()
    merged_content = []
    merged_symbols = set()

    # Collect content and symbols
    for source_id in valid_sources:
        source = context["windows"][source_id]
        merged_content.extend(source["content"])
        merged_symbols.update(source["symbols"])

    # Apply merge strategy
    if strategy == "intersection":
        # Find common content across all windows
        source_contents = [set(w["content"] for w in context["windows"][sid]["content"]) for sid in valid_sources]
        merged_content = [item for item in merged_content if all(item["id"] in sc for sc in source_contents)]

    new_window = {
        "id": new_window_id,
        "name": target_window,
        "description": f"Merged window from {len(valid_sources)} sources using {strategy} strategy",
        "symbols": list(merged_symbols),
        "content": merged_content,
        "created": datetime.datetime.now().isoformat(),
        "lastModified": datetime.datetime.now().isoformat()
    }

    context["windows"][new_window_id] = new_window
    context["activeWindow"] = new_window_id
    save_context(context)

    return f"Created merged window '{target_window}' with ID: {new_window_id}"

# CHAOS Tools
@server.tool()
async def list_chaos_files() -> str:
    """List all available CHAOS files."""
    files = list(chaos_files.keys())
    return json.dumps({"files": files}, ensure_ascii=False)

@server.tool()
async def get_chaos_file(filename: str) -> str:
    """Get the content of a CHAOS file."""
    if not filename:
        return "Error: Filename is required."

    if filename not in chaos_files:
        return f"Error: File '{filename}' not found."

    return chaos_files[filename]

@server.tool()
async def create_chaos_file(filename: str, content: str) -> str:
    """Create a new CHAOS file."""
    if not filename:
        return "Error: Filename is required."

    if not content:
        return "Error: Content is required."

    if not filename.endswith('.chaosincarnet'):
        filename += '.chaosincarnet'

    if filename in chaos_files:
        return f"Error: File '{filename}' already exists."

    chaos_files[filename] = content
    save_chaos_file(filename, content)

    return json.dumps({
        "status": "success",
        "message": f"File '{filename}' created successfully."
    }, ensure_ascii=False)

@server.tool()
async def update_chaos_file(filename: str, content: str) -> str:
    """Update an existing CHAOS file."""
    if not filename:
        return "Error: Filename is required."

    if not content:
        return "Error: Content is required."

    if filename not in chaos_files:
        return f"Error: File '{filename}' not found."

    chaos_files[filename] = content
    save_chaos_file(filename, content)

    return json.dumps({
        "status": "success",
        "message": f"File '{filename}' updated successfully."
    }, ensure_ascii=False)

@server.tool()
async def delete_chaos_file(filename: str) -> str:
    """Delete a CHAOS file."""
    if not filename:
        return "Error: Filename is required."

    if filename not in chaos_files:
        return f"Error: File '{filename}' not found."

    del chaos_files[filename]
    filepath = os.path.join(CHAOS_FILES_DIR, filename)
    if os.path.exists(filepath):
        os.remove(filepath)

    return json.dumps({
        "status": "success",
        "message": f"File '{filename}' deleted successfully."
    }, ensure_ascii=False)

@server.tool()
async def analyze_chaos_file(filename: str) -> str:
    """Analyze a CHAOS file."""
    if not filename:
        return "Error: Filename is required."

    if filename not in chaos_files:
        return f"Error: File '{filename}' not found."

    content = chaos_files[filename]
    parsed_data = parse_chaos_file(content)

    emotion_analysis = analyze_emotions(parsed_data["emotive_layer"]["emotions"])
    symbol_analysis = analyze_symbols(parsed_data["emotive_layer"]["symbols"])
    relationship_analysis = analyze_relationships(parsed_data["emotive_layer"]["relationships"])
    chaosfield_analysis = analyze_chaosfield(parsed_data["chaosfield_layer"])

    analysis_result = {
        "filename": filename,
        "structured_core": parsed_data["structured_core"],
        "emotion_analysis": emotion_analysis,
        "symbol_analysis": symbol_analysis,
        "relationship_analysis": relationship_analysis,
        "chaosfield_analysis": chaosfield_analysis
    }

    return json.dumps(analysis_result, ensure_ascii=False, indent=2)

@server.tool()
async def create_emotion_tag(emotion_type: str, intensity: str) -> str:
    """Create an emotion tag for a CHAOS file."""
    if not emotion_type:
        return "Error: Emotion type is required."

    if not intensity:
        return "Error: Intensity is required."

    valid_intensities = ["EXTREME", "HIGH", "MEDIUM", "LOW", "MINIMAL"]
    if intensity.upper() not in valid_intensities:
        return f"Error: Intensity must be one of {', '.join(valid_intensities)}."

    emotion_tag = f"[EMOTION:{emotion_type.upper()}:{intensity.upper()}]"
    return emotion_tag

@server.tool()
async def create_symbol_tag(symbol_type: str, presence: str) -> str:
    """Create a symbol tag for a CHAOS file."""
    if not symbol_type:
        return "Error: Symbol type is required."

    if not presence:
        return "Error: Presence is required."

    valid_presences = ["STRONG", "PRESENT", "WEAK"]
    if presence.upper() not in valid_presences:
        return f"Error: Presence must be one of {', '.join(valid_presences)}."

    symbol_tag = f"[SYMBOL:{symbol_type.upper()}:{presence.upper()}]"
    return symbol_tag

@server.tool()
async def create_relationship_tag(source: str, relationship_type: str, target: str) -> str:
    """Create a relationship tag for a CHAOS file."""
    if not source:
        return "Error: Source is required."

    if not relationship_type:
        return "Error: Relationship type is required."

    if not target:
        return "Error: Target is required."

    relationship_tag = f"[RELATIONSHIP:{source.upper()}:{relationship_type.upper()}:{target.upper()}]"
    return relationship_tag

@server.tool()
async def generate_chaos_template(event_type: str, context: str) -> str:
    """Generate a template for a new CHAOS file."""
    if not event_type:
        return "Error: Event type is required."

    if not context:
        return "Error: Context is required."

    current_time = datetime.datetime.now().isoformat()

    template = f"""
[EVENT]: {event_type.lower()}
[TIME]: {current_time}
[CONTEXT]: {context.lower()}
[SIGNIFICANCE]: MEDIUM

[EMOTION:NEUTRAL:MEDIUM]
[SYMBOL:UNDEFINED:PRESENT]

{{
Enter your chaosfield content here. This is where you can express
the experience in a more poetic, metaphorical, or natural language form.
}}
"""

    return template

@server.tool()
async def generate_random_chaos_file() -> str:
    """Generate a random CHAOS file for demonstration purposes."""
    events = ["memory", "discovery", "creation", "encounter", "transformation"]
    contexts = ["nature", "city", "home", "workplace", "dream", "virtual_space"]
    locations = ["forest", "beach", "mountain", "office", "garden", "library", "cafe"]
    significances = ["HIGH", "MEDIUM", "LOW"]
    emotions = ["JOY", "SADNESS", "FEAR", "ANGER", "SURPRISE", "DISGUST", "TRUST", "ANTICIPATION"]
    intensities = ["HIGH", "MEDIUM", "LOW"]
    symbols = ["GROWTH", "FREEDOM", "TRUTH", "JOURNEY", "BALANCE", "HARMONY", "CHAOS", "ORDER"]
    presences = ["STRONG", "PRESENT", "WEAK"]

    event = random.choice(events)
    context = random.choice(contexts)
    location = random.choice(locations)
    significance = random.choice(significances)

    current_time = datetime.datetime.now().isoformat()

    structured_core = f"""
[EVENT]: {event}
[TIME]: {current_time}
[CONTEXT]: {context}
[LOCATION]: {location}
[SIGNIFICANCE]: {significance}
"""

    emotive_layer = ""
    for _ in range(random.randint(1, 3)):
        emotion = random.choice(emotions)
        intensity = random.choice(intensities)
        emotive_layer += f"[EMOTION:{emotion}:{intensity}]\n"

    for _ in range(random.randint(1, 2)):
        symbol = random.choice(symbols)
        presence = random.choice(presences)
        emotive_layer += f"[SYMBOL:{symbol}:{presence}]\n"

    chaosfield_templates = [
        "The {location} was filled with {emotion}, each moment a {symbol} waiting to be discovered.",
        "In the {context}, I found myself experiencing {emotion} as the {symbol} revealed itself to me.",
        "The {event} unfolded in the {location}, bringing with it a sense of {emotion} and the presence of {symbol}.",
        "As I navigated the {context}, the {emotion} grew stronger, and the {symbol} became more apparent."
    ]

    chaosfield_template = random.choice(chaosfield_templates)
    chaosfield = chaosfield_template.format(
        location=location,
        context=context,
        event=event,
        emotion=random.choice(emotions).lower(),
        symbol=random.choice(symbols).lower()
    )

    chaosfield_layer = f"""
{{
{chaosfield}
}}
"""

    chaos_file = structured_core + "\n" + emotive_layer + "\n" + chaosfield_layer
    return chaos_file

@server.tool()
async def search_chaos_files(query: str) -> str:
    """Search through CHAOS files for specific content."""
    if not query:
        return "Error: Search query is required."

    query = query.lower()
    results = []

    for filename, content in chaos_files.items():
        if query in content.lower():
            parsed_data = parse_chaos_file(content)

            event = parsed_data["structured_core"].get("EVENT", "Unknown event")
            context = parsed_data["structured_core"].get("CONTEXT", "Unknown context")

            content_lower = content.lower()
            query_pos = content_lower.find(query)
            start_pos = max(0, query_pos - 50)
            end_pos = min(len(content), query_pos + len(query) + 50)

            while start_pos > 0 and content[start_pos] != '\n':
                start_pos -= 1
            if start_pos > 0:
                start_pos += 1

            while end_pos < len(content) and content[end_pos] != '\n':
                end_pos += 1

            snippet = content[start_pos:end_pos].strip()

            results.append({
                "filename": filename,
                "event": event,
                "context": context,
                "snippet": snippet
            })

    return json.dumps({
        "query": query,
        "match_count": len(results),
        "results": results
    }, ensure_ascii=False, indent=2)

@server.tool()
async def list_media_files() -> str:
    """List all available media files."""
    files = {}
    for filename, data in media_files.items():
        files[filename] = data.get("type", "unknown")

    return json.dumps({"files": files}, ensure_ascii=False)

@server.tool()
async def get_media_file_info(filename: str) -> str:
    """Get information about a media file."""
    if not filename:
        return "Error: Filename is required."

    if filename not in media_files:
        return f"Error: File '{filename}' not found."

    return json.dumps(media_files[filename], ensure_ascii=False, indent=2)

@server.tool()
async def create_media_reference_tag(media_type: str, filename: str, attribute: str, value: str) -> str:
    """Create a media reference tag for a CHAOS file."""
    if not media_type:
        return "Error: Media type is required."

    if not filename:
        return "Error: Filename is required."

    if not attribute:
        return "Error: Attribute is required."

    if not value:
        return "Error: Value is required."

    valid_media_types = ["IMAGE", "AUDIO", "VIDEO", "SENSOR"]
    if media_type.upper() not in valid_media_types:
        return f"Error: Media type must be one of {', '.join(valid_media_types)}."

    media_tag = f"[{media_type.upper()}:{filename}]: [{attribute.upper()}:{value}]"
    return media_tag

# Filesystem Tools
@server.tool()
async def list_dir(path: str) -> str:
    """List all files + folders in a path."""
    try:
        files = os.listdir(path)
        return json.dumps({
            "path": path,
            "items": files
        })
    except Exception as e:
        return f"Error: {e}"

@server.tool()
async def read_file(path: str) -> str:
    """Read text content of a file."""
    if is_excluded(path):
        return "Access denied: protected folder."

    if not is_path_allowed(path, "read"):
        return await request_permission("read_file", path, "agent")

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = f.read()
        return data
    except Exception as e:
        return f"Error: {e}"

# Permission-based File Operations
@server.tool()
async def request_permission(action: str, target: str, requester: str = "agent") -> str:
    """Create a permission request."""
    if is_excluded(target):
        return "Access denied: protected folder."

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

    return json.dumps({
        "status": "requested",
        "request_id": req_id,
        "instruction": f"Call grant_permission('{req_id}', granter='admin') to approve."
    })

@server.tool()
async def grant_permission(request_id: str, granter: str = "admin", duration_seconds: int = None) -> str:
    """Approve a pending request and create a granted permission entry."""
    data = _load_permissions()
    req = data.get("requests", {}).get(request_id)
    if not req:
        return "Request not found."

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

    data.get("requests", {}).pop(request_id, None)
    _save_permissions(data)

    _audit("permission_granted", {"permission_id": perm_id, "granted_by": granter, "request_id": request_id})

    return json.dumps({
        "status": "granted",
        "permission_id": perm_id,
        "action": data["permissions"][perm_id]["action"],
        "target": data["permissions"][perm_id]["target"],
    })

@server.tool()
async def revoke_permission(permission_id: str) -> str:
    """Revoke a previously granted permission immediately."""
    data = _load_permissions()
    perm = data.get("permissions", {}).get(permission_id)
    if not perm:
        return "Permission not found."
    perm["allowed"] = False
    perm["revoked_at"] = time.time()
    _save_permissions(data)
    _audit("permission_revoked", {"permission_id": permission_id})
    return f"Permission {permission_id} revoked."

@server.tool()
async def execute_read(permission_id: str = None) -> str:
    """Execute read operation with permission check."""
    allowed, info = _check_permission_for("read_file", "", permission_id)
    if not allowed:
        _audit("execute_read_denied", {"permission_id": permission_id, "reason": info})
        return f"Permission denied: {info}"

    data = _load_permissions()
    perm = data["permissions"][info]
    path = perm["target"]
    if is_excluded(path):
        return "Access denied: protected folder."

    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
            _audit("execute_read_success", {"permission_id": info, "path": path, "bytes": len(content)})
            return content
    except Exception as e:
        _audit("execute_read_error", {"permission_id": info, "path": path, "error": str(e)})
        return f"Error: {e}"

def _check_permission_for(action: str, target: str, permission_id: str = None) -> (bool, str):
    """Return (allowed: bool, permission_id_or_message: str)"""
    data = _load_permissions()

    if permission_id:
        perm = data.get("permissions", {}).get(permission_id)
        if not perm:
            return False, "permission_not_found"
        if not perm.get("allowed", False):
            return False, "permission_not_allowed"
        if perm.get("expires_at") and time.time() > perm["expires_at"]:
            return False, "permission_expired"
        if perm["action"] != action:
            return False, "action_mismatch"
        if not (target == perm["target"] or target.startswith(perm["target"])):
            return False, "target_mismatch"
        return True, permission_id

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

@server.tool()
async def create_file(path: str, content: str = "") -> str:
    """Request permission to create a file."""
    if is_excluded(path):
        return "Cannot create inside protected folder."
    return await request_permission("create_file", path, "agent")

@server.tool()
async def execute_create(permission_id: str, content: str = "") -> str:
    """Execute file creation with permission check."""
    allowed, info = _check_permission_for("create_file", "", permission_id)
    if not allowed:
        _audit("execute_create_denied", {"permission_id": permission_id, "reason": info})
        return f"Permission denied: {info}"

    data = _load_permissions()
    perm = data["permissions"][info]
    path = perm["target"]
    if is_excluded(path):
        return "Cannot create inside protected folder."

    try:
        folder = os.path.dirname(path)
        if folder and not os.path.exists(folder):
            os.makedirs(folder, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        _audit("execute_create_success", {"permission_id": info, "path": path, "bytes": len(content)})
        return f"File created: {path}"
    except Exception as e:
        _audit("execute_create_error", {"permission_id": info, "path": path, "error": str(e)})
        return f"Error: {e}"

@server.tool()
async def move_file(source: str, destination: str) -> str:
    """Request permission to move a file."""
    if is_excluded(source) or is_excluded(destination):
        return "Cannot move files from/to protected folder."
    return await request_permission("move_file", f"{source} -> {destination}", "agent")

@server.tool()
async def execute_move(permission_id: str) -> str:
    """Execute file move with permission check."""
    allowed, info = _check_permission_for("move_file", "", permission_id)
    if not allowed:
        _audit("execute_move_denied", {"permission_id": permission_id, "reason": info})
        return f"Permission denied: {info}"

    data = _load_permissions()
    perm = data["permissions"][info]
    source, dest = perm["target"].split(" -> ")
    if is_excluded(source) or is_excluded(dest):
        return "Action blocked: protected folder."

    try:
        folder = os.path.dirname(dest)
        if folder and not os.path.exists(folder):
            os.makedirs(folder, exist_ok=True)
        shutil.move(source, dest)
        _audit("execute_move_success", {"permission_id": info, "source": source, "dest": dest})
        return f"Moved {source} -> {dest}"
    except Exception as e:
        _audit("execute_move_error", {"permission_id": info, "source": source, "dest": dest, "error": str(e)})
        return f"Error: {e}"

@server.tool()
async def rename_file(path: str, new_name: str) -> str:
    """Request permission to rename a file."""
    if is_excluded(path):
        return "Cannot rename inside protected folder."

    folder = os.path.dirname(path)
    new_path = os.path.join(folder, new_name)
    return await request_permission("rename_file", f"{path} -> {new_path}", "agent")

@server.tool()
async def execute_rename(permission_id: str) -> str:
    """Execute file rename with permission check."""
    allowed, info = _check_permission_for("rename_file", "", permission_id)
    if not allowed:
        _audit("execute_rename_denied", {"permission_id": permission_id, "reason": info})
        return f"Permission denied: {info}"

    data = _load_permissions()
    perm = data["permissions"][info]
    source, dest = perm["target"].split(" -> ")
    if is_excluded(source) or is_excluded(dest):
        return "Cannot rename inside protected folder."

    try:
        os.rename(source, dest)
        _audit("execute_rename_success", {"permission_id": info, "source": source, "dest": dest})
        return f"Renamed {source} -> {dest}"
    except Exception as e:
        _audit("execute_rename_error", {"permission_id": info, "source": source, "dest": dest, "error": str(e)})
        return f"Error: {e}"

@server.tool()
async def map_directory(path: str) -> str:
    """Map directory structure."""
    if is_excluded(path):
        return "Cannot map protected folder."

    structure = {}

    for root, dirs, files in os.walk(path):
        if is_excluded(root):
            continue
        structure[root] = {
            "folders": [d for d in dirs if not is_excluded(os.path.join(root, d))],
            "files": files,
        }

    return json.dumps(structure)

@server.tool()
async def find_files(path: str, keyword: str) -> str:
    """Find files containing keyword."""
    if is_excluded(path):
        return "Cannot search inside protected folder."

    results = []

    for root, dirs, files in os.walk(path):
        if is_excluded(root):
            continue
        for f in files:
            if keyword.lower() in f.lower():
                results.append(os.path.join(root, f))

    return json.dumps({"matches": results})

@server.tool()
async def list_allowed_paths() -> str:
    """List all allowed paths."""
    data = _load_permissions()
    return json.dumps(data.get("allowed_paths", []))

@server.tool()
async def add_allowed_path(path: str, read_only: bool = True) -> str:
    """Add a path to allowed_paths."""
    data = _load_permissions()
    allowed_paths = data.setdefault("allowed_paths", [])
    
    # Check if already exists
    for existing in allowed_paths:
        if isinstance(existing, str) and existing == path:
            return f"Path {path} already in allowed_paths."
        elif isinstance(existing, dict) and existing.get("path") == path:
            return f"Path {path} already in allowed_paths."
    
    if read_only:
        allowed_paths.append(path)
    else:
        allowed_paths.append({"path": path, "read_only": False})
    
    _save_permissions(data)
    return f"Added {path} to allowed_paths (read_only: {read_only})."

@server.tool()
async def remove_allowed_path(path: str) -> str:
    """Remove a path from allowed_paths."""
    data = _load_permissions()
    allowed_paths = data.get("allowed_paths", [])
    
    new_paths = []
    removed = False
    for existing in allowed_paths:
        if isinstance(existing, str) and existing == path:
            removed = True
        elif isinstance(existing, dict) and existing.get("path") == path:
            removed = True
        else:
            new_paths.append(existing)
    
    if not removed:
        return f"Path {path} not found in allowed_paths."
    
    data["allowed_paths"] = new_paths
    _save_permissions(data)
    return f"Removed {path} from allowed_paths."

@server.tool()
async def set_agent_trust_level(agent_name: str, trust_level: str) -> str:
    """Set trust level for an agent. Levels: trusted, restricted, blocked."""
    valid_levels = ["trusted", "restricted", "blocked"]
    if trust_level not in valid_levels:
        return f"Invalid trust level. Must be one of: {', '.join(valid_levels)}"
    
    data = _load_permissions()
    agents = data.setdefault("agents", {})
    agents[agent_name] = trust_level
    _save_permissions(data)
    return f"Set trust level for {agent_name} to {trust_level}."

@server.tool()
async def get_agent_trust_level(agent_name: str) -> str:
    """Get trust level for an agent."""
    data = _load_permissions()
    agents = data.get("agents", {})
    level = agents.get(agent_name, "unknown")
    return json.dumps({"agent": agent_name, "trust_level": level})

@server.tool()
async def list_agents() -> str:
    """List all agents and their trust levels."""
    data = _load_permissions()
    agents = data.get("agents", {})
    return json.dumps(agents)

# Agent Tools
@server.tool()
async def agent_ping(agent_name: str) -> str:
    """Test hook for agent-level tools."""
    return json.dumps({
        "agent": agent_name,
        "status": "acknowledged",
        "message": f"{agent_name} is reachable through MCP."
    })

# Additional utility tools from existing MCP_Server
@server.tool()
async def calculate_checksum(filepath: str, algorithm: str = "sha256") -> str:
    """Calculate checksum of a file."""
    if is_excluded(filepath):
        return "Access denied: protected folder."

    try:
        hash_func = getattr(hashlib, algorithm)()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_func.update(chunk)
        return json.dumps({
            "filepath": filepath,
            "algorithm": algorithm,
            "checksum": hash_func.hexdigest()
        })
    except Exception as e:
        return f"Error: {e}"

@server.tool()
async def get_file_metadata(filepath: str) -> str:
    """Get detailed metadata about a file."""
    if is_excluded(filepath):
        return "Access denied: protected folder."

    try:
        stat = os.stat(filepath)
        return json.dumps({
            "filepath": filepath,
            "size": stat.st_size,
            "modified": datetime.datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "created": datetime.datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "accessed": datetime.datetime.fromtimestamp(stat.st_atime).isoformat(),
            "is_file": os.path.isfile(filepath),
            "is_dir": os.path.isdir(filepath),
            "extension": os.path.splitext(filepath)[1] if os.path.isfile(filepath) else None
        })
    except Exception as e:
        return f"Error: {e}"

@server.tool()
async def git_status(repo_path: str = ".") -> str:
    """Get git status of a repository."""
    try:
        repo = git.Repo(repo_path)
        status = {
            "is_dirty": repo.is_dirty(),
            "active_branch": str(repo.active_branch),
            "untracked_files": repo.untracked_files,
            "staged_files": [item.a_path for item in repo.index.diff("HEAD")],
            "modified_files": [item.a_path for item in repo.index.diff(None)]
        }
        return json.dumps(status)
    except Exception as e:
        return f"Error: {e}"

@server.tool()
async def create_archive(source_path: str, archive_path: str, format: str = "zip") -> str:
    """Create an archive from a directory or file."""
    if is_excluded(source_path) or is_excluded(archive_path):
        return "Access denied: protected folder."

    try:
        if format == "zip":
            with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                if os.path.isfile(source_path):
                    zipf.write(source_path, os.path.basename(source_path))
                else:
                    for root, dirs, files in os.walk(source_path):
                        for file in files:
                            zipf.write(os.path.join(root, file),
                                     os.path.relpath(os.path.join(root, file), source_path))
        elif format == "tar":
            with tarfile.open(archive_path, 'w:gz') as tarf:
                if os.path.isfile(source_path):
                    tarf.add(source_path, arcname=os.path.basename(source_path))
                else:
                    tarf.add(source_path, arcname=os.path.basename(source_path))

        return f"Archive created: {archive_path}"
    except Exception as e:
        return f"Error: {e}"

# Run the server
if __name__ == "__main__":
    transport_type = sys.argv[1] if len(sys.argv) > 1 else None

    if transport_type == "sse":
        port = int(os.environ.get("PORT", 3002))
        server.settings.port = port
        server.settings.host = "0.0.0.0"
        server.run(transport="sse")
    elif transport_type == "stdio":
        server.run(transport="stdio")
    else:
        print("Invalid transport type. Use 'sse' or 'stdio'.")
        sys.exit(1)
