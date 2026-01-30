from . import eden_tool, TextContent, JsonContent

import os

@eden_tool()
def list_dir(path: str):
    """
    List all files + folders in a path.
    """
    try:
        files = os.listdir(path)
        return [JsonContent(type="json", data={
            "path": path,
            "items": files
        })]
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {e}")]

@eden_tool()
def read_file(path: str):
    """
    Read text content of a file.
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = f.read()
        return [TextContent(type="text", text=data)]
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {e}")]
