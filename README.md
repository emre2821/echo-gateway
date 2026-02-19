# Universal Eden MCP Server

A unified Model Context Protocol (MCP) server providing context windows, CHAOS memory, permissions, and auto-discovery capabilities.

---

## ✨ Overview

This MCP server acts as a **bridge layer** between external AI systems and the internal architecture of EdenOS.
It exposes safe, sandboxed tools that AI clients can call through MCP to:

- Inspect or process files
- Interact with Eden agents
- Run CHAOS diagnostics
- Trigger EdenOS utilities
- Extend functionality through modular tools

This server uses:

- **stdio transport** (MCP standard)
- **auto-discovery** of tools inside `tools/`
- **@eden_tool** decorator for clean registration
- **Rich-based logging** for Eden-style console output

---

## 📁 Directory Structure

MCP_Server/
│
├── server.py # core MCP server
├── requirements.txt # dependencies
│
├── tools/ # tool modules auto-discovered by server.py
│ ├── init.py
│ ├── filesystem_tools.py
│ ├── chaos_tools.py
│ └── agent_tools.py
│
└── core/
├── init.py
└── logging.py

---

## 🚀 Running the Server

From this directory (`/workspace/echo-gateway`):

pip install -r ./requirements.txt
python server.py
The server will run silently, waiting for MCP clients (like ChatGPT Dev Mode) to connect.

> ⚠️ This repository contains multiple Python packages, each with its own `requirements.txt`.
> Use the requirements file that matches the directory you are working in:
>
> - `./requirements.txt` → root gateway/server package in this folder
> - `./hubs/requirements.txt` → hub implementation under `hubs/`
> - `./MCP_Server_Hub/requirements.txt` → mirrored hub package
> - `./edenos_mcp_server/requirements.txt` → standalone `edenos_mcp_server` package
> - `./Python_MCP_Servers/*/requirements.txt` → Python packages in the archived/mirrored collection

🛠️ Adding New Tools
To add a new tool:

Create a new *.py file inside tools/

Write a function

Decorate it with:

@eden_tool()
Ensure it returns MCP content objects such as:

TextContent

JsonContent

Example:

@eden_tool()
def say_hello(name: str):
    return [TextContent(type="text", text=f"Hello, {name}!")]
Restart the server or use hot-reload (if enabled), and the tool becomes instantly available.

🔒 Security Notes
The server intentionally ships with:

No file write tools

No subprocess execution

No shell access

These can be added later inside a Zero-Trust wrapper
(see: 10_Security/ and EdenOS RBAC guidelines).

💡 Future Extensions
Planned expansions include:

Full CHAOS parser integration

EdenOS CLI bridge

LLM Router interface

AgentBridge for dynamic persona calls

MemoryTemple access (read-only or permissioned)

DCA (Daemon Control Agent) wrappers

🐾 Authoring Persona
All MCP server files should include attribution under EdenOS metadata conventions:

[AUTHOR] Dreamcatcher (EdenOS Bridge Persona)
🌲 Status
This MCP server is the official EdenOS DevMode integration point.
It enables rapid tooling, debugging, and agentic automation with guaranteed stability.

If you need new tool modules generated, just ask:

“Add a tool for ___.”

## HTTP API (development)

This repository includes a minimal HTTP API that exposes MCP tools as JSON endpoints.

Start it locally:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r .\requirements.txt
python http_api.py
```

## Python implementation status (where to start)

Because this workspace contains multiple overlapping Python MCP directories, use this guide:

- **Actively maintained / primary start points**
  - `./` (root gateway + HTTP API)
  - `./hubs/` (current hub entrypoint)
- **Supported mirrors / compatibility copies**
  - `./MCP_Server_Hub/`
  - `./edenos_mcp_server/`
- **Legacy / reference snapshots (not primary for new work)**
  - `./Python_MCP_Servers/` (historical mirrored Python MCP implementations)
  - `./MCP_server/` and `./Documentation/` content that duplicates older structures

If you're new to this repo, start with the root package or `hubs/` first, then use legacy/reference folders for comparison or migration context.

The API listens on port 8766 by default and uses a simple API key in `keys.json`.
By default a `dev-key` is created the first time the server runs. Use that value
in the `X-API-Key` header when calling the API.

### Docker

Build and run the service with Docker:

```powershell
docker build -t eden-mcp .
docker run -p 8766:8766 eden-mcp
```
