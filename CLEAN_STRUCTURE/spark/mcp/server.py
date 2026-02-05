import functools

import inspect
import threading


class Server:
    def __init__(self, name: str = "mcp-server"):
        self.name = name
        self._tools = []

    def register_tool(self, func):
        self._tools.append(func)

    def list_tools(self):
        return [f.__name__ for f in self._tools]

    def run(self):
        # Minimal run: announce available tools and return.
        print(f"[mcp stub] Server '{self.name}' starting. Registered tools: {self.list_tools()}")
        # In a real implementation this would block and use stdio/transport.


def tool(*dargs, **dkwargs):
    """A decorator that marks functions as MCP tools.

    The decorator attaches metadata onto the function so the server
    can discover and register it.
    """

    def decorator(func):
        setattr(func, "_mcp_tool", True)
        # copy signature metadata as attribute for introspection if needed
        func._mcp_metadata = {
            "name": func.__name__,
            "doc": inspect.getdoc(func),
            "signature": str(inspect.signature(func)),
        }
        return func

    # if used without args
    if len(dargs) == 1 and callable(dargs[0]):
        return decorator(dargs[0])
    return decorator
