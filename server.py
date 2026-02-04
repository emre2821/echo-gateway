# server.py
import importlib
import pkgutil
from mcp.server import Server

server = Server("eden-mcp-server")


def _log(msg: str):
    try:
        # prefer eden_log if available
        from core.logging import eden_log

        eden_log(msg)
    except Exception:
        print(f"[eden-mcp] {msg}")


def load_tools():
    """
    Auto-import all modules inside the tools/ folder,
    and register any functions decorated with @eden_tool().

    Resilient to import/register errors so a single bad tool
    cannot crash the whole server.
    """
    import tools

    for module_info in pkgutil.iter_modules(tools.__path__):
        module_name = f"tools.{module_info.name}"
        try:
            module = importlib.import_module(module_name)
        except Exception as e:
            _log(f"Failed importing {module_name}: {e}")
            continue

        for attr in dir(module):
            obj = getattr(module, attr)
            if callable(obj) and hasattr(obj, "_mcp_tool"):
                try:
                    server.register_tool(obj)
                    _log(f"Registered tool {attr} from {module_name}")
                except Exception as e:
                    _log(f"Failed registering {attr} from {module_name}: {e}")
                    continue


def main():
    load_tools()
    server.run()


if __name__ == "__main__":
    main()
