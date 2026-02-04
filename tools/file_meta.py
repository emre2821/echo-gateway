"""
tools/file_meta.py

Read-only file metadata inspector for MCP Server.

Provides basic metadata for a server-side path or uploaded bytes. Auto-
discoverable via @eden_tool(). Uses stdlib only and respects organizer
exclusions (will deny access to protected paths).
"""
from __future__ import annotations

import datetime
import mimetypes
import os
import stat
from typing import Dict, List, Optional

from . import JsonContent, eden_tool

try:
    from .organizer_tools import is_excluded
except Exception:
    def is_excluded(path: str) -> bool:  # type: ignore
        return False


# Limits
MAX_PREVIEW_BYTES = 16 * 1024
DEFAULT_PREVIEW_BYTES = 512


def _is_text_bytes(blob: bytes) -> bool:
    # simple heuristic: no null bytes and decodable as utf-8
    if b"\x00" in blob:
        return False
    try:
        blob.decode("utf-8")
        return True
    except Exception:
        return False


def _iso(ts: float) -> str:
    return datetime.datetime.fromtimestamp(ts).isoformat()


@eden_tool()
def get_file_meta(
    path: Optional[str] = None,
    bytes_blob: Optional[bytes] = None,
    preview: bool = False,
    preview_bytes: int = DEFAULT_PREVIEW_BYTES,
) -> List[object]:
    """Return metadata for `path` or `bytes_blob`.

    If `path` is provided, the server will read stat info (read-only).
    If `bytes_blob` is provided, a synthetic metadata record is returned.
    `preview` and `preview_bytes` control an optional small sample.

    Returns a single JsonContent item whose `data` is a dict describing the
    file (keys include file, exists, is_file, is_dir, size, mode, mtime,
    ctime, mime, is_text and preview).
    """
    report: Dict[str, object] = {
        "file": None,
        "exists": False,
        "is_file": False,
        "is_dir": False,
        "size": None,
        "mode": None,
        "mtime": None,
        "ctime": None,
        "mime": None,
        "is_text": None,
        "preview": None,
        "error": None,
    }

    try:
        if not path and bytes_blob is None:
            raise ValueError("One of `path` or `bytes_blob` must be provided")

        if path:
            if not os.path.exists(path):
                report["file"] = path
                report["exists"] = False
                return [JsonContent(type="json", data=report)]

            # enforce organizer exclusions
            if is_excluded(path):
                raise PermissionError("Access denied: protected path")

            st = os.stat(path)
            report["file"] = os.path.abspath(path)
            report["exists"] = True
            report["is_file"] = stat.S_ISREG(st.st_mode)
            report["is_dir"] = stat.S_ISDIR(st.st_mode)
            report["size"] = st.st_size
            report["mode"] = oct(st.st_mode & 0o777)
            report["mtime"] = _iso(st.st_mtime)
            report["ctime"] = _iso(st.st_ctime)
            mime, _ = mimetypes.guess_type(path)
            report["mime"] = mime

            if preview and report["is_file"]:
                pb = min(preview_bytes, MAX_PREVIEW_BYTES)
                try:
                    with open(path, "rb") as fh:
                        sample = fh.read(pb)
                    if _is_text_bytes(sample):
                        report["is_text"] = True
                        _s = sample.decode("utf-8", errors="replace")
                        report["preview"] = _s
                    else:
                        report["is_text"] = False
                        report["preview"] = sample[:64].hex()
                except Exception as e:
                    report["preview"] = None
                    report["error"] = f"preview_error: {e}"

        else:
            # bytes_blob provided
            if not isinstance(bytes_blob, (bytes, bytearray)):
                raise ValueError("bytes_blob must be bytes")
            report["file"] = "<bytes>"
            report["exists"] = True
            report["is_file"] = True
            report["is_dir"] = False
            report["size"] = len(bytes_blob)
            report["mode"] = None
            report["mtime"] = None
            report["ctime"] = None
            report["mime"] = None

            if preview:
                pb = min(preview_bytes, MAX_PREVIEW_BYTES)
                sample = bytes(bytes_blob)[:pb]
                if _is_text_bytes(sample):
                    report["is_text"] = True
                    _s = sample.decode("utf-8", errors="replace")
                    report["preview"] = _s
                else:
                    report["is_text"] = False
                    report["preview"] = sample[:64].hex()

    except Exception as e:
        report["error"] = str(e)

    return [JsonContent(type="json", data=report)]
