#!/usr/bin/env python3
"""
EdenOS MCP Server Hub - CHAOS Storage
Handles file I/O operations for CHAOS files.
"""

import os
from typing import Dict, Any, List, Optional

class ChaosStorage:
    """Handles file I/O operations for CHAOS files."""
    
    def __init__(self, chaos_dir: str = "chaos_files"):
        self.chaos_dir = chaos_dir
        os.makedirs(chaos_dir, exist_ok=True)
    
    def save(self, filename: str, content: str) -> bool:
        """Save CHAOS file to disk."""
        if not filename or not content:
            return False
        
        try:
            filepath = os.path.join(self.chaos_dir, filename)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"[ChaosStorage] Failed to save {filename}: {e}")
            return False
    
    def load(self, filename: str) -> Optional[str]:
        """Load CHAOS file from disk."""
        if not filename:
            return None
        
        try:
            filepath = os.path.join(self.chaos_dir, filename)
            if os.path.exists(filepath):
                with open(filepath, "r", encoding="utf-8") as f:
                    return f.read()
            return None
        except Exception as e:
            print(f"[ChaosStorage] Failed to load {filename}: {e}")
            return None
    
    def delete(self, filename: str) -> bool:
        """Delete CHAOS file from disk."""
        if not filename:
            return False
        
        try:
            filepath = os.path.join(self.chaos_dir, filename)
            if os.path.exists(filepath):
                os.remove(filepath)
            return True
        except Exception as e:
            print(f"[ChaosStorage] Failed to delete {filename}: {e}")
            return False
    
    def exists(self, filename: str) -> bool:
        """Check if CHAOS file exists."""
        if not filename:
            return False
        
        filepath = os.path.join(self.chaos_dir, filename)
        return os.path.exists(filepath)
    
    def list_files(self) -> List[str]:
        """List all CHAOS files."""
        try:
            files = []
            for filename in os.listdir(self.chaos_dir):
                filepath = os.path.join(self.chaos_dir, filename)
                if os.path.isfile(filepath) and not filename.startswith('.'):
                    files.append(filename)
            return sorted(files)
        except Exception as e:
            print(f"[ChaosStorage] Failed to list files: {e}")
            return []
    
    def get_file_info(self, filename: str) -> Optional[Dict[str, Any]]:
        """Get file metadata."""
        if not filename:
            return None
        
        try:
            filepath = os.path.join(self.chaos_dir, filename)
            if not os.path.exists(filepath):
                return None
            
            stat = os.stat(filepath)
            return {
                "filename": filename,
                "size": stat.st_size,
                "created": stat.st_ctime,
                "modified": stat.st_mtime,
                "exists": True
            }
        except Exception as e:
            print(f"[ChaosStorage] Failed to get file info for {filename}: {e}")
            return None
    
    def backup_file(self, filename: str, backup_suffix: str = None) -> bool:
        """Create a backup of a CHAOS file."""
        if not filename:
            return False
        
        content = self.load(filename)
        if not content:
            return False
        
        import time
        if backup_suffix is None:
            backup_suffix = str(int(time.time()))
        
        backup_filename = f"{filename}.backup.{backup_suffix}"
        return self.save(backup_filename, content)
    
    def restore_file(self, filename: str, backup_suffix: str) -> bool:
        """Restore a CHAOS file from backup."""
        if not filename or not backup_suffix:
            return False
        
        backup_filename = f"{filename}.backup.{backup_suffix}"
        content = self.load(backup_filename)
        if not content:
            return False
        
        return self.save(filename, content)
    
    def list_backups(self, filename: str) -> List[str]:
        """List all backups for a CHAOS file."""
        if not filename:
            return []
        
        try:
            backup_prefix = f"{filename}.backup."
            backups = []
            
            for existing_file in os.listdir(self.chaos_dir):
                if existing_file.startswith(backup_prefix):
                    backups.append(existing_file)
            
            return sorted(backups, reverse=True)  # Most recent first
        except Exception as e:
            print(f"[ChaosStorage] Failed to list backups for {filename}: {e}")
            return []
    
    def export_file(self, filename: str, export_path: str) -> bool:
        """Export CHAOS file to external location."""
        if not filename or not export_path:
            return False
        
        content = self.load(filename)
        if not content:
            return False
        
        try:
            with open(export_path, "w", encoding="utf-8") as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"[ChaosStorage] Failed to export {filename} to {export_path}: {e}")
            return False
    
    def import_file(self, import_path: str, filename: str = None) -> bool:
        """Import CHAOS file from external location."""
        if not import_path:
            return False
        
        try:
            with open(import_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            if filename is None:
                import os
                filename = os.path.basename(import_path)
            
            return self.save(filename, content)
        except Exception as e:
            print(f"[ChaosStorage] Failed to import {import_path}: {e}")
            return False
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        try:
            files = self.list_files()
            total_size = 0
            file_count = len(files)
            
            for filename in files:
                info = self.get_file_info(filename)
                if info:
                    total_size += info["size"]
            
            return {
                "file_count": file_count,
                "total_size": total_size,
                "storage_dir": self.chaos_dir,
                "files": files
            }
        except Exception as e:
            print(f"[ChaosStorage] Failed to get storage stats: {e}")
            return {
                "file_count": 0,
                "total_size": 0,
                "storage_dir": self.chaos_dir,
                "files": []
            }
