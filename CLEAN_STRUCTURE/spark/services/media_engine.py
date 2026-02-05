#!/usr/bin/env python3
"""
EdenOS MCP Server Hub - Media Engine
Manages media registry with metadata analysis and tagging.
"""

import os
import json
import time
import hashlib
import mimetypes
from typing import Dict, Any, List, Optional

class MediaEngine:
    """Manages media registry with metadata analysis and tagging."""
    
    def __init__(self, media_dir: str = "media_files", registry_file: str = "media_registry.json"):
        self.media_dir = media_dir
        self.registry_file = registry_file
        self.hub = None  # Nerve hook
        
        # Ensure media directory exists
        os.makedirs(media_dir, exist_ok=True)
        
        # Media registry
        self._registry: Dict[str, Dict[str, Any]] = {}
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
        if event_type == "chaos.file.created":
            print(f"[MediaEngine] CHAOS file created: {payload.get('filename')}")
        elif event_type == "filesystem.written":
            # Check if written file is media and auto-register
            path = payload.get("path")
            if path and self._is_media_file(path):
                self.register_media(path)
        elif event_type == "chaos.tag.created":
            print(f"[MediaEngine] CHAOS tag created: {payload}")
    
    def _is_media_file(self, path: str) -> bool:
        """Check if file is a media file."""
        media_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', 
                          '.mp3', '.wav', '.ogg', '.flac', '.m4a',
                          '.mp4', '.avi', '.mkv', '.mov', '.webm',
                          '.pdf', '.doc', '.docx', '.txt', '.rtf'}
        return os.path.splitext(path)[1].lower() in media_extensions
    
    def _load_registry(self):
        """Load media registry from file."""
        try:
            if os.path.exists(self.registry_file):
                with open(self.registry_file, "r", encoding="utf-8") as f:
                    self._registry = json.load(f)
        except Exception as e:
            print(f"[MediaEngine] Failed to load registry: {e}")
            self._registry = {}
    
    def _save_registry(self) -> bool:
        """Save media registry to file."""
        try:
            with open(self.registry_file, "w", encoding="utf-8") as f:
                json.dump(self._registry, f, indent=2)
            return True
        except Exception as e:
            print(f"[MediaEngine] Failed to save registry: {e}")
            return False
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA-256 hash of file."""
        try:
            hash_sha256 = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception:
            return ""
    
    def _analyze_metadata(self, file_path: str) -> Dict[str, Any]:
        """Analyze file metadata."""
        try:
            stat = os.stat(file_path)
            mime_type, _ = mimetypes.guess_type(file_path)
            
            metadata = {
                "size": stat.st_size,
                "created": stat.st_ctime,
                "modified": stat.st_mtime,
                "mime_type": mime_type,
                "extension": os.path.splitext(file_path)[1].lower(),
                "filename": os.path.basename(file_path),
                "path": file_path
            }
            
            # Additional analysis based on file type
            if mime_type:
                if mime_type.startswith("image/"):
                    metadata.update(self._analyze_image_metadata(file_path))
                elif mime_type.startswith("audio/"):
                    metadata.update(self._analyze_audio_metadata(file_path))
                elif mime_type.startswith("video/"):
                    metadata.update(self._analyze_video_metadata(file_path))
                elif mime_type.startswith("text/"):
                    metadata.update(self._analyze_text_metadata(file_path))
            
            return metadata
            
        except Exception as e:
            return {"error": str(e)}
    
    def _analyze_image_metadata(self, file_path: str) -> Dict[str, Any]:
        """Analyze image metadata."""
        metadata = {"type": "image"}
        
        try:
            # Try to get basic image info
            from PIL import Image
            
            with Image.open(file_path) as img:
                metadata.update({
                    "width": img.width,
                    "height": img.height,
                    "format": img.format,
                    "mode": img.mode
                })
                
                # Calculate aspect ratio
                if img.height > 0:
                    metadata["aspect_ratio"] = img.width / img.height
                
        except ImportError:
            metadata["pil_not_available"] = True
        except Exception as e:
            metadata["image_analysis_error"] = str(e)
        
        return metadata
    
    def _analyze_audio_metadata(self, file_path: str) -> Dict[str, Any]:
        """Analyze audio metadata."""
        metadata = {"type": "audio"}
        
        try:
            # Try to get audio info using mutagen
            from mutagen import File
            
            audio_file = File(file_path)
            if audio_file is not None:
                metadata.update({
                    "duration": getattr(audio_file.info, 'length', None),
                    "bitrate": getattr(audio_file.info, 'bitrate', None),
                    "channels": getattr(audio_file.info, 'channels', None),
                    "sample_rate": getattr(audio_file.info, 'sample_rate', None)
                })
                
                # Extract tags
                if hasattr(audio_file, 'tags') and audio_file.tags:
                    tags = {}
                    for key, value in audio_file.tags.items():
                        if isinstance(value, list) and value:
                            tags[key] = str(value[0])
                        else:
                            tags[key] = str(value)
                    metadata["tags"] = tags
        
        except ImportError:
            metadata["mutagen_not_available"] = True
        except Exception as e:
            metadata["audio_analysis_error"] = str(e)
        
        return metadata
    
    def _analyze_video_metadata(self, file_path: str) -> Dict[str, Any]:
        """Analyze video metadata."""
        metadata = {"type": "video"}
        
        try:
            # Try to get video info using ffmpeg-python
            import ffmpeg
            
            probe = ffmpeg.probe(file_path)
            video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
            audio_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'audio'), None)
            
            if video_stream:
                metadata.update({
                    "width": int(video_stream.get('width', 0)),
                    "height": int(video_stream.get('height', 0)),
                    "duration": float(video_stream.get('duration', 0)),
                    "fps": eval(video_stream.get('r_frame_rate', '0/1')),
                    "codec": video_stream.get('codec_name'),
                    "bitrate": int(video_stream.get('bit_rate', 0))
                })
                
                if metadata["height"] > 0:
                    metadata["aspect_ratio"] = metadata["width"] / metadata["height"]
            
            if audio_stream:
                metadata.update({
                    "audio_codec": audio_stream.get('codec_name'),
                    "audio_bitrate": int(audio_stream.get('bit_rate', 0)),
                    "sample_rate": int(audio_stream.get('sample_rate', 0)),
                    "channels": int(audio_stream.get('channels', 0))
                })
        
        except ImportError:
            metadata["ffmpeg_not_available"] = True
        except Exception as e:
            metadata["video_analysis_error"] = str(e)
        
        return metadata
    
    def _analyze_text_metadata(self, file_path: str) -> Dict[str, Any]:
        """Analyze text metadata."""
        metadata = {"type": "text"}
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            metadata.update({
                "character_count": len(content),
                "word_count": len(content.split()),
                "line_count": len(content.splitlines()),
                "encoding": "utf-8"
            })
            
            # Language detection (simple heuristic)
            if content:
                # Simple character frequency analysis for language detection
                chinese_chars = len([c for c in content if '\u4e00' <= c <= '\u9fff'])
                japanese_chars = len([c for c in content if '\u3040' <= c <= '\u309f' or '\u30a0' <= c <= '\u30ff'])
                korean_chars = len([c for c in content if '\uac00' <= c <= '\ud7af'])
                
                total_chars = len(content)
                if total_chars > 0:
                    metadata["language_hints"] = {
                        "chinese_ratio": chinese_chars / total_chars,
                        "japanese_ratio": japanese_chars / total_chars,
                        "korean_ratio": korean_chars / total_chars
                    }
        
        except Exception as e:
            metadata["text_analysis_error"] = str(e)
        
        return metadata
    
    def register_media(self, file_path: str, tags: List[str] = None, description: str = None) -> bool:
        """Register a media file in the registry."""
        if not os.path.exists(file_path):
            return False
        
        try:
            # Calculate file hash
            file_hash = self._calculate_file_hash(file_path)
            
            # Analyze metadata
            metadata = self._analyze_metadata(file_path)
            
            # Create registry entry
            registry_id = file_hash or os.path.basename(file_path)
            self._registry[registry_id] = {
                "id": registry_id,
                "file_path": file_path,
                "metadata": metadata,
                "tags": tags or [],
                "description": description or "",
                "registered_at": time.time(),
                "updated_at": time.time()
            }
            
            # Emit media registered event
            if self.hub:
                self.hub.emit("media.registered", {
                    "media_id": registry_id,
                    "file_path": file_path,
                    "mime_type": metadata.get("mime_type"),
                    "tags": tags or []
                })
            
            return self._save_registry()
            
        except Exception as e:
            print(f"[MediaEngine] Failed to register {file_path}: {e}")
            return False
    
    def get_media_info(self, media_id: str) -> Optional[Dict[str, Any]]:
        """Get media information by ID."""
        return self._registry.get(media_id)
    
    def update_media_tags(self, media_id: str, tags: List[str]) -> bool:
        """Update media tags."""
        if media_id not in self._registry:
            return False
        
        self._registry[media_id]["tags"] = tags
        self._registry[media_id]["updated_at"] = time.time()
        
        return self._save_registry()
    
    def add_media_tag(self, media_id: str, tag: str) -> bool:
        """Add a tag to media."""
        if media_id not in self._registry:
            return False
        
        tags = self._registry[media_id]["tags"]
        if tag not in tags:
            tags.append(tag)
            self._registry[media_id]["updated_at"] = time.time()
            return self._save_registry()
        
        return True
    
    def remove_media_tag(self, media_id: str, tag: str) -> bool:
        """Remove a tag from media."""
        if media_id not in self._registry:
            return False
        
        tags = self._registry[media_id]["tags"]
        if tag in tags:
            tags.remove(tag)
            self._registry[media_id]["updated_at"] = time.time()
            return self._save_registry()
        
        return False
    
    def search_media(self, query: str = None, tags: List[str] = None, mime_type: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Search media registry."""
        results = []
        
        for media_id, media_data in self._registry.items():
            match = True
            
            # Search by query in filename and description
            if query:
                query_lower = query.lower()
                filename = media_data.get("metadata", {}).get("filename", "").lower()
                description = media_data.get("description", "").lower()
                
                if query_lower not in filename and query_lower not in description:
                    match = False
            
            # Filter by tags
            if tags and match:
                media_tags = set(media_data.get("tags", []))
                if not set(tags).issubset(media_tags):
                    match = False
            
            # Filter by mime type
            if mime_type and match:
                media_mime = media_data.get("metadata", {}).get("mime_type", "")
                if mime_type not in media_mime:
                    match = False
            
            if match:
                results.append({
                    "id": media_id,
                    **media_data
                })
                
                if len(results) >= limit:
                    break
        
        return results
    
    def list_all_media(self, limit: int = 100) -> List[Dict[str, Any]]:
        """List all registered media."""
        results = []
        
        for media_id, media_data in self._registry.items():
            results.append({
                "id": media_id,
                **media_data
            })
            
            if len(results) >= limit:
                break
        
        # Sort by registration date (most recent first)
        return sorted(results, key=lambda x: x.get("registered_at", 0), reverse=True)
    
    def get_media_by_tags(self, tags: List[str], match_all: bool = True) -> List[Dict[str, Any]]:
        """Get media by tags."""
        results = []
        
        for media_id, media_data in self._registry.items():
            media_tags = set(media_data.get("tags", []))
            search_tags = set(tags)
            
            if match_all:
                if search_tags.issubset(media_tags):
                    results.append({
                        "id": media_id,
                        **media_data
                    })
            else:
                if media_tags.intersection(search_tags):
                    results.append({
                        "id": media_id,
                        **media_data
                    })
        
        return results
    
    def delete_media(self, media_id: str, delete_file: bool = False) -> bool:
        """Delete media from registry."""
        if media_id not in self._registry:
            return False
        
        try:
            if delete_file:
                file_path = self._registry[media_id]["file_path"]
                if os.path.exists(file_path):
                    os.remove(file_path)
            
            del self._registry[media_id]
            return self._save_registry()
            
        except Exception as e:
            print(f"[MediaEngine] Failed to delete media {media_id}: {e}")
            return False
    
    def get_registry_stats(self) -> Dict[str, Any]:
        """Get registry statistics."""
        if not self._registry:
            return {"total_media": 0}
        
        stats = {
            "total_media": len(self._registry),
            "mime_types": {},
            "tags": {},
            "total_size": 0,
            "file_types": {}
        }
        
        for media_data in self._registry.values():
            # Count mime types
            mime_type = media_data.get("metadata", {}).get("mime_type", "unknown")
            stats["mime_types"][mime_type] = stats["mime_types"].get(mime_type, 0) + 1
            
            # Count file types
            file_type = media_data.get("metadata", {}).get("type", "unknown")
            stats["file_types"][file_type] = stats["file_types"].get(file_type, 0) + 1
            
            # Count tags
            for tag in media_data.get("tags", []):
                stats["tags"][tag] = stats["tags"].get(tag, 0) + 1
            
            # Sum sizes
            size = media_data.get("metadata", {}).get("size", 0)
            stats["total_size"] += size
        
        return stats
    
    def export_registry(self, export_path: str) -> bool:
        """Export media registry to file."""
        try:
            export_data = {
                "registry": self._registry,
                "exported_at": time.time(),
                "stats": self.get_registry_stats()
            }
            
            with open(export_path, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2)
            
            return True
            
        except Exception as e:
            print(f"[MediaEngine] Failed to export registry: {e}")
            return False
    
    def import_registry(self, import_path: str, merge_strategy: str = "merge") -> bool:
        """Import media registry from file."""
        try:
            with open(import_path, "r", encoding="utf-8") as f:
                import_data = json.load(f)
            
            imported_registry = import_data.get("registry", {})
            
            if merge_strategy == "replace":
                self._registry = imported_registry
            elif merge_strategy == "merge":
                self._registry.update(imported_registry)
            
            return self._save_registry()
            
        except Exception as e:
            print(f"[MediaEngine] Failed to import registry: {e}")
            return False

# Global media engine instance
media_engine = MediaEngine()
