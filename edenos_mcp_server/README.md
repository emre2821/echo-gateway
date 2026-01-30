# EdenOS MCP Server

A complete MCP (Model Context Protocol) server with auto-discovery, permissions system, and HTTP API support.

## Features

- **Auto-discovery**: Automatically loads tools from the `tools/` directory
- **Modular architecture**: Easy to extend with new tools
- **Permission system**: Safe file operations with granular permissions
- **HTTP API**: RESTful interface for SaaS-style usage
- **Rich logging**: Beautiful console output with Rich

## Installation

1. Clone or copy the `edenos_mcp_server` directory
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Running the Server

```bash
python server.py
```

The server will start and automatically discover all tools in the `tools/` directory.

### Available Tools

The server includes the following built-in tools:

#### Agent Tools
- `agent_ping(agent_name)` - Test connectivity to an agent

#### CHAOS Tools
- `chaos_inspect(text)` - Analyze CHAOS text structure
- `chaos_extract_tags(text)` - Extract CHAOS tags from text
- `chaos_echo(text)` - Simple passthrough for testing

#### Filesystem Tools
- `list_dir(path)` - List files and directories
- `read_file(path)` - Read file contents

## Project Structure

```
edenos_mcp_server/
├── server.py              # Main server entry point
├── core/
│   ├── __init__.py
│   └── logging.py         # Rich-based logging
├── mcp/
│   ├── __init__.py
│   ├── server.py          # MCP Server implementation
│   └── types.py           # Content types (TextContent, JsonContent)
├── tools/
│   ├── __init__.py        # Tool decorators and helpers
│   ├── agent_tools.py     # Agent-level tools
│   ├── chaos_tools.py     # CHAOS text processing
│   └── filesystem_tools.py # File operations
├── requirements.txt       # Python dependencies
├── pyproject.toml        # Project metadata
└── README.md            # This file
```

## Adding New Tools

1. Create a new Python file in the `tools/` directory
2. Import the `eden_tool` decorator and content types:
   ```python
   from . import eden_tool, TextContent, JsonContent
   ```
3. Decorate your functions with `@eden_tool()`:
   ```python
   @eden_tool()
   def my_tool(param: str):
       return [TextContent(type="text", text=f"Hello {param}")]
   ```
4. Restart the server - your tool will be automatically discovered!

## Development

The server is designed for development and testing. It includes:

- Stub MCP implementation for local testing
- Rich console output for debugging
- Error handling that prevents single tool failures from crashing the server
- Modular architecture for easy extension

## Dependencies

- `rich==13.4.2` - Beautiful console output
- `flask==2.3.3` - HTTP API support (for future features)

## License

EdenOS MCP Server - Dreamcatcher
