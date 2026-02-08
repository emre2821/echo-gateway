#!/usr/bin/env node

/**
 * Universal Eden MCP Server - Production Ready
 * Pure MCP stdio server with proper SDK integration
 * Features: Context windows, CHAOS memory, permissions, auto-discovery
 *
 * Modes:
 * - node server.js (default: MCP stdio)
 * - node server.js --http (HTTP API mode)
 * - node server.js --forge (Interactive tool creator)
 */

import dotenv from 'dotenv';
import { Server } from '@modelcontextprotocol/sdk/server';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ErrorCode,
  ListToolsRequestSchema,
  McpError,
} from '@modelcontextprotocol/sdk/types.js';
import express from 'express';
import { WebSocketServer } from 'ws';
import { v4 as uuidv4 } from 'uuid';
import fs from 'fs-extra';
import path from 'path';
import { fileURLToPath } from 'url';
import chokidar from 'chokidar';

// Load environment variables from .env file if it exists
dotenv.config();

// Fallback UUID generation if import fails
function generateId() {
  try {
    return uuidv4();
  } catch (error) {
    console.error('UUID generation failed, using fallback:', error.message);
    // Cryptographic fallback
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
      const r = Math.random() * 16 | 0;
      const v = c === 'x' ? r : (r & 0x3 | 0x8);
      return v.toString(16);
    });
  }
}

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const mode = process.argv[2] || '--mcp';
const STATE_FILE = path.join(process.cwd(), 'eden-universal-mcp.json');

// Configurable ports via environment variables
const HTTP_PORT = process.env.HTTP_PORT || 3001;
const WS_PORT = process.env.WS_PORT || 3002;
const HOST = process.env.HOST || 'localhost';

// State management with lock
let state = {
  contexts: {},
  chaos: {
    resonances: [],
    anchors: [],
    emotionalState: 'neutral',
    consentChains: []
  },
  permissions: {
    granted: {},
    requests: {},
    audit: []
  },
  activeContext: null,
  lastUpdate: Date.now()
};

let saveLock = false;

async function loadState() {
  try {
    console.error(`Loading state from: ${STATE_FILE}`);
    if (await fs.pathExists(STATE_FILE)) {
      state = await fs.readJson(STATE_FILE);
      console.error('State loaded from file');
    } else {
      console.error('State file not found, creating new state');
      await saveState();
    }
  } catch (error) {
    console.error('Failed to load state:', error);
    console.error('Error details:', {
      name: error.name,
      message: error.message,
      stack: error.stack
    });
    // Continue with default state
    state = {
      contexts: {},
      chaos: {
        resonances: [],
        anchors: [],
        emotionalState: 'neutral',
        consentChains: []
      },
      permissions: {
        granted: {},
        requests: {},
        audit: []
      },
      activeContext: null,
      lastUpdate: Date.now()
    };
  }
}

async function saveState() {
  // Simple lock to prevent concurrent writes
  while (saveLock) {
    await new Promise(resolve => setTimeout(resolve, 10));
  }
  saveLock = true;
  try {
    state.lastUpdate = Date.now();
    console.error(`Saving state to: ${STATE_FILE}`);
    await fs.writeJson(STATE_FILE, state, { spaces: 2 });
    console.error('State saved successfully');
  } catch (error) {
    console.error('Failed to save state:', error);
    console.error('Error details:', {
      name: error.name,
      message: error.message,
      stack: error.stack
    });
  } finally {
    saveLock = false;
  }
}

// Permissions System
const EXCLUSION_ZONES = [
  '/windows',
  '/program files',
  '/system32',
  'c:\\windows',
  'c:\\program files'
];

function isExcluded(target) {
  if (!target) return true;
  const norm = path.normalize(target).toLowerCase();
  return EXCLUSION_ZONES.some(zone =>
    norm.startsWith(zone.toLowerCase())
  );
}

function audit(event, details) {
  state.permissions.audit.push({
    id: generateId(),
    event,
    details,
    ts: Date.now()
  });
  // Trim audit log if too large
  if (state.permissions.audit.length > 1000) {
    state.permissions.audit = state.permissions.audit.slice(-500);
  }
}

function checkPermission(action, target, permId) {
  if (!permId) return false;
  const perm = state.permissions.granted[permId];
  if (!perm || !perm.allowed) return false;
  if (perm.action !== action) return false;
  if (perm.expires && perm.expires < Date.now()) return false;

  // Check if target matches (exact or prefix for directories)
  const permTarget = perm.target || '';
  if (target === permTarget) return true;
  if (target.startsWith(permTarget + path.sep)) return true;

  return false;
}

// Tool Registry
const toolMap = new Map();

function registerTool(toolDef) {
  if (!toolDef.name || !toolDef.handler) {
    throw new Error('Tool must have name and handler');
  }
  toolMap.set(toolDef.name, toolDef);
}

// Core Tools
registerTool({
  name: 'request_permission',
  description: 'Request permission for an action on a target resource',
  inputSchema: {
    type: 'object',
    properties: {
      action: { type: 'string', description: 'Action to perform' },
      target: { type: 'string', description: 'Target resource path' },
      requester: { type: 'string', description: 'Who is requesting', default: 'agent' }
    },
    required: ['action', 'target']
  },
  handler: async (args) => {
    const { action, target, requester = 'agent' } = args;

    if (isExcluded(target)) {
      throw new McpError(ErrorCode.InvalidParams, 'Protected resource');
    }

    const reqId = generateId();
    state.permissions.requests[reqId] = {
      action,
      target,
      requester,
      created: Date.now()
    };
    audit('request_created', { reqId, action, target, requester });
    await saveState();

    return {
      content: [{
        type: 'text',
        text: `Permission requested. Request ID: ${reqId}\nCall grant_permission with this ID to approve.`
      }]
    };
  }
});

registerTool({
  name: 'grant_permission',
  description: 'Grant a permission request',
  inputSchema: {
    type: 'object',
    properties: {
      reqId: { type: 'string', description: 'Request ID to grant' },
      granter: { type: 'string', description: 'Who is granting', default: 'user' },
      duration: { type: 'number', description: 'Duration in seconds (null = forever)' }
    },
    required: ['reqId']
  },
  handler: async (args) => {
    const { reqId, granter = 'user', duration = null } = args;

    const req = state.permissions.requests[reqId];
    if (!req) {
      throw new McpError(ErrorCode.InvalidParams, 'Request not found');
    }

    const permId = generateId();
    const expires = duration === null || duration === undefined
      ? null
      : Date.now() + duration * 1000;

    state.permissions.granted[permId] = {
      ...req,
      granter,
      granted: Date.now(),
      expires,
      allowed: true
    };

    delete state.permissions.requests[reqId];
    audit('granted', { permId, reqId, granter });
    await saveState();

    return {
      content: [{
        type: 'text',
        text: `Permission granted. Permission ID: ${permId}`
      }]
    };
  }
});

registerTool({
  name: 'revoke_permission',
  description: 'Revoke a granted permission',
  inputSchema: {
    type: 'object',
    properties: {
      permId: { type: 'string', description: 'Permission ID to revoke' }
    },
    required: ['permId']
  },
  handler: async (args) => {
    const { permId } = args;
    const perm = state.permissions.granted[permId];

    if (!perm) {
      throw new McpError(ErrorCode.InvalidParams, 'Permission not found');
    }

    perm.allowed = false;
    perm.revoked = Date.now();
    audit('revoked', { permId });
    await saveState();

    return {
      content: [{
        type: 'text',
        text: `Permission ${permId} revoked`
      }]
    };
  }
});

registerTool({
  name: 'list_permissions',
  description: 'List all granted permissions',
  inputSchema: {
    type: 'object',
    properties: {}
  },
  handler: async () => {
    return {
      content: [{
        type: 'text',
        text: JSON.stringify(state.permissions.granted, null, 2)
      }]
    };
  }
});

registerTool({
  name: 'list_dir',
  description: 'List directory contents',
  inputSchema: {
    type: 'object',
    properties: {
      path: { type: 'string', description: 'Directory path to list' }
    },
    required: ['path']
  },
  handler: async (args) => {
    const { path: dirPath } = args;

    if (isExcluded(dirPath)) {
      throw new McpError(ErrorCode.InvalidParams, 'Protected directory');
    }

    try {
      const contents = await fs.readdir(dirPath);
      return {
        content: [{
          type: 'text',
          text: JSON.stringify(contents, null, 2)
        }]
      };
    } catch (error) {
      throw new McpError(
        ErrorCode.InternalError,
        `Failed to read directory: ${error.message}`
      );
    }
  }
});

registerTool({
  name: 'read_file',
  description: 'Read file contents (requires permission)',
  inputSchema: {
    type: 'object',
    properties: {
      path: { type: 'string', description: 'File path to read' },
      permId: { type: 'string', description: 'Permission ID' }
    },
    required: ['path', 'permId']
  },
  handler: async (args) => {
    const { path: filePath, permId } = args;

    if (isExcluded(filePath)) {
      throw new McpError(ErrorCode.InvalidParams, 'Protected file');
    }

    if (!checkPermission('read_file', filePath, permId)) {
      throw new McpError(ErrorCode.InvalidParams, 'Permission denied');
    }

    try {
      const content = await fs.readFile(filePath, 'utf8');
      return {
        content: [{
          type: 'text',
          text: content
        }]
      };
    } catch (error) {
      throw new McpError(
        ErrorCode.InternalError,
        `Failed to read file: ${error.message}`
      );
    }
  }
});

// Context Window Tools
registerTool({
  name: 'create_context_window',
  description: 'Create a new context window with symbolic memory',
  inputSchema: {
    type: 'object',
    properties: {
      name: { type: 'string', description: 'Window name' },
      description: { type: 'string', description: 'Window description' },
      symbols: {
        type: 'array',
        items: { type: 'string' },
        description: 'Symbolic tags'
      }
    },
    required: ['name']
  },
  handler: async (args) => {
    const { name, description = '', symbols = [] } = args;
    const id = generateId();

    state.contexts[id] = {
      id,
      name,
      description,
      symbols,
      content: [],
      created: Date.now(),
      lastModified: Date.now()
    };

    state.activeContext = id;
    await saveState();

    return {
      content: [{
        type: 'text',
        text: `Created context window '${name}' with ID: ${id}`
      }]
    };
  }
});

registerTool({
  name: 'add_context',
  description: 'Add content to a context window',
  inputSchema: {
    type: 'object',
    properties: {
      windowId: { type: 'string', description: 'Window ID (optional, uses active)' },
      content: { type: 'string', description: 'Content to add' },
      type: {
        type: 'string',
        enum: ['memory', 'reasoning', 'symbol', 'metadata'],
        description: 'Content type'
      },
      symbols: {
        type: 'array',
        items: { type: 'string' },
        description: 'Symbolic tags'
      }
    },
    required: ['content', 'type']
  },
  handler: async (args) => {
    const { windowId, content, type, symbols = [] } = args;
    const targetId = windowId || state.activeContext;

    if (!targetId || !state.contexts[targetId]) {
      throw new McpError(ErrorCode.InvalidParams, 'Invalid window ID');
    }

    const entry = {
      id: generateId(),
      content,
      type,
      symbols,
      timestamp: Date.now()
    };

    state.contexts[targetId].content.push(entry);
    state.contexts[targetId].lastModified = Date.now();
    await saveState();

    return {
      content: [{
        type: 'text',
        text: `Added ${type} content to window ${targetId}`
      }]
    };
  }
});

registerTool({
  name: 'list_contexts',
  description: 'List all context windows',
  inputSchema: {
    type: 'object',
    properties: {}
  },
  handler: async () => {
    const windows = Object.values(state.contexts).map(w => ({
      id: w.id,
      name: w.name,
      description: w.description,
      symbols: w.symbols,
      contentCount: w.content.length,
      isActive: w.id === state.activeContext
    }));

    return {
      content: [{
        type: 'text',
        text: JSON.stringify(windows, null, 2)
      }]
    };
  }
});

// CHAOS Memory Tools
registerTool({
  name: 'add_resonance',
  description: 'Add emotional resonance to CHAOS memory',
  inputSchema: {
    type: 'object',
    properties: {
      content: { type: 'string', description: 'Resonance content' },
      emotionalWeight: { type: 'number', description: 'Emotional intensity (0-1)' },
      type: { type: 'string', description: 'Resonance type' }
    },
    required: ['content']
  },
  handler: async (args) => {
    const { content, emotionalWeight = 0.5, type = 'general' } = args;

    const resonance = {
      id: generateId(),
      content,
      emotionalWeight,
      type,
      timestamp: Date.now()
    };

    state.chaos.resonances.push(resonance);
    await saveState();

    return {
      content: [{
        type: 'text',
        text: `Added resonance: ${resonance.id}`
      }]
    };
  }
});

// File Watcher (background process)
function startWatcher() {
  const conversationsPath = path.join(process.cwd(), 'conversations');

  if (!fs.existsSync(conversationsPath)) {
    return; // No conversations directory
  }

  chokidar.watch(path.join(conversationsPath, '*.json'))
    .on('add', async (filePath) => {
      try {
        const data = await fs.readJson(filePath);

        // Extract resonances from conversation
        if (data.messages) {
          for (const msg of data.messages) {
            if (msg.emotionalWeight) {
              state.chaos.resonances.push({
                id: generateId(),
                content: msg.content,
                emotionalWeight: msg.emotionalWeight,
                type: 'conversation',
                timestamp: Date.now(),
                source: path.basename(filePath)
              });
            }
          }
          await saveState();
        }
      } catch (error) {
        console.error('Watcher error:', error);
      }
    });
}

// Auto-load tools from tools directory
async function loadExternalTools() {
  const toolsDir = path.join(__dirname, 'tools');

  if (!fs.existsSync(toolsDir)) {
    return;
  }

  try {
    const files = await fs.readdir(toolsDir);

    for (const file of files) {
      if (file.endsWith('.js')) {
        try {
          const toolPath = path.join(toolsDir, file);
          const mod = await import(`file://${toolPath}`);

          if (mod.default) {
            registerTool(mod.default);
          }
        } catch (error) {
          console.error(`Failed to load tool ${file}:`, error.message);
        }
      }
    }
  } catch (error) {
    console.error('Failed to load external tools:', error);
  }
}

// MCP Stdio Mode (default)
async function runMcpMode() {
  const server = new Server(
    {
      name: 'universal-eden-mcp',
      version: '1.0.0',
    },
    {
      protocolVersion: '2025-06-18',
      capabilities: {
        tools: {},
      },
    }
  );

  server.setRequestHandler(ListToolsRequestSchema, async () => ({
    tools: Array.from(toolMap.values()).map(t => ({
      name: t.name,
      description: t.description,
      inputSchema: t.inputSchema,
    }))
  }));

  server.setRequestHandler(CallToolRequestSchema, async (request) => {
    const { name, arguments: args } = request.params;
    console.error(`Tool called: ${name} with args:`, args);

    const tool = toolMap.get(name);

    if (!tool) {
      console.error(`Tool not found: ${name}`);
      throw new McpError(
        ErrorCode.MethodNotFound,
        `Unknown tool: ${name}`
      );
    }

    try {
      const result = await tool.handler(args || {});
      console.error(`Tool ${name} executed successfully`);
      return result;
    } catch (error) {
      console.error(`Tool ${name} failed:`, error);
      console.error('Error details:', {
        name: error.name,
        message: error.message,
        stack: error.stack
      });
      if (error instanceof McpError) {
        throw error;
      }
      throw new McpError(
        ErrorCode.InternalError,
        `Tool execution failed: ${error.message}`
      );
    }
  });

  const transport = new StdioServerTransport();
  await server.connect(transport);

  console.error('Universal Eden MCP server running on stdio');
}

// HTTP API Mode with SSE support for ChatGPT
function runHttpMode() {
  const app = express();
  app.use(express.json());

  const wss = new WebSocketServer({ port: WS_PORT });
  const clients = new Set();

  wss.on('connection', (ws) => {
    clients.add(ws);
    ws.on('close', () => clients.delete(ws));
    ws.send(JSON.stringify({ type: 'connected', state }));
  });

  function broadcast(data) {
    const message = JSON.stringify(data);
    clients.forEach(client => {
      if (client.readyState === 1) {
        client.send(message);
      }
    });
  }

  // SSE endpoint for ChatGPT compatibility
  app.get('/sse', (req, res) => {
    res.writeHead(200, {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive',
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Headers': 'Cache-Control'
    });

    // Send initial connection event
    res.write(`data: ${JSON.stringify({ type: 'connected', state })}\n\n`);

    // Keep connection alive
    const heartbeat = setInterval(() => {
      res.write(`data: ${JSON.stringify({ type: 'heartbeat', timestamp: Date.now() })}\n\n`);
    }, 30000);

    // Clean up on disconnect
    req.on('close', () => {
      clearInterval(heartbeat);
    });
  });

  app.get('/api/tools', (req, res) => {
    const tools = Array.from(toolMap.values()).map(t => ({
      name: t.name,
      description: t.description,
      inputSchema: t.inputSchema
    }));
    res.json({ tools });
  });

  app.post('/api/tools/:name', async (req, res) => {
    const { name } = req.params;
    const args = req.body;

    const tool = toolMap.get(name);
    if (!tool) {
      return res.status(404).json({ error: 'Tool not found' });
    }

    try {
      const result = await tool.handler(args);
      broadcast({ type: 'tool_executed', tool: name, result });
      res.json(result);
    } catch (error) {
      res.status(500).json({ error: error.message });
    }
  });

  app.get('/api/state', (req, res) => {
    res.json(state);
  });

  // MCP protocol endpoint with SSE headers
  app.post('/mcp', (req, res) => {
    res.writeHead(200, {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive',
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Headers': 'Content-Type, Cache-Control',
      'Access-Control-Allow-Methods': 'GET, POST, OPTIONS'
    });

    // Handle MCP request and stream response
    const handleMcpRequest = async () => {
      try {
        // Handle empty or malformed requests
        if (!req.body || typeof req.body !== 'object') {
          res.write(`data: ${JSON.stringify({ error: { code: -32700, message: 'Parse error' } })}\n\n`);
          res.write('data: [DONE]\n\n');
          res.end();
          return;
        }

        const { method, params, id } = req.body;

        if (method === 'tools/list') {
          const tools = Array.from(toolMap.values()).map(t => ({
            name: t.name,
            description: t.description,
            inputSchema: t.inputSchema
          }));
          res.write(`data: ${JSON.stringify({ result: { tools }, id })}\n\n`);
        } else if (method === 'tools/call') {
          const { name, arguments: args } = params || {};
          const tool = toolMap.get(name);

          if (!tool) {
            res.write(`data: ${JSON.stringify({ error: { code: -32601, message: 'Tool not found' }, id })}\n\n`);
          } else {
            try {
              const result = await tool.handler(args || {});
              res.write(`data: ${JSON.stringify({ result, id })}\n\n`);
            } catch (error) {
              res.write(`data: ${JSON.stringify({ error: { code: -32603, message: error.message }, id })}\n\n`);
            }
          }
        } else if (method === 'initialize') {
          // Handle MCP initialization
          res.write(`data: ${JSON.stringify({
            result: {
              protocolVersion: "2025-06-18",
              capabilities: {
                tools: {},
                logging: {}
              },
              serverInfo: {
                name: "universal-eden-mcp",
                version: "1.0.0"
              }
            },
            id
          })}\n\n`);
        } else {
          res.write(`data: ${JSON.stringify({ error: { code: -32601, message: 'Method not found' }, id })}\n\n`);
        }
      } catch (error) {
        res.write(`data: ${JSON.stringify({ error: { code: -32603, message: 'Internal error' }, id: req.body?.id })}\n\n`);
      }

      res.write('data: [DONE]\n\n');
      res.end();
    };

    handleMcpRequest();
  });

  // Add OPTIONS handler for CORS preflight
  app.options('/mcp', (req, res) => {
    res.writeHead(200, {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Headers': 'Content-Type, Cache-Control',
      'Access-Control-Allow-Methods': 'GET, POST, OPTIONS'
    });
    res.end();
  });

  app.listen(HTTP_PORT, HOST, () => {
    console.log(`HTTP API: http://${HOST}:${HTTP_PORT}`);
    console.log(`WebSocket: ws://${HOST}:${WS_PORT}`);
    console.log(`SSE Endpoint: http://${HOST}:${HTTP_PORT}/sse`);
    console.log(`MCP Endpoint: http://${HOST}:${HTTP_PORT}/mcp`);
  });
}

// Main
async function main() {
  try {
    console.error('Starting Universal Eden MCP Server...');
    await loadState();
    console.error('State loaded successfully');

    await loadExternalTools();
    console.error(`Loaded ${toolMap.size} tools`);

    startWatcher();
    console.error('File watcher started');

    if (mode === '--http') {
      console.error('Starting HTTP mode...');
      runHttpMode();
    } else if (mode === '--forge') {
      console.log('Forge mode not yet implemented');
      console.log('Create tools manually in ./tools/ directory');
      process.exit(0);
    } else {
      console.error('Starting MCP stdio mode...');
      await runMcpMode();
    }
  } catch (error) {
    console.error('Fatal error during startup:', error);
    console.error('Stack trace:', error.stack);
    process.exit(1);
  }
}

main().catch(error => {
  console.error('Fatal error:', error);
  process.exit(1);
});
