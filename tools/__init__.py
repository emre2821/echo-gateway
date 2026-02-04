"""Tools package helpers and small compatibility shims for MCP dev server.

Provides:
- eden_tool: decorator used to mark functions as MCP tools (adds _mcp_tool)
- TextContent, JsonContent: small container types used by tool functions

This file intentionally keeps the runtime behavior minimal and import-safe so
importing tools modules doesn't have side-effects.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable
import inspect


@dataclass
class TextContent:
    type: str = "text"
    text: str = ""


@dataclass
class JsonContent:
    type: str = "json"
    data: Any = None


def eden_tool(*dargs, **dkwargs) -> Callable:
    """Decorator to mark a function as an MCP tool.

    Usage:
      @eden_tool()
      def foo(...):
          ...

    or

      @eden_tool
      def foo(...):
          ...
    """

    def decorator(func: Callable) -> Callable:
        setattr(func, "_mcp_tool", True)
        func._eden_metadata = {
            "name": func.__name__,
            "doc": inspect.getdoc(func),
            "signature": str(inspect.signature(func)),
        }
        return func

    # support @eden_tool (no parens) and @eden_tool() (with parens)
    if len(dargs) == 1 and callable(dargs[0]):
        return decorator(dargs[0])
    return decorator


__all__ = ["eden_tool", "TextContent", "JsonContent"]
