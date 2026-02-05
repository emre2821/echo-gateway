#!/usr/bin/env python3
"""
EdenOS MCP Server Hub - Filesystem Engine
Handles all file operations with validation and security.
"""

import os
import shutil
import glob
from typing import Dict, Any, List, Optional, Union
from permissions_engine import permissions_engine

class FilesystemEngine:
    """Handles all file operations with validation and security."""
    
    def __init__(self):
        self.permissions = permissions_engine
        self.hub = None  # Nerve hook
    
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
            print(f"[FilesystemEngine] Permission denied: {payload}")
        elif event_type == "system.warning":
            print(f"[FilesystemEngine] System warning: {payload}")
        elif event_type == "chaos.file.created":
            print(f"[FilesystemEngine] CHAOS file created: {payload.get('filename')}")
    
    def validate_path(self, path: str, operation: str = "read") -> bool:
        """Validate path for operations."""
        if not path:
            return False
        
        # Check permissions
        if not self.permissions.is_path_allowed(path, operation):
            return False
        
        # Check if path exists for read operations
        if operation in ["read", "list", "info"]:
            if not os.path.exists(path):
                return False
        
        return True
    
    def read_file(self, path: str, encoding: str = "utf-8") -> Optional[str]:
        """Read file contents."""
        if not self.validate_path(path, "read"):
            return None
        
        try:
            with open(path, "r", encoding=encoding) as f:
                return f.read()
        except Exception as e:
            print(f"[FilesystemEngine] Failed to read {path}: {e}")
            return None
    
    def read_file_bytes(self, path: str) -> Optional[bytes]:
        """Read file as bytes."""
        if not self.validate_path(path, "read"):
            return None
        
        try:
            with open(path, "rb") as f:
                return f.read()
        except Exception as e:
            print(f"[FilesystemEngine] Failed to read bytes {path}: {e}")
            return None
    
    def write_file(self, path: str, content: Union[str, bytes], encoding: str = "utf-8") -> bool:
        """Write file contents."""
        if not self.validate_path(path, "write"):
            return False
        
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(path), exist_ok=True)
            
            if isinstance(content, bytes):
                with open(path, "wb") as f:
                    f.write(content)
            else:
                with open(path, "w", encoding=encoding) as f:
                    f.write(content)
            
            # Emit filesystem written event
            if self.hub:
                self.hub.emit("filesystem.written", {
                    "path": path,
                    "size": len(content) if isinstance(content, (str, bytes)) else 0,
                    "encoding": encoding if not isinstance(content, bytes) else "binary"
                })
            
            return True
            
        except Exception as e:
            print(f"[FilesystemEngine] Failed to write {path}: {e}")
            return False
    
    def append_file(self, path: str, content: str, encoding: str = "utf-8") -> bool:
        """Append content to file."""
        if not self.validate_path(path, "write"):
            return False
        
        try:
            with open(path, "a", encoding=encoding) as f:
                f.write(content)
            return True
            
        except Exception as e:
            print(f"[FilesystemEngine] Failed to append to {path}: {e}")
            return False
    
    def delete_file(self, path: str) -> bool:
        """Delete a file."""
        if not self.validate_path(path, "delete"):
            return False
        
        try:
            if os.path.exists(path):
                os.remove(path)
                
                # Emit filesystem deleted event
                if self.hub:
                    self.hub.emit("filesystem.deleted", {
                        "path": path
                    })
            
            return True
            
        except Exception as e:
            print(f"[FilesystemEngine] Failed to delete {path}: {e}")
            return False
    
    def move_file(self, source: str, destination: str) -> bool:
        """Move a file."""
        if not self.validate_path(source, "read") or not self.validate_path(destination, "write"):
            return False
        
        try:
            # Create destination directory if it doesn't exist
            os.makedirs(os.path.dirname(destination), exist_ok=True)
            shutil.move(source, destination)
            return True
            
        except Exception as e:
            print(f"[FilesystemEngine] Failed to move {source} to {destination}: {e}")
            return False
    
    def copy_file(self, source: str, destination: str) -> bool:
        """Copy a file."""
        if not self.validate_path(source, "read") or not self.validate_path(destination, "write"):
            return False
        
        try:
            # Create destination directory if it doesn't exist
            os.makedirs(os.path.dirname(destination), exist_ok=True)
            shutil.copy2(source, destination)
            return True
            
        except Exception as e:
            print(f"[FilesystemEngine] Failed to copy {source} to {destination}: {e}")
            return False
    
    def rename_file(self, path: str, new_name: str) -> bool:
        """Rename a file."""
        if not self.validate_path(path, "write"):
            return False
        
        try:
            new_path = os.path.join(os.path.dirname(path), new_name)
            if not self.validate_path(new_path, "write"):
                return False
            
            os.rename(path, new_path)
            return True
            
        except Exception as e:
            print(f"[FilesystemEngine] Failed to rename {path} to {new_name}: {e}")
            return False
    
    def list_directory(self, path: str, recursive: bool = False, pattern: str = "*") -> List[Dict[str, Any]]:
        """List directory contents."""
        if not self.validate_path(path, "list"):
            return []
        
        try:
            files = []
            
            if recursive:
                # Recursive search
                search_pattern = os.path.join(path, "**", pattern)
                for file_path in glob.glob(search_pattern, recursive=True):
                    if os.path.isfile(file_path):
                        files.append(self._get_file_info(file_path))
            else:
                # Non-recursive search
                search_pattern = os.path.join(path, pattern)
                for file_path in glob.glob(search_pattern):
                    if os.path.isfile(file_path):
                        files.append(self._get_file_info(file_path))
            
            return files
            
        except Exception as e:
            print(f"[FilesystemEngine] Failed to list directory {path}: {e}")
            return []
    
    def find_files(self, search_dir: str, name_pattern: str = "*", content_pattern: str = None, max_results: int = 100) -> List[Dict[str, Any]]:
        """Find files by name and/or content pattern."""
        if not self.validate_path(search_dir, "list"):
            return []
        
        try:
            results = []
            
            # Search by name pattern
            search_pattern = os.path.join(search_dir, "**", name_pattern)
            for file_path in glob.glob(search_pattern, recursive=True):
                if os.path.isfile(file_path):
                    file_info = self._get_file_info(file_path)
                    
                    # Search content if pattern provided
                    if content_pattern:
                        content = self.read_file(file_path)
                        if content and content_pattern.lower() in content.lower():
                            file_info["content_matches"] = content.lower().count(content_pattern.lower())
                            results.append(file_info)
                    else:
                        results.append(file_info)
                    
                    # Limit results
                    if len(results) >= max_results:
                        break
            
            return results
            
        except Exception as e:
            print(f"[FilesystemEngine] Failed to find files in {search_dir}: {e}")
            return []
    
    def map_directory(self, path: str, max_depth: int = 5) -> Dict[str, Any]:
        """Map directory structure."""
        if not self.validate_path(path, "list"):
            return {}
        
        try:
            def _map_recursive(current_path: str, current_depth: int) -> Dict[str, Any]:
                if current_depth > max_depth:
                    return {"error": "Max depth exceeded"}
                
                result = {
                    "path": current_path,
                    "type": "directory" if os.path.isdir(current_path) else "file",
                    "children": []
                }
                
                if os.path.isdir(current_path):
                    try:
                        for item in os.listdir(current_path):
                            item_path = os.path.join(current_path, item)
                            if self.validate_path(item_path, "list"):
                                child_result = _map_recursive(item_path, current_depth + 1)
                                result["children"].append(child_result)
                    except PermissionError:
                        result["error"] = "Permission denied"
                
                return result
            
            return _map_recursive(path, 0)
            
        except Exception as e:
            print(f"[FilesystemEngine] Failed to map directory {path}: {e}")
            return {"error": str(e)}
    
    def get_file_info(self, path: str) -> Optional[Dict[str, Any]]:
        """Get detailed file information."""
        if not self.validate_path(path, "info"):
            return None
        
        return self._get_file_info(path)
    
    def _get_file_info(self, path: str) -> Dict[str, Any]:
        """Internal method to get file info without validation."""
        try:
            stat = os.stat(path)
            
            return {
                "path": path,
                "name": os.path.basename(path),
                "size": stat.st_size,
                "created": stat.st_ctime,
                "modified": stat.st_mtime,
                "accessed": stat.st_atime,
                "is_file": os.path.isfile(path),
                "is_directory": os.path.isdir(path),
                "extension": os.path.splitext(path)[1],
                "parent": os.path.dirname(path)
            }
            
        except Exception as e:
            return {"path": path, "error": str(e)}
    
    def create_directory(self, path: str) -> bool:
        """Create a directory."""
        if not self.validate_path(path, "write"):
            return False
        
        try:
            os.makedirs(path, exist_ok=True)
            return True
            
        except Exception as e:
            print(f"[FilesystemEngine] Failed to create directory {path}: {e}")
            return False
    
    def delete_directory(self, path: str, recursive: bool = False) -> bool:
        """Delete a directory."""
        if not self.validate_path(path, "delete"):
            return False
        
        try:
            if recursive:
                shutil.rmtree(path)
            else:
                os.rmdir(path)
            return True
            
        except Exception as e:
            print(f"[FilesystemEngine] Failed to delete directory {path}: {e}")
            return False
    
    def get_disk_usage(self, path: str) -> Dict[str, Any]:
        """Get disk usage information."""
        if not self.validate_path(path, "info"):
            return {}
        
        try:
            usage = shutil.disk_usage(path)
            return {
                "path": path,
                "total": usage.total,
                "used": usage.used,
                "free": usage.free,
                "usage_percent": (usage.used / usage.total) * 100
            }
            
        except Exception as e:
            print(f"[FilesystemEngine] Failed to get disk usage for {path}: {e}")
            return {"error": str(e)}
    
    def search_in_file(self, path: str, pattern: str, case_sensitive: bool = False) -> List[Dict[str, Any]]:
        """Search for pattern within a file."""
        if not self.validate_path(path, "read"):
            return []
        
        try:
            content = self.read_file(path)
            if not content:
                return []
            
            matches = []
            lines = content.split('\n')
            
            search_pattern = pattern if case_sensitive else pattern.lower()
            
            for line_num, line in enumerate(lines, 1):
                search_line = line if case_sensitive else line.lower()
                
                if search_pattern in search_line:
                    matches.append({
                        "line_number": line_num,
                        "line_content": line,
                        "match_count": line.lower().count(pattern.lower()) if not case_sensitive else line.count(pattern)
                    })
            
            return matches
            
        except Exception as e:
            print(f"[FilesystemEngine] Failed to search in {path}: {e}")
            return []

# Global filesystem engine instance
filesystem_engine = FilesystemEngine()
