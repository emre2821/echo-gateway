# chaos_tools.py

from . import eden_tool, TextContent, JsonContent
from typing import Dict

@eden_tool()
def chaos_inspect(text: str):
    """
    Basic CHAOS diagnostic tool.
    Returns structural clues, tag counts, and metadata.
    This is a staging version until the real parser is plugged in.
    """
    lines = text.splitlines()
    length = len(text)
    num_lines = len(lines)

    tag_counts: Dict[str, int] = {}
    for line in lines:
        if line.strip().startswith("[") and "]" in line:
            tag = line.strip().split("]")[0] + "]"
            tag_counts[tag] = tag_counts.get(tag, 0) + 1

    return [JsonContent(
        type="json",
        data={
            "length": length,
            "lines": num_lines,
            "tags_detected": tag_counts,
            "preview": text[:300]
        }
    )]

@eden_tool()
def chaos_extract_tags(text: str):
    """
    Extract all CHAOS tags in order.
    Good for debugging and tooling integration.
    """
    tags = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("[") and "]" in stripped:
            tag = stripped.split("]", 1)[0] + "]"
            tags.append(tag)

    return [JsonContent(
        type="json",
        data={
            "count": len(tags),
            "tags": tags
        }
    )]

@eden_tool()
def chaos_echo(text: str):
    """
    A simple passthrough tool.
    Useful for testing Dev Mode pipes.
    """
    return [TextContent(type="text", text=text)]
