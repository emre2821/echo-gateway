"""tools.archive_tools

Self-contained, read-only ZIP/archive inspection MCP tool intended to live
under ``tools/`` and be auto-discoverable via the ``@eden_tool()`` decorator.

Exports a single MCP-friendly function ``inspect_archive`` (decorated with
``@eden_tool``) that accepts either a local file path to a ``.zip`` file or
raw bytes of an archive via ``bytes_blob``.

Behavior:
    - Read-only: never writes to disk or extracts files.
    - Returns JSON-serializable metadata about the archive and its entries.
    - Provides optional small previews of file contents (text or base64) with
        safe limits.
    - Includes lightweight protections against obvious zip-bomb responses by
        limiting total reported/uncompressed sizes and max-preview bytes.

No external dependencies (stdlib only).
"""

from __future__ import annotations

import base64
import io
import json
import re
import zipfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union


# ---- eden_tool decorator retrieval / fallback registry ----
# Attempt to import a globally-provided decorator; if missing, define a no-op
# that registers tools into a local registry so the MCP loader can still
# introspect.
try:
    # typical in-repo pattern: tools package provides eden_tool
    from . import eden_tool  # type: ignore
except Exception:
    try:
        # alternative external package (if present)
        from edenos_sdk import eden_tool  # type: ignore
    except Exception:
        # fallback: simple registry and decorator
        _LOCAL_TOOL_REGISTRY: Dict[str, Dict[str, Any]] = {}

        def eden_tool(name: Optional[str] = None, **meta):
            def decorator(func):
                key = name or func.__name__
                _LOCAL_TOOL_REGISTRY[key] = {"func": func, "meta": meta}
                return func

            return decorator

        # expose registry attribute so a discovery mechanism can inspect it
        __mcp_local_tool_registry__ = _LOCAL_TOOL_REGISTRY  # type: ignore


# ---- dataclasses for JSON-serializable metadata ----
@dataclass
class EntryMeta:
    name: str
    is_dir: bool
    size: int
    compressed_size: int
    crc32: int
    mtime_iso: str
    comment: str
    compress_type: int


@dataclass
class ArchiveReport:
    archive_name: str
    archive_path: Optional[str]
    num_entries: int
    total_uncompressed_size: int
    total_compressed_size: int
    entries: List[Dict[str, Any]]
    warnings: List[str]


# ---- configuration / safety limits ----
MAX_TOTAL_UNCOMPRESSED = 50 * 1024 * 1024  # 50 MB total uncompressed to report
MAX_ENTRY_PREVIEW = 16 * 1024  # 16 KB preview per file
MAX_LISTED_ENTRIES = 1000  # maximum number of entries to include in listing
DEFAULT_PREVIEW_TEXT_BYTES = 2048  # default preview bytes if preview=True


# ---- helper utilities ----
def _zipinfo_mtime_iso(zinfo: zipfile.ZipInfo) -> str:
    try:
        dt = datetime(*zinfo.date_time, tzinfo=timezone.utc)
        return dt.isoformat()
    except Exception:
        return ""


def _safe_text_preview(
    data: bytes, max_bytes: int
) -> Tuple[Optional[str], Optional[str]]:
    """Try to decode bytes to text (utf-8 then latin-1).

    If it looks binary then return ``(None, None)``. Returns a tuple with the
    text preview and the detected encoding.
    """
    snippet = data[:max_bytes]
    for enc in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            text = snippet.decode(enc)
            # Heuristic: if NUL bytes present it's likely binary
            if "\x00" in text:
                return None, None
            return text, enc
        except Exception:
            continue
    return None, None


def _b64_preview(data: bytes, max_bytes: int) -> str:
    return base64.b64encode(data[:max_bytes]).decode("ascii")


def _human_size(n: float) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024.0:
            return f"{n:.1f}{unit}"
        n /= 1024.0
    return f"{n:.1f}TB"


# ---- core archive inspection primitives (read-only) ----
def _open_zip_from_path(path: Union[str, Path]) -> zipfile.ZipFile:
    return zipfile.ZipFile(str(path), mode="r")


def _open_zip_from_bytes(blob: bytes) -> zipfile.ZipFile:
    return zipfile.ZipFile(io.BytesIO(blob), mode="r")


def _collect_entry_meta(zinfo: zipfile.ZipInfo) -> EntryMeta:
    return EntryMeta(
        name=zinfo.filename,
        is_dir=zinfo.is_dir(),
        size=zinfo.file_size,
        compressed_size=zinfo.compress_size,
        crc32=zinfo.CRC,
        mtime_iso=_zipinfo_mtime_iso(zinfo),
        comment=(
            zinfo.comment.decode("utf-8", errors="ignore")
            if zinfo.comment
            else ""
        ),
        compress_type=zinfo.compress_type,
    )


def _build_report(
    zf: zipfile.ZipFile,
    archive_name: str,
    archive_path: Optional[str] = None,
    preview: bool = False,
    preview_bytes: int = DEFAULT_PREVIEW_TEXT_BYTES,
    max_entries: int = MAX_LISTED_ENTRIES,
) -> ArchiveReport:
    infos = zf.infolist()
    listed = []
    warnings: List[str] = []
    total_uncompressed = 0
    total_compressed = 0

    if len(infos) > max_entries:
        warnings.append(
            "Archive contains %d entries; listing truncated to %d entries." % (
                len(infos), max_entries
            )
        )

    for i, zinfo in enumerate(infos):
        if i >= max_entries:
            break
        meta = _collect_entry_meta(zinfo)
        total_uncompressed += meta.size
        total_compressed += meta.compressed_size

        entry_dict: Dict[str, Any] = asdict(meta)

        # Provide a small preview for non-directories, within safety limits
        if preview and not meta.is_dir:
            if total_uncompressed > MAX_TOTAL_UNCOMPRESSED:
                warnings.append(
                    "Total uncompressed size exceeds safety limit; "
                    "skipping previews."
                )
                entry_dict["preview"] = None
            else:
                # try to open and read a small chunk
                try:
                    with zf.open(zinfo, "r") as fh:
                        chunk = fh.read(
                            min(preview_bytes, MAX_ENTRY_PREVIEW)
                        )
                    text, enc = _safe_text_preview(chunk, preview_bytes)
                    if text is not None:
                        entry_dict["preview"] = {
                            "type": "text",
                            "encoding": enc,
                            "content": text,
                        }
                    else:
                        entry_dict["preview"] = {
                            "type": "base64",
                            "content": _b64_preview(chunk, preview_bytes),
                        }
                except Exception as e:
                    entry_dict["preview"] = None
                    warnings.append(
                        "Failed to preview entry %s: %s" % (meta.name, str(e))
                    )

        listed.append(entry_dict)

    # safety warning for zip bombs (naive)
    if total_uncompressed > MAX_TOTAL_UNCOMPRESSED:
        warnings.append(
            (
                "Total uncompressed size %d bytes exceeds the configured "
                "safety threshold (%s). Further previews were omitted."
            )
            % (total_uncompressed, _human_size(MAX_TOTAL_UNCOMPRESSED))
        )

    return ArchiveReport(
        archive_name=archive_name,
        archive_path=str(archive_path) if archive_path else None,
        num_entries=len(infos),
        total_uncompressed_size=total_uncompressed,
        total_compressed_size=total_compressed,
        entries=listed,
        warnings=warnings,
    )


# ---- search helper ----
def _search_in_entry(
    zf: zipfile.ZipFile,
    zinfo: zipfile.ZipInfo,
    pattern: Union[str, re.Pattern],
    max_matches: int = 3,
) -> List[Dict[str, Any]]:
    """Search a single entry's text (if decodable) for ``pattern``.

    Returns a list of matches with small context snippets.
    """
    matches = []
    try:
        with zf.open(zinfo, "r") as fh:
            raw = fh.read(MAX_ENTRY_PREVIEW * 16)
        text, _enc = _safe_text_preview(raw, len(raw))
        if text is None:
            return matches
        if isinstance(pattern, str):
            pat = re.compile(re.escape(pattern))
        else:
            pat = pattern
        for m in pat.finditer(text):
            start = max(m.start() - 40, 0)
            end = min(m.end() + 40, len(text))
            snippet = text[start:end]
            matches.append(
                {
                    "entry": zinfo.filename,
                    "match_span": [m.start(), m.end()],
                    "snippet": snippet,
                }
            )
            if len(matches) >= max_matches:
                break
    except Exception:
        # skip unreadable or binary entries
        pass
    return matches


# ---- MCP-exposed tool ----
@eden_tool(
    name="archive_inspect",
    description=(
        "Read-only ZIP/archive inspection tool"
    ),
)
def inspect_archive(
    path: Optional[str] = None,
    bytes_blob: Optional[bytes] = None,
    *,
    preview: bool = False,
    preview_bytes: int = DEFAULT_PREVIEW_TEXT_BYTES,
    max_entries: int = 200,
    search: Optional[str] = None,
    case_sensitive: bool = False,
) -> Dict[str, Any]:
    """
    Inspect a ZIP archive (provided as path or bytes) and return metadata.

    Parameters:
        path: local filesystem path to a ``.zip`` file (string). If provided,
            ``bytes_blob`` is ignored.
        bytes_blob: raw bytes of a ZIP archive.
        preview: whether to include small previews of file contents (text or
            base64).
        preview_bytes: how many bytes to use for preview attempts; bounded by
            ``MAX_ENTRY_PREVIEW``.
        max_entries: maximum number of entries to list (safety cap).
        search: optional substring or regex to search inside text-decodable
            entries.
        case_sensitive: affect search when ``search`` is provided as substring.

    Returns:
        A JSON-serializable dict with keys:
          - archive: archive metadata and entries
          - search_matches: list of matches if search provided
    """
    if not path and not bytes_blob:
        raise ValueError("One of `path` or `bytes_blob` must be provided.")

    if preview_bytes <= 0:
        preview_bytes = DEFAULT_PREVIEW_TEXT_BYTES
    preview_bytes = min(preview_bytes, MAX_ENTRY_PREVIEW)

    # ensure max_entries reasonable
    max_entries = max(1, min(max_entries, MAX_LISTED_ENTRIES))

    zf = None
    archive_path = None
    archive_name = "<bytes>"
    try:
        if path:
            p = Path(path)
            if not p.exists() or not p.is_file():
                raise FileNotFoundError(f"Archive path not found: {path}")
            archive_path = str(p.resolve())
            archive_name = p.name
            zf = _open_zip_from_path(p)
        else:
            archive_name = "<bytes_blob>"
            # bytes_blob is checked earlier; assert for type-checkers
            assert bytes_blob is not None
            zf = _open_zip_from_bytes(bytes_blob)

        report = _build_report(
            zf,
            archive_name,
            archive_path,
            preview=preview,
            preview_bytes=preview_bytes,
            max_entries=max_entries,
        )

        result: Dict[str, Any] = {"archive": asdict(report)}

        # optional search
        if search:
            if case_sensitive:
                pattern = search
            else:
                pattern = re.compile(re.escape(search), re.IGNORECASE)

            matches: List[Dict[str, Any]] = []
            # Iterate through entries, bounded to avoid scanning huge archives.
            for zinfo in zf.infolist()[:max_entries]:
                if zinfo.is_dir():
                    continue
                matches.extend(_search_in_entry(zf, zinfo, pattern))
                if len(matches) >= 100:
                    break

            result["search_matches"] = matches

        return result
    finally:
        try:
            if zf:
                zf.close()
        except Exception:
            pass


# ---- convenience CLI when run directly (useful for local dev) ----
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(
        description=("Read-only ZIP inspector (tool)")
    )
    parser.add_argument(
        "path",
        nargs="?",
        help="Path to .zip file",
    )
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Include small previews",
    )
    parser.add_argument(
        "--preview-bytes",
        type=int,
        default=DEFAULT_PREVIEW_TEXT_BYTES,
    )
    parser.add_argument(
        "--max-entries",
        type=int,
        default=200,
    )
    parser.add_argument(
        "--search",
        type=str,
        help=(
            "Search substring or regex (case-insensitive by default)"
        ),
    )
    args = parser.parse_args()

    if not args.path:
        print("Provide a path to a ZIP file.")
        raise SystemExit(2)

    with open(args.path, "rb") as f:
        blob = f.read()

    out = inspect_archive(
        path=args.path,
        bytes_blob=None,
        preview=args.preview,
        preview_bytes=args.preview_bytes,
        max_entries=args.max_entries,
        search=args.search,
    )

    print(json.dumps(out, indent=2, ensure_ascii=False))
