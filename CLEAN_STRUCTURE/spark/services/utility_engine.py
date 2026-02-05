#!/usr/bin/env python3
"""
EdenOS MCP Server Hub - Utility Engine
Handles git operations, archive management, and checksum utilities.
"""

import os
import hashlib
import tarfile
import zipfile
import subprocess
from typing import Dict, Any, List, Optional
from permissions_engine import permissions_engine

class UtilityEngine:
    """Handles git operations, archive management, and checksum utilities."""
    
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
        if event_type == "filesystem.written":
            # Auto-calculate checksums for important files
            path = payload.get("path")
            if path and self._should_checksum(path):
                checksum = self.calculate_checksum(path)
                if checksum:
                    print(f"[UtilityEngine] Auto-checksum for {path}: {checksum[:16]}...")
        elif event_type == "system.started":
            print("[UtilityEngine] System started - ready for operations")
        elif event_type == "chaos.file.created":
            print(f"[UtilityEngine] CHAOS file created: {payload.get('filename')}")
    
    def _should_checksum(self, path: str) -> bool:
        """Check if file should be auto-checksummed."""
        important_extensions = {'.py', '.json', '.md', '.txt', '.yml', '.yaml'}
        return os.path.splitext(path)[1].lower() in important_extensions
    
    # ==================== CHECKSUM UTILITIES ====================
    
    def calculate_checksum(self, file_path: str, algorithm: str = "sha256") -> Optional[str]:
        """Calculate checksum of a file."""
        if not self.permissions.is_path_allowed(file_path, "read"):
            return None
        
        if not os.path.exists(file_path):
            return None
        
        try:
            hash_func = getattr(hashlib, algorithm.lower(), None)
            if not hash_func:
                return None
            
            with open(file_path, "rb") as f:
                hash_obj = hash_func()
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_obj.update(chunk)
                checksum = hash_obj.hexdigest()
                
                # Emit checksum calculated event
                if self.hub:
                    self.hub.emit("utility.checksum.calculated", {
                        "file_path": file_path,
                        "algorithm": algorithm,
                        "checksum": checksum
                    })
                
                return checksum
        
        except Exception as e:
            print(f"[UtilityEngine] Failed to calculate checksum for {file_path}: {e}")
            return None
    
    def verify_checksum(self, file_path: str, expected_checksum: str, algorithm: str = "sha256") -> bool:
        """Verify file checksum."""
        actual_checksum = self.calculate_checksum(file_path, algorithm)
        return actual_checksum == expected_checksum if actual_checksum else False
    
    def calculate_directory_checksum(self, dir_path: str, algorithm: str = "sha256", ignore_patterns: List[str] = None) -> Optional[str]:
        """Calculate checksum of entire directory."""
        if not self.permissions.is_path_allowed(dir_path, "read"):
            return None
        
        if not os.path.isdir(dir_path):
            return None
        
        try:
            hash_func = getattr(hashlib, algorithm.lower(), None)
            if not hash_func:
                return None
            
            hash_obj = hash_func()
            ignore_patterns = ignore_patterns or ["__pycache__", ".git", "*.pyc"]
            
            for root, dirs, files in os.walk(dir_path):
                # Sort for consistent ordering
                dirs.sort()
                files.sort()
                
                for file in files:
                    file_path = os.path.join(root, file)
                    
                    # Check ignore patterns
                    should_ignore = False
                    for pattern in ignore_patterns:
                        if pattern in file_path or file_path.endswith(pattern):
                            should_ignore = True
                            break
                    
                    if not should_ignore and self.permissions.is_path_allowed(file_path, "read"):
                        # Add relative path to hash
                        rel_path = os.path.relpath(file_path, dir_path)
                        hash_obj.update(rel_path.encode())
                        
                        # Add file content to hash
                        with open(file_path, "rb") as f:
                            for chunk in iter(lambda: f.read(4096), b""):
                                hash_obj.update(chunk)
            
            return hash_obj.hexdigest()
        
        except Exception as e:
            print(f"[UtilityEngine] Failed to calculate directory checksum for {dir_path}: {e}")
            return None
    
    # ==================== ARCHIVE UTILITIES ====================
    
    def create_archive(self, source_path: str, archive_path: str, format_type: str = "zip", compression: str = None) -> bool:
        """Create archive from source path."""
        if not self.permissions.is_path_allowed(source_path, "read"):
            return False
        
        if not self.permissions.is_path_allowed(archive_path, "write"):
            return False
        
        try:
            # Create archive directory if needed
            os.makedirs(os.path.dirname(archive_path), exist_ok=True)
            
            if format_type.lower() == "zip":
                return self._create_zip_archive(source_path, archive_path, compression)
            elif format_type.lower() in ["tar", "tar.gz", "tgz", "tar.bz2", "tbz2"]:
                return self._create_tar_archive(source_path, archive_path, format_type, compression)
            else:
                print(f"[UtilityEngine] Unsupported archive format: {format_type}")
                return False
        
        except Exception as e:
            print(f"[UtilityEngine] Failed to create archive {archive_path}: {e}")
            return False
    
    def _create_zip_archive(self, source_path: str, archive_path: str, compression: str = None) -> bool:
        """Create ZIP archive."""
        try:
            compression_map = {
                "deflate": zipfile.ZIP_DEFLATED,
                "stored": zipfile.ZIP_STORED,
                "bzip2": zipfile.ZIP_BZIP2,
                "lzma": zipfile.ZIP_LZMA
            }
            
            compression_type = compression_map.get(compression.lower(), zipfile.ZIP_DEFLATED)
            
            with zipfile.ZipFile(archive_path, 'w', compression_type) as zipf:
                if os.path.isfile(source_path):
                    zipf.write(source_path, os.path.basename(source_path))
                elif os.path.isdir(source_path):
                    for root, dirs, files in os.walk(source_path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arc_path = os.path.relpath(file_path, os.path.dirname(source_path))
                            zipf.write(file_path, arc_path)
            
            return True
        
        except Exception as e:
            print(f"[UtilityEngine] Failed to create ZIP archive: {e}")
            return False
    
    def _create_tar_archive(self, source_path: str, archive_path: str, format_type: str, compression: str = None) -> bool:
        """Create TAR archive."""
        try:
            # Determine compression
            if format_type in ["tar.gz", "tgz"]:
                mode = "w:gz"
            elif format_type in ["tar.bz2", "tbz2"]:
                mode = "w:bz2"
            else:
                mode = "w"
            
            with tarfile.open(archive_path, mode) as tarf:
                if os.path.isfile(source_path):
                    tarf.add(source_path, arcname=os.path.basename(source_path))
                elif os.path.isdir(source_path):
                    tarf.add(source_path, arcname=os.path.basename(source_path))
            
            return True
        
        except Exception as e:
            print(f"[UtilityEngine] Failed to create TAR archive: {e}")
            return False
    
    def extract_archive(self, archive_path: str, extract_path: str) -> bool:
        """Extract archive to path."""
        if not self.permissions.is_path_allowed(archive_path, "read"):
            return False
        
        if not self.permissions.is_path_allowed(extract_path, "write"):
            return False
        
        try:
            os.makedirs(extract_path, exist_ok=True)
            
            if archive_path.endswith('.zip'):
                with zipfile.ZipFile(archive_path, 'r') as zipf:
                    zipf.extractall(extract_path)
            else:
                with tarfile.open(archive_path, 'r:*') as tarf:
                    tarf.extractall(extract_path)
            
            return True
        
        except Exception as e:
            print(f"[UtilityEngine] Failed to extract archive {archive_path}: {e}")
            return False
    
    def list_archive_contents(self, archive_path: str) -> List[Dict[str, Any]]:
        """List contents of archive."""
        if not self.permissions.is_path_allowed(archive_path, "read"):
            return []
        
        try:
            contents = []
            
            if archive_path.endswith('.zip'):
                with zipfile.ZipFile(archive_path, 'r') as zipf:
                    for info in zipf.infolist():
                        contents.append({
                            "filename": info.filename,
                            "size": info.file_size,
                            "compressed_size": info.compress_size,
                            "is_directory": info.is_dir(),
                            "modified": info.date_time
                        })
            else:
                with tarfile.open(archive_path, 'r:*') as tarf:
                    for member in tarf.getmembers():
                        contents.append({
                            "filename": member.name,
                            "size": member.size,
                            "is_directory": member.isdir(),
                            "modified": member.mtime
                        })
            
            return contents
        
        except Exception as e:
            print(f"[UtilityEngine] Failed to list archive contents {archive_path}: {e}")
            return []
    
    # ==================== GIT UTILITIES ====================
    
    def is_git_repository(self, path: str) -> bool:
        """Check if path is a git repository."""
        if not self.permissions.is_path_allowed(path, "read"):
            return False
        
        try:
            git_dir = os.path.join(path, ".git")
            return os.path.exists(git_dir)
        except Exception:
            return False
    
    def get_git_status(self, path: str) -> Optional[Dict[str, Any]]:
        """Get git status of repository."""
        if not self.is_git_repository(path):
            return None
        
        try:
            # Change to repository directory
            original_cwd = os.getcwd()
            os.chdir(path)
            
            # Get git status
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                return None
            
            # Parse status output
            modified_files = []
            untracked_files = []
            staged_files = []
            
            for line in result.stdout.strip().split('\n'):
                if line:
                    status_code = line[:2]
                    file_path = line[3:]
                    
                    if status_code[0] in ['M', 'A', 'D', 'R', 'C']:
                        staged_files.append(file_path)
                    if status_code[1] in ['M', 'D']:
                        modified_files.append(file_path)
                    if status_code == '??':
                        untracked_files.append(file_path)
            
            # Get current branch
            branch_result = subprocess.run(
                ["git", "branch", "--show-current"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            current_branch = branch_result.stdout.strip() if branch_result.returncode == 0 else "unknown"
            
            # Get last commit info
            commit_result = subprocess.run(
                ["git", "log", "-1", "--format=%H|%s|%an|%ad", "--date=iso"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            last_commit = None
            if commit_result.returncode == 0:
                commit_parts = commit_result.stdout.strip().split('|')
                if len(commit_parts) >= 4:
                    last_commit = {
                        "hash": commit_parts[0],
                        "message": commit_parts[1],
                        "author": commit_parts[2],
                        "date": commit_parts[3]
                    }
            
            os.chdir(original_cwd)
            
            return {
                "path": path,
                "current_branch": current_branch,
                "is_clean": len(modified_files) == 0 and len(untracked_files) == 0 and len(staged_files) == 0,
                "staged_files": staged_files,
                "modified_files": modified_files,
                "untracked_files": untracked_files,
                "last_commit": last_commit
            }
        
        except Exception as e:
            print(f"[UtilityEngine] Failed to get git status for {path}: {e}")
            if 'original_cwd' in locals():
                os.chdir(original_cwd)
            return None
    
    def get_git_log(self, path: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get git commit history."""
        if not self.is_git_repository(path):
            return []
        
        try:
            original_cwd = os.getcwd()
            os.chdir(path)
            
            result = subprocess.run(
                ["git", "log", f"-{limit}", "--format=%H|%s|%an|%ad|%p", "--date=iso"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            os.chdir(original_cwd)
            
            if result.returncode != 0:
                return []
            
            commits = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    parts = line.split('|')
                    if len(parts) >= 4:
                        commits.append({
                            "hash": parts[0],
                            "message": parts[1],
                            "author": parts[2],
                            "date": parts[3],
                            "parents": parts[4].split() if len(parts) > 4 else []
                        })
            
            return commits
        
        except Exception as e:
            print(f"[UtilityEngine] Failed to get git log for {path}: {e}")
            if 'original_cwd' in locals():
                os.chdir(original_cwd)
            return []
    
    def git_add(self, path: str, files: List[str]) -> bool:
        """Add files to git staging area."""
        if not self.is_git_repository(path):
            return False
        
        try:
            original_cwd = os.getcwd()
            os.chdir(path)
            
            for file_path in files:
                if not self.permissions.is_path_allowed(file_path, "read"):
                    continue
                
                result = subprocess.run(
                    ["git", "add", file_path],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode != 0:
                    print(f"[UtilityEngine] Failed to add {file_path}: {result.stderr}")
                    os.chdir(original_cwd)
                    return False
            
            os.chdir(original_cwd)
            return True
        
        except Exception as e:
            print(f"[UtilityEngine] Failed to git add: {e}")
            if 'original_cwd' in locals():
                os.chdir(original_cwd)
            return False
    
    def git_commit(self, path: str, message: str, author: str = None) -> bool:
        """Create git commit."""
        if not self.is_git_repository(path):
            return False
        
        try:
            original_cwd = os.getcwd()
            os.chdir(path)
            
            cmd = ["git", "commit", "-m", message]
            if author:
                cmd.extend(["--author", author])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            os.chdir(original_cwd)
            return result.returncode == 0
        
        except Exception as e:
            print(f"[UtilityEngine] Failed to git commit: {e}")
            if 'original_cwd' in locals():
                os.chdir(original_cwd)
            return False
    
    def git_pull(self, path: str, remote: str = "origin", branch: str = None) -> bool:
        """Pull changes from remote."""
        if not self.is_git_repository(path):
            return False
        
        try:
            original_cwd = os.getcwd()
            os.chdir(path)
            
            cmd = ["git", "pull", remote]
            if branch:
                cmd.append(branch)
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            os.chdir(original_cwd)
            return result.returncode == 0
        
        except Exception as e:
            print(f"[UtilityEngine] Failed to git pull: {e}")
            if 'original_cwd' in locals():
                os.chdir(original_cwd)
            return False
    
    def git_push(self, path: str, remote: str = "origin", branch: str = None) -> bool:
        """Push changes to remote."""
        if not self.is_git_repository(path):
            return False
        
        try:
            original_cwd = os.getcwd()
            os.chdir(path)
            
            cmd = ["git", "push", remote]
            if branch:
                cmd.append(branch)
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            os.chdir(original_cwd)
            return result.returncode == 0
        
        except Exception as e:
            print(f"[UtilityEngine] Failed to git push: {e}")
            if 'original_cwd' in locals():
                os.chdir(original_cwd)
            return False
    
    # ==================== METADATA UTILITIES ====================
    
    def get_file_metadata(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive file metadata."""
        if not self.permissions.is_path_allowed(file_path, "read"):
            return None
        
        try:
            stat = os.stat(file_path)
            
            metadata = {
                "path": file_path,
                "name": os.path.basename(file_path),
                "size": stat.st_size,
                "created": stat.st_ctime,
                "modified": stat.st_mtime,
                "accessed": stat.st_atime,
                "is_file": os.path.isfile(file_path),
                "is_directory": os.path.isdir(file_path),
                "extension": os.path.splitext(file_path)[1],
                "parent": os.path.dirname(file_path),
                "checksum": {
                    "md5": self.calculate_checksum(file_path, "md5"),
                    "sha1": self.calculate_checksum(file_path, "sha1"),
                    "sha256": self.calculate_checksum(file_path, "sha256")
                }
            }
            
            # Add git information if in repository
            if self.is_git_repository(os.path.dirname(file_path)):
                git_status = self.get_git_status(os.path.dirname(file_path))
                if git_status:
                    metadata["git"] = {
                        "repository": os.path.dirname(file_path),
                        "branch": git_status["current_branch"],
                        "is_tracked": file_path not in git_status["untracked_files"],
                        "is_modified": file_path in git_status["modified_files"] or file_path in git_status["staged_files"]
                    }
            
            return metadata
        
        except Exception as e:
            print(f"[UtilityEngine] Failed to get metadata for {file_path}: {e}")
            return None

# Global utility engine instance
utility_engine = UtilityEngine()
