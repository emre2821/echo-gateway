# Universal Eden MCP Gateway

## Overview

The Universal Eden MCP Server now functions as the **primary gateway** for all MCP server implementations. This provides a unified interface for managing tools, permissions, and routing between different MCP servers.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                Universal Eden MCP Gateway              │
│                   (Primary Server)                   │
├─────────────────────────────────────────────────────────────┤
│  Tool Routing  │  Permission Management  │  Audit Trail    │
├─────────────────┼───────────────────────────┼─────────────────┤
│                │                        │                 │
│ ▼              │                        │                 │
│ ┌─────────────┐ │                        │                 │
│ │ Windows MCP   │ │                        │                 │
│ │ (Python)     │ │                        │                 │
│ └─────────────┘ │                        │                 │
│                │                        │                 │
│ ┌─────────────┐ │                        │                 │
│ │ Filesystem   │ │                        │                 │
│ │ Tools       │ │                        │                 │
│ └─────────────┘ │                        │                 │
└─────────────────┴─────────────────────────────────┴─────────────────┘
```

## Features

### ✅ Completed High Priority Tasks

1. **Permission System Overhaul** - Granular permission levels:
   - `always_allow_all` - Always allow all actions
   - `allow_session` - Allow all actions for this session
   - `allow_action_session` - Allow specific action for this session
   - `decline` - Deny the action

2. **Unified Configuration** - Single config file for all servers:
   - Server definitions and capabilities
   - Tool routing rules
   - Permission inheritance
   - Development settings

3. **Session Management** - Time-based permission expiration:
   - Session creation and tracking
   - Automatic cleanup of expired sessions
   - Activity monitoring

4. **Modular Tool System** - Easy tool/rule edits:
   - Dynamic tool registration
   - Server-agnostic tool definitions
   - Runtime tool discovery

5. **API Gateway** - Routes requests to appropriate servers:
   - Intelligent tool routing
   - Fallback server order
   - Cross-server communication

6. **Local Development** - Hot reload capabilities:
   - File watching for changes
   - Automatic server restart
   - Development mode debugging

7. **Audit System** - Comprehensive logging:
   - Permission request logging
   - Tool execution tracking
   - Security event monitoring

## Configuration

### Main Config: `config/mcp-gateway.json`

```json
{
  "gateway": {
    "name": "Universal Eden MCP Gateway",
    "primary": true,
    "mode": "stdio"
  },
  "servers": {
    "universal_eden": {
      "name": "Universal Eden MCP Server",
      "enabled": true,
      "type": "node"
    },
    "windows_mcp": {
      "name": "Windows MCP",
      "enabled": true,
      "type": "python"
    },
    "filesystem_tools": {
      "name": "Filesystem Tools",
      "enabled": true,
      "type": "python"
    }
  },
  "routing": {
    "tool_mapping": {
      "file_system": ["universal_eden", "filesystem_tools"],
      "desktop_automation": ["universal_eden", "windows_mcp"]
    }
  }
}
```

## Usage

### Start the Gateway Server

```bash
# Primary gateway server (routes to all MCP implementations)
npm run start-gateway

# Original server (standalone)
npm start

# HTTP API mode
npm run http
```

### Tool Categories

- **File System**: File operations, directory listing, metadata
- **Desktop Automation**: Application control, UI interaction, PowerShell
- **UI Interaction**: Click, type, scroll, drag operations
- **Process Management**: Task management, process control
- **Memory Management**: Context windows, CHAOS memory
- **Permissions**: Permission requests, audit logging

## Permission Levels

1. **Always Allow All** - No permission checks required
2. **Allow Session** - Grant permissions for entire session (1 hour)
3. **Allow Action Session** - Grant permission for specific action (5 minutes)
4. **Decline** - Explicitly deny the action

## Security Features

- **Audit Logging**: All permission requests and tool executions logged
- **Session Isolation**: Time-based session expiration
- **Tool Sandboxing**: Isolated execution environments
- **Permission Inheritance**: Child servers inherit parent permissions

## Development

### Hot Reload

The gateway automatically reloads when files change:
- Tool modifications in `/tools` directory
- Configuration changes in `/config`
- Server file updates

### Debug Mode

Enable detailed logging:
```bash
DEBUG=true npm run start-gateway
```

## Next Steps

### 🔄 In Progress

- **Tool Sandboxing** - Isolated execution environments
- **Cloud Deployment** - Remote server configuration
- **Testing Framework** - Comprehensive test suite
- **Documentation** - Complete usage guides
- **Performance Optimization** - Concurrent execution handling

### 📋 Remaining Tasks

1. Implement sandboxed tool execution
2. Create cloud deployment configurations
3. Build automated testing pipeline
4. Write comprehensive documentation
5. Optimize for production workloads

## File Structure

```
MCP_Server/
├── server-gateway.js          # New unified gateway server
├── config/
│   └── mcp-gateway.json   # Gateway configuration
├── gateway/
│   └── mcp-gateway.js    # Gateway routing logic
├── tools/                   # Universal Eden tools
├── logs/                     # Audit and debug logs
└── sessions.json              # Active sessions
```

The Universal Eden MCP Server is now the **primary gateway** that unifies all MCP server tools under a single, permission-managed interface.
