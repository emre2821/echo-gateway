#!/usr/bin/env python3
"""
EdenOS MCP Server Hub - CHAOS Handler (Tool Adapter)
Thin adapter layer that calls the chaos engine.
No business logic here - just tool interface.
"""

from chaos import chaos_engine

# Export functions that tools can call - these delegate to the engine
def create_chaos_file(filename: str, content: str, metadata: dict = None) -> bool:
    """Create a new CHAOS file."""
    return chaos_engine.create_file(filename, content, metadata)

def read_chaos_file(filename: str):
    """Read and parse a CHAOS file."""
    return chaos_engine.read_file(filename)

def update_chaos_file(filename: str, content: str, metadata: dict = None) -> bool:
    """Update an existing CHAOS file."""
    return chaos_engine.update_file(filename, content, metadata)

def delete_chaos_file(filename: str) -> bool:
    """Delete a CHAOS file."""
    return chaos_engine.delete_file(filename)

def analyze_chaos_file(filename: str):
    """Analyze a CHAOS file."""
    return chaos_engine.analyze_file(filename)

def list_chaos_files():
    """List all CHAOS files with registry info."""
    return chaos_engine.list_files()

def get_chaos_file_info(filename: str):
    """Get registry info for a specific file."""
    return chaos_engine.get_file_info(filename)

def create_emotion_tag(emotion_type: str, intensity: str):
    """Create an emotion tag."""
    return chaos_engine.create_emotion_tag(emotion_type, intensity)

def create_symbol_tag(symbol_type: str, presence: str):
    """Create a symbol tag."""
    return chaos_engine.create_symbol_tag(symbol_type, presence)

def create_relationship_tag(source: str, relationship_type: str, target: str):
    """Create a relationship tag."""
    return chaos_engine.create_relationship_tag(source, relationship_type, target)

def search_chaos_files(query: str, search_type: str = "content"):
    """Search CHAOS files."""
    return chaos_engine.search_files(query, search_type)
