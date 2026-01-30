"""
tools/checksum_tool.py

Read-only checksum computation tool for MCP Server.

Usage:
  - compute checksums for a local file path (server-side) or uploaded bytes
  - respects organizer permission exclusions (will deny protected paths)
  - returns a JSON-serializable report wrapped in JsonContent

Design constraints:
  - Single-file, stdlib-only
  - Auto-discoverable via @eden_tool()
  - Read-only by default (never writes to disk)
"""
from __future__ import annotations

import hashlib
import os
from typing import Dict, List, Optional

from . import JsonContent, eden_tool

try:
    # organizer_tools provides is_excluded and allowed-path logic
    from .organizer_tools import is_excluded
except Exception:
    # fallback: permissive (no exclusion) if organizer_tools not available
    def is_excluded(path: str) -> bool:  # type: ignore
        return False


# Safety/config
MAX_BYTES = 200 * 1024 * 1024  # 200 MB max for bytes_blob
CHUNK_SIZE = 64 * 1024
DEFAULT_ALGORITHMS = ["sha256", "md5"]


def _hash_bytes(blob: bytes, algos: List[str]) -> Dict[str, str]:
    res: Dict[str, hashlib._Hash] = {}
    for a in algos:
        try:
            res[a] = hashlib.new(a)
        except Exception:
            # ignore unsupported algorithms
            continue
    for h in res.values():
        h.update(blob)
    return {k: v.hexdigest() for k, v in res.items()}


def _hash_file(path: str, algos: List[str]) -> Dict[str, str]:
    digest_map: Dict[str, hashlib._Hash] = {}
    for a in algos:
        try:
            digest_map[a] = hashlib.new(a)
        except Exception:
            continue

    with open(path, "rb") as fh:
        while True:
            chunk = fh.read(CHUNK_SIZE)
            if not chunk:
                break
            for h in digest_map.values():
                h.update(chunk)

    return {k: v.hexdigest() for k, v in digest_map.items()}


@eden_tool()
def compute_checksums(
    path: Optional[str] = None,
    bytes_blob: Optional[bytes] = None,
    algorithms: Optional[List[str]] = None,
) -> List[Dict[str, object]]:
    """Compute checksums for a file path or raw bytes.

    Parameters
    - path: server-side absolute or relative path to a file (preferred)
    - bytes_blob: raw bytes of a file (useful for uploads)
    - algorithms: list of hash names (defaults to sha256 and md5)

    Returns a list containing a single JsonContent with keys:
      file, size, checksums, warnings, error
    """
    algs = algorithms or DEFAULT_ALGORITHMS

    report: Dict[str, object] = {
        "file": None,
        "size": None,
        "checksums": {},
        "warnings": [],
        "error": None,
    }

    try:
        if not path and not bytes_blob:
            raise ValueError("One of `path` or `bytes_blob` must be provided.")

        if path:
            # ensure path exists and is a file
            if not os.path.exists(path) or not os.path.isfile(path):
                raise FileNotFoundError(f"File not found: {path}")

            # check permission/exclusion
            if is_excluded(path):
                raise PermissionError("Access denied: protected path")

            size = os.path.getsize(path)
            report["file"] = os.path.abspath(path)
            report["size"] = size
            report["checksums"] = _hash_file(path, algs)

        else:
            # bytes_blob path
            if not isinstance(bytes_blob, (bytes, bytearray)):
                raise ValueError("bytes_blob must be bytes")
            if len(bytes_blob) > MAX_BYTES:
                raise ValueError("bytes_blob exceeds maximum allowed size")
            report["file"] = "<bytes>"
            report["size"] = len(bytes_blob)
            report["checksums"] = _hash_bytes(bytes(bytes_blob), algs)

    except Exception as e:
        report["error"] = str(e)

    return [JsonContent(type="json", data=report)]
