"""Local MCP stub for development/testing.

This is a minimal implementation that provides parts of the
`mcp` API this server expects: `mcp.server.Server`, `mcp.server.tool`
decorator and `mcp.types` content classes. This stub is intentionally
lightweight and meant for dev/testing only.
"""

from .server import Server, tool
from .types import TextContent, JsonContent

__all__ = ["Server", "tool", "TextContent", "JsonContent"]
