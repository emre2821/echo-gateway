# echo-gateway

`echo-gateway` is a mixed Node.js + Python workspace for experimenting with MCP (Model Context Protocol) servers and a ChatGPT Apps SDK-style Next.js UI.

This repository currently contains **multiple parallel implementations** (some duplicated under different folders) rather than a single clean package. This README reflects the repository as it exists today.

## What is in this repo right now

### 1) Root Next.js app scaffold (`/`)
The repo root has a Next.js project (`package.json`, `next.config.ts`, `middleware.ts`, `app/`, `public/`) plus a stdio MCP script at `scripts/mcp-stdio.js`.

- `npm run dev|build|start|lint|format` are defined in the root `package.json`.
- `baseUrl.ts` sets `BASE_URL`/`VERCEL_URL` logic.
- `middleware.ts` adds permissive CORS headers.
- `scripts/mcp-stdio.js` starts a stdio MCP server named `echo-gateway`.

> Note: the root app directory is incomplete for a standard App Router run (for example, no `app/layout.tsx` in root), and there is a fuller Next.js implementation under `NextJS_Application/`.

### 2) Fuller Next.js ChatGPT App implementation (`NextJS_Application/`)
This directory includes a complete App Router structure with:

- `app/layout.tsx` with `NextChatSDKBootstrap`
- `app/mcp/route.ts` using `mcp-handler`
- `app/page.tsx` and `app/custom-page/page.tsx`

If you are working on the ChatGPT Apps SDK web UI + MCP route pattern, this is currently the most complete Next.js implementation in the repository.

### 3) Python MCP servers
There are several Python MCP codebases, including:

- `edenos_mcp_server/`
- `hubs/` (including `hubs/mcp_server_hub.py`)
- `MCP_Server_Hub/`
- `Python_MCP_Servers/`

These provide MCP server/hub functionality, tool loading, and permission/audit-oriented workflows with overlapping scope.

## Top-level structure (high signal folders)

- `app/` – root Next.js app pages/components (partial)
- `NextJS_Application/` – fuller Next.js ChatGPT Apps SDK app
- `scripts/` – utility scripts, including stdio MCP launcher
- `edenos_mcp_server/` – standalone Python MCP server package
- `hubs/` and `MCP_Server_Hub/` – Python MCP hub implementations
- `Python_MCP_Servers/` – additional Python MCP server variants
- `Documentation/`, `CLEAN_STRUCTURE/`, `lore/` – docs/planning/reference content

## Quick start

### Root Node workspace
```bash
npm install
npm run dev
```

### Root stdio MCP server
```bash
node scripts/mcp-stdio.js
```

### Python dependencies (root)
```bash
python -m venv .venv
source .venv/bin/activate   # Windows PowerShell: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Python hub example
```bash
cd hubs
pip install -r requirements.txt
python mcp_server_hub.py stdio
```

## Repository status

This repo appears to be an active consolidation workspace:

- multiple MCP server variants coexist,
- duplicated docs/readmes exist in different subtrees,
- not every top-level project is fully wired together.

For new work, it is usually best to choose one target implementation first (for example `NextJS_Application/` for Apps SDK UI work, or `edenos_mcp_server/`/`hubs/` for Python MCP backends) and treat other directories as reference/legacy unless needed.

## Changelog

See `CHANGELOG.md` for historical notes.
