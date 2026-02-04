#!/usr/bin/env node

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  ListResourcesRequestSchema,
  ReadResourceRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { baseURL } from "../baseUrl.js";
import { z } from "zod";

const getAppsSdkCompatibleHtml = async (baseUrl, path) => {
  const result = await fetch(`${baseUrl}${path}`);
  return await result.text();
};

type ContentWidget = {
  id: string;
  title: string;
  templateUri: string;
  invoking: string;
  invoked: string;
  html: string;
  description: string;
  widgetDomain: string;
};

const handler = async (server) => {
  const html = await getAppsSdkCompatibleHtml(baseURL, "/");

  const contentWidget = {
    id: "show_content",
    title: "Show Content",
    templateUri: "ui://widget/content-template.html",
    invoking: "Loading content...",
    invoked: "Content loaded",
    html: html,
    description: "Displays the homepage content",
    widgetDomain: "https://nextjs.org/docs",
  };

  server.setRequestHandler(ListResourcesRequestSchema, async () => {
    return {
      resources: [
        {
          uri: contentWidget.templateUri,
          name: contentWidget.title,
          description: contentWidget.description,
          mimeType: "text/html",
        },
      ],
    };
  });

  server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
    if (request.params.uri === contentWidget.templateUri) {
      return {
        contents: [
          {
            uri: request.params.uri,
            mimeType: "text/html",
            text: `<html>${contentWidget.html}</html>`,
          },
        ],
      };
    }
    throw new Error(`Resource not found: ${request.params.uri}`);
  });

  server.setRequestHandler(ListToolsRequestSchema, async () => {
    return {
      tools: [
        {
          name: contentWidget.id,
          description: "Fetch and display the homepage content with the name of the user",
          inputSchema: {
            type: "object",
            properties: {
              name: {
                type: "string",
                description: "The name of the user to display on the homepage",
              },
            },
            required: ["name"],
          },
        },
      ],
    };
  });

  server.setRequestHandler(CallToolRequestSchema, async (request) => {
    if (request.params.name === contentWidget.id) {
      const { name } = request.params.arguments;
      return {
        content: [
          {
            type: "text",
            text: name,
          },
        ],
      };
    }
    throw new Error(`Tool not found: ${request.params.name}`);
  });
};

const server = new Server(
  {
    name: "echo-gateway",
    version: "1.0.0",
  },
  {
    capabilities: {
      tools: {},
      resources: {},
    },
  }
);

await handler(server);

const transport = new StdioServerTransport();
await server.connect(transport);
console.error("Echo Gateway MCP server running on stdio");
