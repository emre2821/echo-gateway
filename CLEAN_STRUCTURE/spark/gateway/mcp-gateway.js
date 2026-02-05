#!/usr/bin/env node

/**
 * MCP Gateway - Routes requests between multiple MCP servers
 * Universal Eden MCP Server acts as primary gateway
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
import fs from 'fs-extra';
import path from 'path';
import { fileURLToPath } from 'url';
import { spawn } from 'child_process';

dotenv.config();

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const CONFIG_FILE = path.join(__dirname, '..', 'config', 'mcp-gateway.json');

class MCPGateway {
  constructor() {
    this.config = null;
    this.servers = new Map();
    this.toolRegistry = new Map();
    this.permissionManager = new PermissionManager();
    this.sessionManager = new SessionManager();
  }

  async initialize() {
    await this.loadConfig();
    await this.initializeServers();
    this.setupToolRouting();
  }

  async loadConfig() {
    try {
      this.config = await fs.readJson(CONFIG_FILE);
      console.error('[GATEWAY] Configuration loaded:', this.config.gateway.name);
    } catch (error) {
      console.error('[GATEWAY] Failed to load config:', error);
      throw new Error('Gateway configuration required');
    }
  }

  async initializeServers() {
    for (const [serverId, serverConfig] of Object.entries(this.config.servers)) {
      if (!serverConfig.enabled) continue;

      console.error(`[GATEWAY] Initializing server: ${serverConfig.name}`);

      try {
        const server = await this.createServer(serverId, serverConfig);
        this.servers.set(serverId, server);
        console.error(`[GATEWAY] Server ${serverConfig.name} initialized successfully`);
      } catch (error) {
        console.error(`[GATEWAY] Failed to initialize ${serverConfig.name}:`, error);
      }
    }
  }

  async createServer(serverId, config) {
    const serverPath = path.resolve(__dirname, '..', config.path);

    switch (config.type) {
      case 'node':
        return await this.createNodeServer(serverId, config);
      case 'python':
        return await this.createPythonServer(serverId, config);
      default:
        throw new Error(`Unsupported server type: ${config.type}`);
    }
  }

  async createNodeServer(serverId, config) {
    const serverModule = await import(path.join(config.path, 'server.js'));
    return {
      id: serverId,
      name: config.name,
      type: config.type,
      process: null,
      module: serverModule,
      config
    };
  }

  async createPythonServer(serverId, config) {
    return {
      id: serverId,
      name: config.name,
      type: config.type,
      process: null,
      config,
      command: config.command,
      args: ['--stdio'],
      cwd: path.resolve(__dirname, '..', config.path)
    };
  }

  setupToolRouting() {
    // Register tools from all enabled servers
    for (const [serverId, server] of this.servers) {
      const tools = await this.getServerTools(serverId);
      tools.forEach(tool => {
        const toolKey = `${serverId}:${tool.name}`;
        this.toolRegistry.set(toolKey, {
          serverId,
          tool,
          server
        });
      });
    }
  }

  async getServerTools(serverId) {
    const server = this.servers.get(serverId);
    if (!server) return [];

    // For now, return a mock tool list - this would be expanded
    // to actually query each server for its tools
    const toolMapping = {
      'universal_eden': [
        { name: 'request_permission', description: 'Request permission for an action' },
        { name: 'file_read', description: 'Read file contents' },
        { name: 'file_write', description: 'Write to files' },
        { name: 'directory_list', description: 'List directory contents' }
      ],
      'windows_mcp': [
        { name: 'app_tool', description: 'Manages Windows applications' },
        { name: 'powershell_tool', description: 'Execute PowerShell commands' },
        { name: 'state_tool', description: 'Capture desktop state' },
        { name: 'click_tool', description: 'Click on UI elements' },
        { name: 'type_tool', description: 'Type text into input fields' }
      ],
      'filesystem_tools': [
        { name: 'file_meta', description: 'Get file metadata' },
        { name: 'archive_tools', description: 'Archive management' },
        { name: 'checksum_tool', description: 'Generate file checksums' }
      ]
    };

    return toolMapping[serverId] || [];
  }

  routeTool(toolName) {
    // Find which server should handle this tool
    for (const [category, serverIds] of Object.entries(this.config.routing.tool_mapping)) {
      if (serverIds.includes(toolName) || category.includes(toolName)) {
        // Return first available server in the fallback order
        for (const serverId of this.config.routing.fallback_order) {
          if (serverIds.includes(serverId) && this.servers.has(serverId)) {
            return this.servers.get(serverId);
          }
        }
      }
    }

    // Default to primary server
    return this.servers.get(this.config.routing.default_server);
  }

  async handleToolCall(request) {
    const { name, arguments: args } = request.params;

    // Check permissions
    const permissionResult = await this.permissionManager.checkPermission(name, args);
    if (!permissionResult.allowed) {
      throw new McpError(
        ErrorCode.PermissionDenied,
        `Permission denied: ${permissionResult.reason}`
      );
    }

    // Route to appropriate server
    const targetServer = this.routeTool(name);
    if (!targetServer) {
      throw new McpError(
        ErrorCode.MethodNotFound,
        `No server available for tool: ${name}`
      );
    }

    console.error(`[GATEWAY] Routing ${name} to ${targetServer.name}`);

    // Execute tool on target server
    return await this.executeToolOnServer(targetServer, name, args);
  }

  async executeToolOnServer(server, toolName, args) {
    if (server.type === 'node') {
      // For Node.js servers, we can call the tool directly
      const toolKey = `${server.id}:${toolName}`;
      const toolInfo = this.toolRegistry.get(toolKey);
      if (toolInfo && toolInfo.tool.handler) {
        return await toolInfo.tool.handler(args);
      }
    } else if (server.type === 'python') {
      // For Python servers, we need to spawn the process
      return await this.executePythonTool(server, toolName, args);
    }

    throw new McpError(
      ErrorCode.InternalError,
      `Cannot execute tool ${toolName} on server type ${server.type}`
    );
  }

  async executePythonTool(server, toolName, args) {
    return new Promise((resolve, reject) => {
      const child = spawn(server.command, server.args, {
        cwd: server.cwd,
        stdio: ['pipe', 'pipe', 'pipe']
      });

      const request = {
        jsonrpc: '2.0',
        id: Date.now(),
        method: 'tools/call',
        params: {
          name: toolName,
          arguments: args
        }
      };

      child.stdin.write(JSON.stringify(request) + '\n');

      let output = '';
      child.stdout.on('data', (data) => {
        output += data.toString();
      });

      child.stderr.on('data', (data) => {
        console.error(`[GATEWAY] Server error: ${data.toString()}`);
      });

      child.on('close', (code) => {
        if (code === 0) {
          try {
            const response = JSON.parse(output);
            resolve(response.result);
          } catch (error) {
            reject(new Error(`Invalid response from server: ${error.message}`));
          }
        } else {
          reject(new Error(`Server process exited with code ${code}`));
        }
      });
    });
  }

  async listTools() {
    const allTools = [];

    for (const [serverId, server] of this.servers) {
      const tools = await this.getServerTools(serverId);
      tools.push(...tools.map(tool => ({
        ...tool,
        serverId,
        serverName: server.name
      })));
    }

    return {
      tools: allTools
    };
  }
}

class PermissionManager {
  constructor() {
    this.levels = ['always_allow_all', 'allow_session', 'allow_action_session', 'decline'];
  }

  async checkPermission(toolName, args) {
    // Implement permission checking logic here
    // For now, allow all tools - this would be expanded based on config
    return {
      allowed: true,
      level: 'allow_action_session',
      expires: Date.now() + 300000 // 5 minutes
    };
  }
}

class SessionManager {
  constructor() {
    this.sessions = new Map();
  }

  createSession() {
    const sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    this.sessions.set(sessionId, {
      created: Date.now(),
      lastActivity: Date.now(),
      permissions: {}
    });
    return sessionId;
  }

  getSession(sessionId) {
    return this.sessions.get(sessionId);
  }

  cleanupExpiredSessions() {
    const now = Date.now();
    const expireTime = 3600000; // 1 hour

    for (const [sessionId, session] of this.sessions) {
      if (now - session.lastActivity > expireTime) {
        this.sessions.delete(sessionId);
      }
    }
  }
}

// Initialize and start the gateway server
async function main() {
  const gateway = new MCPGateway();
  await gateway.initialize();

  const server = new Server(
    {
      name: 'MCP Gateway',
      version: '1.0.0',
    },
    {
      capabilities: {
        tools: {},
      },
    }
  );

  // Handle list tools request
  server.setRequestHandler(ListToolsRequestSchema, async (request) => {
    const result = await gateway.listTools();
    return {
      tools: result.tools
    };
  });

  // Handle tool call request
  server.setRequestHandler(CallToolRequestSchema, async (request) => {
    return await gateway.handleToolCall(request);
  });

  const transport = new StdioServerTransport();
  await server.connect(transport);

  console.error('[GATEWAY] MCP Gateway started successfully');
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch(console.error);
}
