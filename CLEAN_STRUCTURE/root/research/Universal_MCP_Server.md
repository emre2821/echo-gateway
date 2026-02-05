#!/usr/bin/env node

/**
 * Universal Eden MCP Server (Revised)
 * Pure MCP stdio server by default, with optional HTTP/WS or forge modes.
 * Combines context management, CHAOS memory, permissions, auto-tools, and file watching.
 * Uses real MCP SDK for protocol compliance.
 */

const { Server, ErrorCode, McpError } = require('@modelcontextprotocol/sdk/server/index.js');
const { StdioServerTransport } = require('@modelcontextprotocol/sdk/server/stdio.js');
const { ListToolsRequestSchema, CallToolRequestSchema } = require('@modelcontextprotocol/sdk/types.js');
const express = require('express');
const { WebSocketServer } = require('ws');
const { v4: uuidv4 } = require('uuid');
const fs = require('fs-extra');
const path = require('path');
const chokidar = require('chokidar');
const inquirer = require('inquirer');
const Handlebars = require('handlebars');
const _ = require('lodash');

const mode = process.argv[2] || '--mcp'; // Default to MCP stdio
const STATE_FILE = path.join(process.cwd(), 'eden-universal-mcp.json');

let state = {
  contexts: {},
  chaos: { resonances: [], anchors: [], emotionalState: 'neutral', consentChains: [] },
  permissions: { granted: {}, requests: {}, audit: [] },
  tools: [], // For persistence, but runtime uses toolMap
  activeContext: null,
  lastUpdate: Date.now()
};

async function loadState() {
  if (await fs.pathExists(STATE_FILE)) {
    state = await fs.readJson(STATE_FILE);
  } else {
    await saveState();
  }
}

async function saveState() {
  state.lastUpdate = Date.now();
  await fs.writeJson(STATE_FILE, state, { spaces: 2 });
}

// Permissions System
const EXCLUSION_ZONES = ['/windows', '/program files']; // Expand as needed

function isExcluded(target) {
  const norm = path.normalize(target || '').toLowerCase();
  return EXCLUSION_ZONES.some(zone => norm.startsWith(zone.toLowerCase()));
}

function requestPermission(action, target, requester = 'agent') {
  if (isExcluded(target)) throw new McpError(ErrorCode.InvalidParams, 'Protected resource');
  const reqId = uuidv4();
  state.permissions.requests[reqId] = { action, target, requester, created: Date.now() };
  audit('request_created', { reqId, action, target, requester });
  saveState();
  return { content: [{ type: 'text', text: JSON.stringify({ reqId }) }] };
}

function grantPermission({ reqId, granter = 'user', duration = null }) {
  const req = state.permissions.requests[reqId];
  if (!req) throw new McpError(ErrorCode.InvalidParams, 'Request not found');
  const permId = uuidv4();
  const expires = duration ? Date.now() + duration * 1000 : null;
  state.permissions.granted[permId] = { ...req, granter, granted: Date.now(), expires, allowed: true };
  delete state.permissions.requests[reqId];
  audit('granted', { permId, reqId });
  saveState();
  return { content: [{ type: 'text', text: JSON.stringify({ permId }) }] };
}

// Add revokePermission, checkPermission similarly

function audit(event, details) {
  state.permissions.audit.push({ id: uuidv4(), event, details, ts: Date.now() });
}

// Tool System
const toolMap = new Map(); // name -> { name, description, inputSchema, handler, annotations }

function registerTool(toolDef) {
  toolMap.set(toolDef.name, toolDef);
}

// Auto-load from 'tools/' dir
async function loadTools() {
  const toolsDir = path.join(__dirname, 'tools');
  if (fs.existsSync(toolsDir)) {
    const files = await fs.readdir(toolsDir);
    for (const file of files) {
      if (file.endsWith('.js')) {
        const mod = require(path.join(toolsDir, file));
        Object.values(mod).forEach(def => {
          if (def && def.name && def.handler) {
            registerTool(def);
          }
        });
      }
    }
  }
}

// Example Tools (ported/adapted)
registerTool({
  name: 'list_dir',
  description: 'List directory contents',
  inputSchema: { type: 'object', properties: { path: { type: 'string' } }, required: ['path'] },
  annotations: { readOnlyHint: true },
  handler: async ({ path }) => {
    if (isExcluded(path)) throw new McpError(ErrorCode.InvalidParams, 'Protected');
    const contents = await fs.readdir(path);
    return { content: [{ type: 'text', text: JSON.stringify(contents) }] };
  }
});

// Context Tools (from bundles)
registerTool({
  name: 'create_context_window',
  description: 'Create a new context window',
  inputSchema: { type: 'object', properties: { name: { type: 'string' }, description: { type: 'string' }, symbols: { type: 'array', items: { type: 'string' } } }, required: ['name'] },
  handler: async (args) => {
    const id = uuidv4();
    state.contexts[id] = { ...args, id, content: [], created: Date.now(), lastModified: Date.now(), symbols: args.symbols || [] };
    state.activeContext = id;
    await saveState();
    return { content: [{ type: 'text', text: `Created window ${id}` }] };
  }
});

// Add more: add_context, query_context, merge_windows, add_resonance (for CHAOS), etc.

// File Watcher (background, for all modes)
function startWatcher() {
  chokidar.watch(path.join(process.cwd(), 'conversations', '*.json')).on('add', async (filePath) => {
    try {
      const data = await fs.readJson(filePath);
      // Extract and add to state.chaos.resonances/anchors (implement extractResonances, extractAnchors)
      // Example stub:
      state.chaos.resonances.push({ id: uuidv4(), content: JSON.stringify(data), type: 'conversation', timestamp: Date.now() });
      await saveState();
      // In HTTP mode, broadcast if wss exists
    } catch (err) {
      console.error('Watcher error:', err);
    }
  });
}

// Forge Mode (CLI tool generator)
async function runForgeMode() {
  console.log('Forge Mode: Interactive Tool Creator');
  // Use inquirer to collect tool info (name, desc, params, handler code, annotations)
  const answers = await inquirer.prompt([
    { type: 'input', name: 'name', message: 'Tool name (kebab-case)' },
    // Add more: description, parameters (loop), annotations, handler (editor)
  ]);
  // Validate/sanitize handler (from bundle (2))
  const handlerCode = answers.handler; // Assume collected
  const toolDef = {
    name: answers.name,
    description: answers.description,
    inputSchema: { /* build from params */ },
    handler: new Function('args', handlerCode), // Dangerous; sanitize in prod
    annotations: answers.annotations
  };
  // Save to tools dir as JS file
  const toolFile = path.join(__dirname, 'tools', `${answers.name}.js`);
  await fs.writeFile(toolFile, `module.exports = ${JSON.stringify(toolDef, null, 2)};`);
  console.log(`Tool ${answers.name} generated and saved. Restart server to load.`);
}

// HTTP/WebSocket Mode
function runHttpMode() {
  const app = express();
  app.use(express.json());
  const wss = new WebSocketServer({ port: 3002 });
  const clients = new Set();

  wss.on('connection', (ws) => {
    clients.add(ws);
    ws.on('close', () => clients.delete(ws));
  });

  function broadcastUpdate() {
    const update = JSON.stringify({ type: 'update', state });
    clients.forEach((client) => {
      if (client.readyState === client.OPEN) client.send(update);
    });
  }

  // Endpoints
  app.get('/list-tools', (req, res) => res.json({ tools: Array.from(toolMap.values()).map(t => ({ name: t.name, description: t.description, inputSchema: t.inputSchema })) }));
  app.post('/call-tool', async (req, res) => {
    const { name, params } = req.body;
    const tool = toolMap.get(name);
    if (!tool) return res.status(404).json({ error: 'Tool not found' });
    try {
      const result = await tool.handler(params);
      broadcastUpdate(); // If state changed
      res.json(result);
    } catch (err) {
      res.status(500).json({ error: err.message });
    }
  });
  // Add more: /permissions/request, /grant, /state, etc.

  app.listen(3001, () => console.log('HTTP API on 3001, WS on 3002'));
}

// Pure MCP Stdio Mode
async function runMcpMode() {
  const server = new Server(
    { name: 'universal-eden-mcp', version: '1.0.0' },
    { capabilities: { tools: {} } }
  );

  server.setRequestHandler(ListToolsRequestSchema, async () => ({
    tools: Array.from(toolMap.values()).map(t => ({
      name: t.name,
      description: t.description,
      inputSchema: t.inputSchema,
      // Add annotations if spec supports
    }))
  }));

  server.setRequestHandler(CallToolRequestSchema, async (request) => {
    const { name, arguments: args } = request.params;
    const tool = toolMap.get(name);
    if (!tool) throw new McpError(ErrorCode.MethodNotFound, `Unknown tool: ${name}`);
    // Validate args against inputSchema (use zod or similar in prod)
    // Check annotations for safety (e.g., if destructive, require permId in args and checkPermission)
    if (tool.annotations && tool.annotations.destructiveHint && !checkPermission('execute', name, args.permId)) {
      throw new McpError(ErrorCode.PermissionDenied, 'Permission required');
    }
    return await tool.handler(args);
  });

  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.log('MCP stdio server running');
}

// Main
async function main() {
  await loadState();
  await loadTools();
  startWatcher(); // Runs in background for all modes

  if (mode === '--forge') {
    await runForgeMode();
  } else if (mode === '--http') {
    runHttpMode();
  } else {
    await runMcpMode();
  }
}

main().catch(err => {
  console.error('Server error:', err);
  process.exit(1);
});
