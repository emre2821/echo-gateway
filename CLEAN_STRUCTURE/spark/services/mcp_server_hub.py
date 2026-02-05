#!/usr/bin/env python3
"""
EdenOS MCP Server Hub - Router Only
Pure router that registers tools and delegates to engines.
No state, no direct file operations, no business logic.
"""

import json
from hub_core import server, register, event_bus, emit
from permissions_engine import permissions_engine
from context_engine import context_engine
from chaos_handler import (
    create_chaos_file, read_chaos_file, update_chaos_file, delete_chaos_file,
    analyze_chaos_file, list_chaos_files,
    create_emotion_tag, create_symbol_tag, create_relationship_tag
)
from permission_manager import (
    is_path_allowed, add_allowed_path, remove_allowed_path,
    list_allowed_paths, audit_event
)
from filesystem_engine import filesystem_engine
from media_engine import media_engine
from agent_trust_engine import agent_trust_engine
from utility_engine import utility_engine
from chaos.engine import ChaosEngine
from backbone_adapter import backbone_adapter
from local_event_gateway import local_event_gateway

# Initialize CHAOS engine
chaos_engine = ChaosEngine()

# Register engines with hub
register("permissions", permissions_engine)
register("context", context_engine)
register("filesystem", filesystem_engine)
register("media", media_engine)
register("agent_trust", agent_trust_engine)
register("utility", utility_engine)
register("chaos", chaos_engine)
register("backbone", backbone_adapter)
register("local_event_gateway", local_event_gateway)

# Create hub object for engines
class Hub:
    def __init__(self, event_bus, emit):
        self.event_bus = event_bus
        self.emit = emit

hub = Hub(event_bus, emit)

# Auto-wire all engines at boot
for engine in [
    permissions_engine, context_engine, filesystem_engine,
    media_engine, agent_trust_engine, utility_engine, chaos_engine,
    backbone_adapter, local_event_gateway
]:
    engine.on_boot(hub)

# ==================== CHAOS FILE TOOLS ====================

@server.tool()
async def create_chaos_file_tool(filename: str, content: str, metadata: str = None) -> str:
    """Create a new CHAOS file."""
    try:
        metadata_dict = json.loads(metadata) if metadata else None
        success = create_chaos_file(filename, content, metadata_dict)
        
        if success:
            audit_event("chaos_file_created", {"filename": filename})
            return json.dumps({"status": "success", "message": f"File '{filename}' created successfully."})
        else:
            return json.dumps({"status": "error", "message": f"Failed to create file '{filename}'."})
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

@server.tool()
async def read_chaos_file_tool(filename: str) -> str:
    """Read a CHAOS file."""
    try:
        result = read_chaos_file(filename)
        if result:
            audit_event("chaos_file_read", {"filename": filename})
            return json.dumps(result, ensure_ascii=False, indent=2)
        else:
            return json.dumps({"status": "error", "message": f"File '{filename}' not found."})
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

@server.tool()
async def update_chaos_file_tool(filename: str, content: str, metadata: str = None) -> str:
    """Update an existing CHAOS file."""
    try:
        metadata_dict = json.loads(metadata) if metadata else None
        success = update_chaos_file(filename, content, metadata_dict)
        
        if success:
            audit_event("chaos_file_updated", {"filename": filename})
            return json.dumps({"status": "success", "message": f"File '{filename}' updated successfully."})
        else:
            return json.dumps({"status": "error", "message": f"Failed to update file '{filename}'."})
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

@server.tool()
async def delete_chaos_file_tool(filename: str) -> str:
    """Delete a CHAOS file."""
    try:
        success = delete_chaos_file(filename)
        
        if success:
            audit_event("chaos_file_deleted", {"filename": filename})
            return json.dumps({"status": "success", "message": f"File '{filename}' deleted successfully."})
        else:
            return json.dumps({"status": "error", "message": f"Failed to delete file '{filename}'."})
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

@server.tool()
async def analyze_chaos_file_tool(filename: str) -> str:
    """Analyze a CHAOS file."""
    try:
        result = analyze_chaos_file(filename)
        if result:
            audit_event("chaos_file_analyzed", {"filename": filename})
            return json.dumps(result, ensure_ascii=False, indent=2)
        else:
            return json.dumps({"status": "error", "message": f"Failed to analyze file '{filename}'."})
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

@server.tool()
async def list_chaos_files_tool() -> str:
    """List all CHAOS files."""
    try:
        result = list_chaos_files()
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

@server.tool()
async def create_emotion_tag_tool(emotion_type: str, intensity: str) -> str:
    """Create an emotion tag for a CHAOS file."""
    try:
        result = create_emotion_tag(emotion_type, intensity)
        if result:
            return result
        else:
            return json.dumps({"status": "error", "message": "Invalid emotion type or intensity."})
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

@server.tool()
async def create_symbol_tag_tool(symbol_type: str, presence: str) -> str:
    """Create a symbol tag for a CHAOS file."""
    try:
        result = create_symbol_tag(symbol_type, presence)
        if result:
            return result
        else:
            return json.dumps({"status": "error", "message": "Invalid symbol type or presence."})
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

@server.tool()
async def create_relationship_tag_tool(source: str, relationship_type: str, target: str) -> str:
    """Create a relationship tag for a CHAOS file."""
    try:
        result = create_relationship_tag(source, relationship_type, target)
        if result:
            return result
        else:
            return json.dumps({"status": "error", "message": "Invalid relationship parameters."})
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

# ==================== PERMISSION TOOLS ====================

@server.tool()
async def add_allowed_path_tool(path: str) -> str:
    """Add a path to the allowed paths list."""
    try:
        success = add_allowed_path(path)
        if success:
            return json.dumps({"status": "success", "message": f"Path '{path}' added to allowed paths."})
        else:
            return json.dumps({"status": "error", "message": f"Failed to add path '{path}' to allowed paths."})
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

@server.tool()
async def remove_allowed_path_tool(path: str) -> str:
    """Remove a path from the allowed paths list."""
    try:
        success = remove_allowed_path(path)
        if success:
            return json.dumps({"status": "success", "message": f"Path '{path}' removed from allowed paths."})
        else:
            return json.dumps({"status": "error", "message": f"Failed to remove path '{path}' from allowed paths."})
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

@server.tool()
async def list_allowed_paths_tool() -> str:
    """List all allowed paths."""
    try:
        paths = list_allowed_paths()
        return json.dumps({"allowed_paths": paths, "count": len(paths)}, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

@server.tool()
async def check_path_allowed_tool(path: str, operation: str = "read") -> str:
    """Check if a path is allowed for operations."""
    try:
        allowed = is_path_allowed(path, operation)
        return json.dumps({"path": path, "operation": operation, "allowed": allowed}, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

# ==================== FILESYSTEM TOOLS ====================

@server.tool()
async def read_file_tool(path: str) -> str:
    """Read file contents."""
    try:
        content = filesystem_engine.read_file(path)
        if content is not None:
            audit_event("file_read", {"path": path})
            return json.dumps({"content": content}, ensure_ascii=False)
        else:
            return json.dumps({"status": "error", "message": f"Failed to read file '{path}'."})
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

@server.tool()
async def write_file_tool(path: str, content: str, encoding: str = "utf-8") -> str:
    """Write file contents."""
    try:
        success = filesystem_engine.write_file(path, content, encoding)
        if success:
            audit_event("file_written", {"path": path})
            return json.dumps({"status": "success", "message": f"File '{path}' written successfully."})
        else:
            return json.dumps({"status": "error", "message": f"Failed to write file '{path}'."})
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

@server.tool()
async def delete_file_tool(path: str) -> str:
    """Delete a file."""
    try:
        success = filesystem_engine.delete_file(path)
        if success:
            audit_event("file_deleted", {"path": path})
            return json.dumps({"status": "success", "message": f"File '{path}' deleted successfully."})
        else:
            return json.dumps({"status": "error", "message": f"Failed to delete file '{path}'."})
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

@server.tool()
async def list_directory_tool(path: str) -> str:
    """List directory contents."""
    try:
        contents = filesystem_engine.list_directory(path)
        return json.dumps({"path": path, "contents": contents}, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

# ==================== MEDIA TOOLS ====================

@server.tool()
async def register_media_tool(file_path: str, tags: str = None, description: str = None) -> str:
    """Register a media file."""
    try:
        tags_list = json.loads(tags) if tags else []
        success = media_engine.register_media(file_path, tags_list, description)
        if success:
            audit_event("media_registered", {"file_path": file_path})
            return json.dumps({"status": "success", "message": f"Media '{file_path}' registered successfully."})
        else:
            return json.dumps({"status": "error", "message": f"Failed to register media '{file_path}'."})
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

@server.tool()
async def get_media_info_tool(media_id: str) -> str:
    """Get media information."""
    try:
        info = media_engine.get_media_info(media_id)
        if info:
            return json.dumps(info, ensure_ascii=False, indent=2)
        else:
            return json.dumps({"status": "error", "message": f"Media '{media_id}' not found."})
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

@server.tool()
async def list_media_tool() -> str:
    """List all registered media."""
    try:
        media_list = media_engine.list_media()
        return json.dumps(media_list, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

# ==================== AGENT TRUST TOOLS ====================

@server.tool()
async def register_agent_tool(agent_info: str, initial_trust: str = "unknown") -> str:
    """Register a new agent."""
    try:
        agent_dict = json.loads(agent_info)
        from agent_trust_engine import TrustLevel
        trust_level = TrustLevel(initial_trust.upper())
        
        agent_id = agent_trust_engine.register_agent(agent_dict, trust_level)
        audit_event("agent_registered", {"agent_id": agent_id})
        return json.dumps({"status": "success", "agent_id": agent_id})
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

@server.tool()
async def set_agent_trust_tool(agent_id: str, trust_level: str, reason: str = None) -> str:
    """Set trust level for an agent."""
    try:
        from agent_trust_engine import TrustLevel
        level = TrustLevel(trust_level.upper())
        
        success = agent_trust_engine.set_trust_level(agent_id, level, reason)
        if success:
            audit_event("agent_trust_changed", {"agent_id": agent_id, "level": trust_level})
            return json.dumps({"status": "success", "message": f"Trust level set for agent '{agent_id}'."})
        else:
            return json.dumps({"status": "error", "message": f"Failed to set trust level for agent '{agent_id}'."})
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

@server.tool()
async def get_agent_trust_tool(agent_id: str) -> str:
    """Get trust level for an agent."""
    try:
        level = agent_trust_engine.get_trust_level(agent_id)
        if level:
            return json.dumps({"agent_id": agent_id, "trust_level": level.value})
        else:
            return json.dumps({"status": "error", "message": f"Agent '{agent_id}' not found."})
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

# ==================== UTILITY TOOLS ====================

@server.tool()
async def calculate_checksum_tool(file_path: str, algorithm: str = "sha256") -> str:
    """Calculate file checksum."""
    try:
        checksum = utility_engine.calculate_checksum(file_path, algorithm)
        if checksum:
            return json.dumps({"file_path": file_path, "algorithm": algorithm, "checksum": checksum})
        else:
            return json.dumps({"status": "error", "message": f"Failed to calculate checksum for '{file_path}'."})
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

@server.tool()
async def create_archive_tool(source_path: str, archive_path: str, format: str = "zip") -> str:
    """Create archive from directory."""
    try:
        success = utility_engine.create_archive(source_path, archive_path, format)
        if success:
            audit_event("archive_created", {"source": source_path, "archive": archive_path})
            return json.dumps({"status": "success", "message": f"Archive '{archive_path}' created successfully."})
        else:
            return json.dumps({"status": "error", "message": f"Failed to create archive '{archive_path}'."})
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

@server.tool()
async def git_status_tool(path: str = ".") -> str:
    """Get git repository status."""
    try:
        status = utility_engine.get_git_status(path)
        return json.dumps(status, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

# ==================== CONTEXT TOOLS ====================

@server.tool()
async def add_context_text_tool(text: str, source: str = "user") -> str:
    """Add text to context window."""
    try:
        success = context_engine.add_text(text, source)
        if success:
            return json.dumps({"status": "success", "message": "Text added to context."})
        else:
            return json.dumps({"status": "error", "message": "Failed to add text to context."})
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

@server.tool()
async def get_context_window_tool(limit: int = 50) -> str:
    """Get context window entries."""
    try:
        entries = context_engine.get_window(limit)
        return json.dumps({"entries": entries, "count": len(entries)}, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

@server.tool()
async def search_context_tool(query: str, limit: int = 10) -> str:
    """Search context window."""
    try:
        results = context_engine.search(query, limit)
        return json.dumps({"query": query, "results": results, "count": len(results)}, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

@server.tool()
async def clear_context_tool() -> str:
    """Clear context window."""
    try:
        context_engine.clear_window()
        audit_event("context_cleared", {})
        return json.dumps({"status": "success", "message": "Context window cleared."})
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

@server.tool()
async def start_event_gateway_tool() -> str:
    """Start the Local Event Gateway when server is running."""
    try:
        local_event_gateway.start_when_ready()
        return json.dumps({"status": "success", "message": "Local Event Gateway started"})
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

def main():
    """Main entry point for the MCP server hub."""
    import asyncio
    
    # Emit system started event
    emit("system.started", {
        "server": "eden-mcp-server-hub",
        "engines": ["permissions", "context", "filesystem", "media", "agent_trust", "utility", "chaos", "backbone", "local_event_gateway"],
        "event_nervous_system": "activated",
        "external_gateway": "ws://127.0.0.1:8765"
    })
    
    audit_event("server_started", {"server": "eden-mcp-server-hub"})
    
    print("EdenOS MCP Server Hub starting...")
    print("Modular architecture with sovereign cognitive systems")
    print("Event-driven nervous system activated")
    print("Press Ctrl+C to stop")
    
    try:
        asyncio.run(server.run())
    except KeyboardInterrupt:
        print("\nShutting down EdenOS MCP Server Hub...")
        emit("system.stopped", {"server": "eden-mcp-server-hub"})
        audit_event("server_stopped", {"server": "eden-mcp-server-hub"})

if __name__ == "__main__":
    main()
