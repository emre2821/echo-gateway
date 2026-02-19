# EdenOS MCP Server Hub

**Unified MCP Server aggregating tools from multiple Eden ecosystem servers.**

This MCP server combines tools from:

- **Eden Context Window MCP**: Context management with symbolic memory
- **CHAOS MCP Server**: CHAOS file processing and analysis
- **EdenOS MCP Server**: Filesystem operations with permissions
- **Additional utility tools**: Checksums, git operations, archiving

## Installation

```bash
# from /workspace/echo-gateway/hubs
pip install -r ./requirements.txt
```

> ⚠️ In this mixed workspace, install from `hubs/requirements.txt` for the hub.
> Do not use the root `requirements.txt` unless you are setting up the root gateway package.

## Usage

### STDIO Transport (for MCP clients like Claude Desktop)

```bash
python mcp_server_hub.py stdio
```

### SSE Transport (for web clients)

```bash
python mcp_server_hub.py sse
```

The SSE server runs on port 3002 by default (configurable via PORT environment variable).

## Available Tools

### Context Window Management
- `create_context_window`: Create new context windows with symbolic tags
- `add_context`: Add context information to windows
- `query_context`: Query context with symbolic reasoning
- `list_windows`: List all context windows
- `set_active_window`: Set active context window
- `merge_windows`: Merge multiple context windows

### CHAOS File Processing
- `list_chaos_files`: List CHAOS files
- `get_chaos_file`: Retrieve CHAOS file content
- `create_chaos_file`: Create new CHAOS files
- `update_chaos_file`: Update existing CHAOS files
- `delete_chaos_file`: Delete CHAOS files
- `analyze_chaos_file`: Analyze CHAOS file structure and emotions
- `create_emotion_tag`: Generate emotion tags
- `create_symbol_tag`: Generate symbol tags
- `create_relationship_tag`: Generate relationship tags
- `generate_chaos_template`: Create CHAOS file templates
- `search_chaos_files`: Search through CHAOS files
- `generate_random_chaos_file`: Generate random CHAOS files for testing

### Media File Management
- `list_media_files`: List available media files
- `get_media_file_info`: Get media file information
- `create_media_reference_tag`: Create media reference tags

### Filesystem Operations (with Permissions)
- `list_dir`: List directory contents
- `read_file`: Read file contents
- `request_permission`: Request permission for file operations
- `grant_permission`: Grant permissions
- `revoke_permission`: Revoke permissions
- `execute_read`: Execute read with permission
- `create_file`: Request file creation permission
- `execute_create`: Create file with permission
- `move_file`: Request file move permission
- `execute_move`: Move file with permission
- `rename_file`: Request file rename permission
- `execute_rename`: Rename file with permission
- `map_directory`: Map directory structure
- `find_files`: Find files by keyword
- `list_permissions`: List all permissions
- `list_requests`: List permission requests
- `list_audit`: View audit log

### Permission and Agent Management
- `list_allowed_paths`: List all allowed paths
- `add_allowed_path`: Add a path to allowed_paths (with read_only option)
- `remove_allowed_path`: Remove a path from allowed_paths
- `set_agent_trust_level`: Set trust level for an agent (trusted/restricted/blocked)
- `get_agent_trust_level`: Get trust level for an agent
- `list_agents`: List all agents and their trust levels

## Data Storage

The server stores data in the following files:
- `context-window.json`: Context window data
- `permissions.json`: Permission system data
- `chaos_files/`: Directory for CHAOS files
- `media_files/`: Directory for media files

## Security

- File operations are restricted from protected system directories
- Permission system requires explicit approval for sensitive operations
- All operations are audited

## Author

Cascade AI Assistant (EdenOS Bridge Persona)


## Workspace directory status

To reduce confusion across overlapping Python MCP folders:

- **Actively maintained**: `hubs/` (primary hub entrypoint) and repository root (`/workspace/echo-gateway`).
- **Compatibility mirrors**: `MCP_Server_Hub/`, `edenos_mcp_server/`.
- **Legacy/reference**: `Python_MCP_Servers/` snapshots and older duplicated docs/structures.
