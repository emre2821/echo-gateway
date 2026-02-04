#!/usr/bin/env node

/**
 * Eden Context Window MCP Bundle
 * Advanced context window management for Eden ecosystem with persistent memory and symbolic reasoning
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ErrorCode,
  ListToolsRequestSchema,
  McpError,
} from '@modelcontextprotocol/sdk/types.js';
import fs from 'fs-extra';
import path from 'path';
import { v4 as uuidv4 } from 'uuid';
import _ from 'lodash';

const CONTEXT_FILE = path.join(process.cwd(), 'context-window.json');

class EdenContextWindowServer {
  constructor() {
    this.server = new Server(
      {
        name: 'eden-context-window-mcp',
        version: '1.0.0',
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    this.setupToolHandlers();
    this.loadContext();
  }

  async loadContext() {
    try {
      if (await fs.pathExists(CONTEXT_FILE)) {
        this.context = await fs.readJson(CONTEXT_FILE);
      } else {
        this.context = {
          windows: {},
          activeWindow: null,
          metadata: {
            created: new Date().toISOString(),
            lastModified: new Date().toISOString()
          }
        };
        await this.saveContext();
      }
    } catch (error) {
      console.error('Failed to load context:', error);
      this.context = { windows: {}, activeWindow: null };
    }
  }

  async saveContext() {
    try {
      this.context.metadata.lastModified = new Date().toISOString();
      await fs.writeJson(CONTEXT_FILE, this.context, { spaces: 2 });
    } catch (error) {
      console.error('Failed to save context:', error);
    }
  }

  setupToolHandlers() {
    this.server.setRequestHandler(ListToolsRequestSchema, async () =>({
      tools: [
        {
          name: 'create_context_window',
          description: 'Create a new context window with symbolic memory capabilities',
          inputSchema: {
            type: 'object',
            properties: {
              name: {
                type: 'string',
                description: 'Name of context window'
              },
              description: {
                type: 'string',
                description: 'Description of context window purpose'
              },
              symbols: {
                type: 'array',
                items: { type: 'string' },
                description: 'Symbolic tags for this context'
              }
            },
            required: ['name']
          }
        },
        {
          name: 'add_context',
          description: 'Add context information to active window',
          inputSchema: {
            type: 'object',
            properties: {
              windowId: {
                type: 'string',
                description: 'ID of context window (optional, uses active if not provided)'
              },
              content: {
                type: 'string',
                description: 'Context content to add'
              },
              type: {
                type: 'string',
                enum: ['memory', 'reasoning', 'symbol', 'metadata'],
                description: 'Type of context content'
              },
              symbols: {
                type: 'array',
                items: { type: 'string' },
                description: 'Symbolic tags for this content'
              }
            },
            required: ['content', 'type']
          }
        },
        {
          name: 'query_context',
          description: 'Query context windows with symbolic reasoning',
          inputSchema: {
            type: 'object',
            properties: {
              windowId: {
                type: 'string',
                description: 'ID of context window (optional, uses active if not provided)'
              },
              query: {
                type: 'string',
                description: 'Query string for context retrieval'
              },
              symbols: {
                type: 'array',
                items: { type: 'string' },
                description: 'Symbolic filters for query'
              },
              limit: {
                type: 'number',
                description: 'Maximum number of results to return'
              }
            },
            required: ['query']
            }
          }
        },
        {
          name: 'list_windows',
          description: 'List all available context windows',
          inputSchema: {
            type: 'object',
            properties: {}
          }
        },
        {
          name: 'set_active_window',
          description: 'Set active context window',
          inputSchema: {
            type: 'object',
            properties: {
              windowId: {
                type: 'string',
                description: 'ID of window to set as active'
              }
            },
            required: ['windowId']
          }
        },
        {
          name: 'merge_windows',
          description: 'Merge multiple context windows with symbolic reasoning',
          inputSchema: {
            type: 'object',
            properties: {
              sourceWindows: {
                type: 'array',
                items: { type: 'string' },
                description: 'Array of source window IDs to merge'
              },
              targetWindow: {
                type: 'string',
                description: 'Name for new merged window'
              },
              strategy: {
                type: 'string',
                enum: ['union', 'intersection', 'weighted'],
                description: 'Merge strategy'
              }
            },
            required: ['sourceWindows', 'targetWindow']
          }
        }
      ]
    }));

    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      try {
        switch (name) {
          case 'create_context_window':
            return await this.createContextWindow(args);
          case 'add_context':
            return await this.addContext(args);
          case 'query_context':
            return await this.queryContext(args);
          case 'list_windows':
            return await this.listWindows();
          case 'set_active_window':
            return await this.setActiveWindow(args);
          case 'merge_windows':
            return await this.mergeWindows(args);
          default:
            throw new McpError(
              ErrorCode.MethodNotFound,
              `Unknown tool: ${name}`
            );
        }
      } catch (error) {
        throw new McpError(
          ErrorCode.InternalError,
          `Tool execution failed: ${error.message}`
        );
      }
    });
  }

  async createContextWindow(args) {
    const { name, description, symbols = [] } = args;
    const windowId = uuidv4();

    const newWindow = {
      id: windowId,
      name,
      description: description || '',
      symbols,
      content: [],
      created: new Date().toISOString(),
      lastModified: new Date().toISOString()
    };

    this.context.windows[windowId] = newWindow;
    this.context.activeWindow = windowId;
    await this.saveContext();

    return {
      content: [
        {
          type: 'text',
          text: `Created context window '${name}' with ID: ${windowId}`
        }
      ]
    };
  }

  async addContext(args) {
    const { windowId, content, type, symbols = [] } = args;
    const targetWindowId = windowId || this.context.activeWindow;

    if (!targetWindowId || !this.context.windows[targetWindowId]) {
      throw new McpError(ErrorCode.InvalidParams, 'Invalid window ID');
    }

    const contextEntry = {
      id: uuidv4(),
      content,
      type,
      symbols,
      timestamp: new Date().toISOString()
    };

    this.context.windows[targetWindowId].content.push(contextEntry);
    this.context.windows[targetWindowId].lastModified = new Date().toISOString();
    await this.saveContext();

    return {
      content: [
        {
          type: 'text',
          text: `Added ${type} context to window ${targetWindowId}`
        }
      ]
    };
  }

  async queryContext(args) {
    const { windowId, query, symbols = [], limit = 10 } = args;
    const targetWindowId = windowId || this.context.activeWindow;

    if (!targetWindowId || !this.context.windows[targetWindowId]) {
      throw new McpError(ErrorCode.InvalidParams, 'Invalid window ID');
    }

    const window = this.context.windows[targetWindowId];
    let results = window.content;

    // Filter by symbols if provided
    if (symbols.length > 0) {
      results = results.filter(item =>
        symbols.some(symbol => item.symbols.includes(symbol))
      );
    }

    // Simple text search
    if (query) {
      const queryLower = query.toLowerCase();
      results = results.filter(item =>
        item.content.toLowerCase().includes(queryLower)
      );
    }

    // Limit results
    results = results.slice(0, limit);

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(results, null, 2)
        }
      ]
    };
  }

  async listWindows() {
    const windows = Object.values(this.context.windows).map(window => ({
      id: window.id,
      name: window.name,
      description: window.description,
      symbols: window.symbols,
      contentCount: window.content.length,
      created: window.created,
      lastModified: window.lastModified,
      isActive: window.id === this.context.activeWindow
    }));

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(windows, null, 2)
        }
      ]
    };
  }

  async setActiveWindow(args) {
    const { windowId } = args;

    if (!this.context.windows[windowId]) {
      throw new McpError(ErrorCode.InvalidParams, 'Window ID not found');
    }

    this.context.activeWindow = windowId;
    await this.saveContext();

    const window = this.context.windows[windowId];
    return {
      content: [
        {
          type: 'text',
          text: `Set active window to: ${window.name} (${windowId})`
        }
      ]
    };
  }

  async mergeWindows(args) {
    const { sourceWindows, targetWindow, strategy = 'union' } = args;

    // Validate source windows exist
    const validSources = sourceWindows.filter(id => this.context.windows[id]);
    if (validSources.length === 0) {
      throw new McpError(ErrorCode.InvalidParams, 'No valid source windows found');
    }

    const newWindowId = uuidv4();
    let mergedContent = [];
    let mergedSymbols = new Set();

    // Collect content and symbols based on strategy
    for (const sourceId of validSources) {
      const source = this.context.windows[sourceId];
      mergedContent.push(...source.content);
      source.symbols.forEach(symbol => mergedSymbols.add(symbol));
    }

    // Apply merge strategy
    if (strategy === 'intersection') {
      // Find common content across all windows
      const sourceContents = validSources.map(id =>
        new Set(this.context.windows[id].content.map(item => item.id))
      );
      mergedContent = mergedContent.filter(item =>
        sourceContents.every(contentSet => contentSet.has(item.id))
      );
    }

    const newWindow = {
      id: newWindowId,
      name: targetWindow,
      description: `Merged window from ${validSources.length} sources using ${strategy} strategy`,
      symbols: Array.from(mergedSymbols),
      content: mergedContent,
      created: new Date().toISOString(),
      lastModified: new Date().toISOString()
    };

    this.context.windows[newWindowId] = newWindow;
    this.context.activeWindow = newWindowId;
    await this.saveContext();

    return {
      content: [
        {
          type: 'text',
          text: `Created merged window '${targetWindow}' with ID: ${newWindowId}`
        }
      ]
    };
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error('Eden Context Window MCP server running on stdio');
  }
}

const server = new EdenContextWindowServer();
server.run().catch(console.error);
