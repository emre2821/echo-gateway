#!/usr/bin/env node

/**
 * Unified MCP Server with Gateway Integration
 * Primary server that routes to other MCP implementations
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
const CONFIG_FILE = path.join(__dirname, 'config', 'mcp-gateway.json');

class UnifiedMCPServer {
  constructor() {
    this.config = null;
    this.servers = new Map();
    this.permissionManager = new PermissionManager();
    this.sessionManager = new SessionManager();
    this.auditLogger = new AuditLogger();
  }

  async initialize() {
    await this.loadConfig();
    await this.initializeServers();
    await this.setupToolRegistry();
  }

  async loadConfig() {
    try {
      this.config = await fs.readJson(CONFIG_FILE);
      console.error('[UNIFIED MCP] Configuration loaded:', this.config.gateway.name);
    } catch (error) {
      console.error('[UNIFIED MCP] Failed to load config:', error);
      throw new Error('Gateway configuration required');
    }
  }

  async initializeServers() {
    for (const [serverId, serverConfig] of Object.entries(this.config.servers)) {
      if (!serverConfig.enabled) continue;

      console.error(`[UNIFIED MCP] Initializing server: ${serverConfig.name}`);

      try {
        const server = await this.createServer(serverId, serverConfig);
        this.servers.set(serverId, server);
        console.error(`[UNIFIED MCP] Server ${serverConfig.name} initialized successfully`);
      } catch (error) {
        console.error(`[UNIFIED MCP] Failed to initialize ${serverConfig.name}:`, error);
      }
    }
  }

  async createServer(serverId, config) {
    const serverPath = path.resolve(__dirname, config.path);

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
    if (serverId === 'universal_eden') {
      // Load the main server module
      const serverModule = await import(path.join(config.path, 'server.js'));
      return {
        id: serverId,
        name: config.name,
        type: config.type,
        process: null,
        module: serverModule,
        config,
        tools: await this.loadUniversalEdenTools()
      };
    }

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
      cwd: path.resolve(__dirname, config.path)
    };
  }

  async loadUniversalEdenTools() {
    // Load tools from the tools directory
    const toolsDir = path.join(__dirname, 'tools');
    const tools = [];

    try {
      const toolFiles = await fs.readdir(toolsDir);
      for (const file of toolFiles) {
        if (file.endsWith('.py') && file !== '__init__.py') {
          try {
            const toolModule = await import(path.join(toolsDir, file));
            // Extract tool functions from the module
            for (const [funcName, func] of Object.entries(toolModule)) {
              if (typeof func === 'function' && hasattr(func, '_mcp_tool')) {
                const metadata = func._eden_metadata;
                tools.push({
                  name: metadata.name,
                  description: metadata.doc,
                  inputSchema: this.generateInputSchema(func),
                  handler: func
                });
              }
            }
          } catch (error) {
            console.error(`[UNIFIED MCP] Failed to load tool ${file}:`, error);
          }
        }
      }
    } catch (error) {
      console.error('[UNIFIED MCP] Failed to load tools directory:', error);
    }

    return tools;
  }

  generateInputSchema(func) {
    // Generate a basic input schema from function signature
    const signature = func._eden_metadata?.signature || '';
    return {
      type: 'object',
      properties: {
        // This would be expanded to parse actual parameters
      }
    };
  }

  async setupToolRegistry() {
    this.toolRegistry = new Map();

    // Register tools from all servers
    for (const [serverId, server] of this.servers) {
      if (server.tools) {
        server.tools.forEach(tool => {
          const toolKey = `${serverId}:${tool.name}`;
          this.toolRegistry.set(toolKey, {
            serverId,
            tool,
            server
          });
        });
      }
    }
  }

  routeTool(toolName, args) {
    // Check tool mapping in routing config
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
    const { name: toolName, arguments: args } = request.params;

    // Log the request
    await this.auditLogger.log({
      event: 'tool_call_requested',
      tool: toolName,
      args,
      timestamp: Date.now()
    });

    // Check permissions
    const permissionResult = await this.permissionManager.checkPermission(toolName, args);
    if (!permissionResult.allowed) {
      await this.auditLogger.log({
        event: 'permission_denied',
        tool: toolName,
        reason: permissionResult.reason,
        timestamp: Date.now()
      });

      throw new McpError(
        ErrorCode.PermissionDenied,
        `Permission denied: ${permissionResult.reason}`
      );
    }

    // Route to appropriate server
    const targetServer = this.routeTool(toolName, args);
    if (!targetServer) {
      throw new McpError(
        ErrorCode.MethodNotFound,
        `No server available for tool: ${toolName}`
      );
    }

    console.error(`[UNIFIED MCP] Routing ${toolName} to ${targetServer.name}`);

    try {
      // Execute tool on target server
      const result = await this.executeToolOnServer(targetServer, toolName, args);

      await this.auditLogger.log({
        event: 'tool_call_completed',
        tool: toolName,
        server: targetServer.id,
        result: 'success',
        timestamp: Date.now()
      });

      return { result };
    } catch (error) {
      await this.auditLogger.log({
        event: 'tool_call_failed',
        tool: toolName,
        server: targetServer.id,
        error: error.message,
        timestamp: Date.now()
      });

      throw error;
    }
  }

  async executeToolOnServer(server, toolName, args) {
    if (server.type === 'node' && server.id === 'universal_eden') {
      // Direct execution for Universal Eden tools
      const toolKey = `${server.id}:${toolName}`;
      const toolInfo = this.toolRegistry.get(toolKey);
      if (toolInfo && toolInfo.tool.handler) {
        return await toolInfo.tool.handler(args);
      }
    } else if (server.type === 'python') {
      // Execute Python server tools via subprocess
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
        console.error(`[UNIFIED MCP] Server error: ${data.toString()}`);
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
      if (server.tools) {
        server.tools.forEach(tool => {
          allTools.push({
            name: tool.name,
            description: tool.description,
            inputSchema: tool.inputSchema,
            serverId,
            serverName: server.name
          });
        });
      }
    }

    return allTools;
  }
}

class PermissionManager {
  constructor(config) {
    this.levels = ['always_allow_all', 'allow_session', 'allow_action_session', 'decline'];
    this.config = config;
  }

  async checkPermission(toolName, args) {
    // Implement granular permission checking
    const sessionId = args.session_id || 'default';

    // Check for always allow all
    if (this.hasPermission('always_allow_all', sessionId)) {
      return {
        allowed: true,
        level: 'always_allow_all',
        expires: null
      };
    }

    // Check for session-based permissions
    if (this.hasPermission('allow_session', sessionId)) {
      return {
        allowed: true,
        level: 'allow_session',
        expires: Date.now() + 3600000 // 1 hour
      };
    }

    // Check for action-specific permissions
    const actionKey = `action:${toolName}`;
    if (this.hasPermission('allow_action_session', sessionId) && this.hasPermission(actionKey, sessionId)) {
      return {
        allowed: true,
        level: 'allow_action_session',
        expires: Date.now() + 300000 // 5 minutes
      };
    }

    // Default to decline
    return {
      allowed: false,
      level: 'decline',
      reason: 'No permission granted for this action',
      expires: null
    };
  }

  hasPermission(level, sessionId) {
    // This would be expanded to check actual permission storage
    return level === 'allow_action_session'; // Temporary implementation
  }
}

class SessionManager {
  constructor() {
    this.sessions = new Map();
  }

  createSession(options = {}) {
    const sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    this.sessions.set(sessionId, {
      created: Date.now(),
      lastActivity: Date.now(),
      permissions: options.permissions || {},
      expires: Date.now() + (options.duration || 3600000)
    });
    return sessionId;
  }

  getSession(sessionId) {
    const session = this.sessions.get(sessionId);
    if (!session) return null;

    // Check if session expired
    if (Date.now() > session.expires) {
      this.sessions.delete(sessionId);
      return null;
    }

    // Update last activity
    session.lastActivity = Date.now();
    return session;
  }

  cleanupExpiredSessions() {
    const now = Date.now();

    for (const [sessionId, session] of this.sessions) {
      if (now > session.expires) {
        this.sessions.delete(sessionId);
      }
    }
  }
}

class AuditLogger {
  constructor() {
    this.logFile = path.join(__dirname, 'logs', 'audit.log');
    this.maxEntries = 1000;
  }

  async log(entry) {
    try {
      await fs.ensureDir(path.dirname(this.logFile));
      const logEntry = {
        ...entry,
        id: this.generateId(),
        timestamp: new Date().toISOString()
      };

      const logLine = JSON.stringify(logEntry) + '\n';
      await fs.appendFile(this.logFile, logLine);

      // Trim log if too large
      await this.trimLog();
    } catch (error) {
      console.error('[UNIFIED MCP] Failed to write audit log:', error);
    }
  }

  async trimLog() {
    try {
      const content = await fs.readFile(this.logFile, 'utf8');
      const lines = content.split('\n').filter(line => line.trim());

      if (lines.length > this.maxEntries) {
        const trimmed = lines.slice(-this.maxEntries);
        await fs.writeFile(this.logFile, trimmed.join('\n'));
      }
    } catch (error) {
      // Ignore trim errors
    }
  }

  generateId() {
    return Date.now().toString(36) + Math.random().toString(36).substr(2, 9);
  }
}

// Initialize and start the unified server
async function main() {
  const server = new UnifiedMCPServer();
  await server.initialize();

  const mcpServer = new Server(
    {
      name: 'Universal Eden MCP Gateway',
      version: '1.0.0',
    },
    {
      capabilities: {
        tools: {},
      },
    }
  );

  // Handle list tools request
  mcpServer.setRequestHandler(ListToolsRequestSchema, async (request) => {
    const tools = await server.listTools();
    return {
      tools
    };
  });

  // Handle tool call request
  mcpServer.setRequestHandler(CallToolRequestSchema, async (request) => {
    return await server.handleToolCall(request);
  });

  const transport = new StdioServerTransport();
  await mcpServer.connect(transport);

  console.error('[UNIFIED MCP] Universal MCP Gateway started successfully');
  console.error('[UNIFIED MCP] Primary server for all MCP tools');
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch(console.error);
}
