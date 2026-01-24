#!/usr/bin/env node

/**
 * Universal File Reader MCP Server
 * Reads any file type with smart content extraction
 * Supports: PDF, DOCX, TXT, JSON, CSV, Images, and more
 */

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  ListResourcesRequestSchema,
  ReadResourceRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import fs from "fs/promises";
import path from "path";
import { homedir } from "os";

// Configuration via environment variables
const MAX_FILE_SIZE = parseInt(process.env.MAX_FILE_SIZE) || 50 * 1024 * 1024; // 50MB default
const ALLOWED_DIRECTORIES = process.env.ALLOWED_DIRECTORIES ?
  process.env.ALLOWED_DIRECTORIES.split(',').map(d => path.resolve(d.trim())) :
  [homedir(), process.cwd()];

// Create require function for ES modules
const { createRequire } = await import('module');
const require = createRequire(import.meta.url);

// Lazy load heavy dependencies
let pdfParse = null;
let PDFDocument = null;
let mammoth = null;
let csvParser = null;

function loadDependencies() {
  if (!pdfParse) {
    try {
      pdfParse = require("pdf-parse");
      PDFDocument = require("pdf-lib");
      console.error("[Universal Reader] PDF dependencies loaded");
    } catch (error) {
      console.error("[Universal Reader] PDF dependencies not available:", error.message);
    }
  }
  if (!mammoth) {
    try {
      mammoth = require("mammoth");
      console.error("[Universal Reader] DOCX dependencies loaded");
    } catch (error) {
      console.error("[Universal Reader] DOCX dependencies not available:", error.message);
    }
  }
  if (!csvParser) {
    try {
      csvParser = require("csv-parse");
      console.error("[Universal Reader] CSV parser loaded");
    } catch (error) {
      console.error("[Universal Reader] CSV parser not available, using fallback:", error.message);
    }
  }
}

// Helper function to resolve paths with security validation
function resolvePath(inputPath) {
  if (!inputPath) return inputPath;

  if (inputPath.startsWith('~')) {
    return path.join(homedir(), inputPath.slice(1));
  }

  if (path.isAbsolute(inputPath)) {
    return inputPath;
  }

  return path.resolve(inputPath);
}

// Security validation function
function validatePath(filePath) {
  const resolvedPath = path.resolve(filePath);

  // Check for directory traversal attempts
  if (resolvedPath.includes('..')) {
    return { valid: false, error: 'Path traversal not allowed' };
  }

  // Check if path is within allowed directories
  const isAllowed = ALLOWED_DIRECTORIES.some(allowedDir =>
    resolvedPath.startsWith(allowedDir)
  );

  if (!isAllowed) {
    return {
      valid: false,
      error: `Access denied. Path must be within one of: ${ALLOWED_DIRECTORIES.join(', ')}`
    };
  }

  return { valid: true, path: resolvedPath };
}

// Get file info
async function getFileInfo(filePath) {
  try {
    const stats = await fs.stat(filePath);
    return {
      name: path.basename(filePath),
      size: stats.size,
      sizeFormatted: formatFileSize(stats.size),
      modified: stats.mtime,
      extension: path.extname(filePath).toLowerCase(),
      isReadable: true
    };
  } catch (error) {
    return {
      name: path.basename(filePath),
      size: 0,
      sizeFormatted: "0 B",
      modified: new Date(),
      extension: path.extname(filePath).toLowerCase(),
      isReadable: false,
      error: error.message
    };
  }
}

// Format file size
function formatFileSize(bytes) {
  if (bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
}

// Read text files
async function readTextFile(filePath) {
  try {
    const content = await fs.readFile(filePath, 'utf8');
    return {
      success: true,
      content: content,
      type: 'text',
      encoding: 'utf8',
      lines: content.split('\n').length,
      characters: content.length
    };
  } catch (error) {
    return {
      success: false,
      error: error.message
    };
  }
}

// Read PDF files
async function readPdfFile(filePath) {
  loadDependencies();
  if (!pdfParse || !PDFDocument) {
    return {
      success: false,
      error: "PDF dependencies not available"
    };
  }

  try {
    const pdfBytes = await fs.readFile(filePath);
    const pdfData = await pdfParse(pdfBytes);

    // Try to get form fields if pdf-lib is available
    let formFields = [];
    try {
      const pdfDoc = await PDFDocument.load(pdfBytes);
      const form = pdfDoc.getForm();
      if (form) {
        const fields = form.getFields();
        formFields = fields.map(field => ({
          name: field.getName(),
          type: field.constructor.name,
          value: field.getText() || field.getSelected() || null
        }));
      }
    } catch (e) {
      console.error("Could not extract form fields:", e.message);
    }

    return {
      success: true,
      content: pdfData.text,
      type: 'pdf',
      pages: pdfData.numpages,
      info: pdfData.info,
      formFields: formFields,
      characters: pdfData.text.length
    };
  } catch (error) {
    return {
      success: false,
      error: error.message
    };
  }
}

// Read DOCX files
async function readDocxFile(filePath) {
  loadDependencies();
  if (!mammoth) {
    return {
      success: false,
      error: "DOCX dependencies not available"
    };
  }

  try {
    const docxBytes = await fs.readFile(filePath);
    const result = await mammoth.extractRawText({ arrayBuffer: docxBytes });

    return {
      success: true,
      content: result.value,
      type: 'docx',
      characters: result.value.length
    };
  } catch (error) {
    return {
      success: false,
      error: error.message
    };
  }
}

// Read image files (as base64)
async function readImageFile(filePath) {
  try {
    const imageBytes = await fs.readFile(filePath);
    const ext = path.extname(filePath).toLowerCase();
    const mimeTypes = {
      '.jpg': 'image/jpeg',
      '.jpeg': 'image/jpeg',
      '.png': 'image/png',
      '.gif': 'image/gif',
      '.bmp': 'image/bmp',
      '.webp': 'image/webp'
    };

    return {
      success: true,
      content: imageBytes.toString('base64'),
      type: 'image',
      mimeType: mimeTypes[ext] || 'application/octet-stream',
      size: imageBytes.length
    };
  } catch (error) {
    return {
      success: false,
      error: error.message
    };
  }
}

// Read JSON files
async function readJsonFile(filePath) {
  try {
    const content = await fs.readFile(filePath, 'utf8');
    const parsed = JSON.parse(content);

    return {
      success: true,
      content: parsed,
      type: 'json',
      raw: content,
      characters: content.length
    };
  } catch (error) {
    return {
      success: false,
      error: error.message
    };
  }
}

// Read CSV files with proper parsing
async function readCsvFile(filePath) {
  try {
    const content = await fs.readFile(filePath, 'utf8');

    // Use proper CSV parser if available, otherwise fallback
    if (csvParser) {
      return new Promise((resolve, reject) => {
        csvParser.parse(content, {
          columns: true,
          skip_empty_lines: true,
          trim: true
        }, (err, records) => {
          if (err) {
            reject({ success: false, error: err.message });
          } else {
            resolve({
              success: true,
              content: { headers: Object.keys(records[0] || {}), rows: records },
              type: 'csv',
              lines: records.length,
              characters: content.length
            });
          }
        });
      });
    } else {
      // Fallback CSV parsing
      const lines = content.split('\n').filter(line => line.trim());
      const headers = lines[0] ? lines[0].split(',').map(h => h.trim().replace(/^"|"$/g, '')) : [];
      const rows = lines.slice(1).map(line => {
        const values = line.split(',').map(cell => cell.trim().replace(/^"|"$/g, ''));
        return headers.reduce((obj, header, index) => {
          obj[header] = values[index] || '';
          return obj;
        }, {});
      });

      return {
        success: true,
        content: { headers, rows },
        type: 'csv',
        lines: rows.length,
        characters: content.length
      };
    }
  } catch (error) {
    return {
      success: false,
      error: error.message
    };
  }
}

// Main file reader function with security and size checks
async function readFile(filePath) {
  // Validate path security
  const validation = validatePath(filePath);
  if (!validation.valid) {
    return {
      success: false,
      error: validation.error
    };
  }

  const validatedPath = validation.path;
  const fileInfo = await getFileInfo(validatedPath);

  if (!fileInfo.isReadable) {
    return {
      success: false,
      error: fileInfo.error || "File not accessible"
    };
  }

  // Check file size limit
  if (fileInfo.size > MAX_FILE_SIZE) {
    return {
      success: false,
      error: `File too large. Maximum size is ${formatFileSize(MAX_FILE_SIZE)}`
    };
  }

  const ext = fileInfo.extension;

  switch (ext) {
    case '.txt':
    case '.md':
    case '.log':
      return await readTextFile(validatedPath);

    case '.pdf':
      return await readPdfFile(validatedPath);

    case '.docx':
      return await readDocxFile(validatedPath);

    case '.json':
      return await readJsonFile(validatedPath);

    case '.csv':
      return await readCsvFile(validatedPath);

    case '.jpg':
    case '.jpeg':
    case '.png':
    case '.gif':
    case '.bmp':
    case '.webp':
      return await readImageFile(validatedPath);

    default:
      return await readTextFile(validatedPath); // Try as text for unknown types
  }
}

// Create server
const server = new Server(
  {
    name: "universal-file-reader",
    version: "1.0.0",
  },
  {
    capabilities: {
      tools: true,
      resources: true,
    },
  }
);

// List tools
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: "read_file",
        description: "Read any file type with smart content extraction",
        inputSchema: {
          type: "object",
          properties: {
            file_path: {
              type: "string",
              description: "Path to the file to read"
            }
          },
          required: ["file_path"]
        },
      },
      {
        name: "list_directory",
        description: "List files and directories with detailed info",
        inputSchema: {
          type: "object",
          properties: {
            directory: {
              type: "string",
              description: "Directory path to list (default: current directory)"
            },
            show_hidden: {
              type: "boolean",
              description: "Show hidden files (default: false)",
              default: false
            }
          },
        },
      },
      {
        name: "get_file_info",
        description: "Get detailed information about a file",
        inputSchema: {
          type: "object",
          properties: {
            file_path: {
              type: "string",
              description: "Path to the file"
            }
          },
          required: ["file_path"]
        },
      },
      {
        name: "search_files",
        description: "Search for files by name pattern",
        inputSchema: {
          type: "object",
          properties: {
            directory: {
              type: "string",
              description: "Directory to search in (default: current directory)"
            },
            pattern: {
              type: "string",
              description: "Search pattern (supports * and ? wildcards)"
            },
            file_type: {
              type: "string",
              description: "Filter by file type (pdf, image, text, etc.)"
            }
          },
          required: ["pattern"]
        },
      }
    ],
  };
});

// Handle tool calls
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    switch (name) {
      case "read_file":
        const { file_path } = args;
        const resolvedPath = resolvePath(file_path);
        const result = await readFile(resolvedPath);

        if (!result.success) {
          throw new Error(result.error);
        }

        let response = `File: ${path.basename(resolvedPath)}\n`;
        response += `Type: ${result.type}\n`;
        response += `Size: ${formatFileSize(await (await fs.stat(resolvedPath)).size)}\n\n`;

        if (result.type === 'image') {
          return {
            content: [
              {
                type: "text",
                text: response
              },
              {
                type: "image",
                data: result.content,
                mimeType: result.mimeType
              }
            ],
          };
        } else if (result.type === 'json') {
          return {
            content: [
              {
                type: "text",
                text: response + "JSON Content:\n"
              },
              {
                type: "text",
                text: JSON.stringify(result.content, null, 2)
              }
            ],
          };
        } else if (result.type === 'csv') {
          const csvText = `Headers: ${result.content.headers.join(', ')}\n\n`;
          csvText += `Rows: ${result.content.rows.length} total\n\n`;
          csvText += result.content.rows.slice(0, 5).map((row, i) =>
            `Row ${i + 1}: ${row.join(', ')}`
          ).join('\n');
          if (result.content.rows.length > 5) {
            csvText += `\n... and ${result.content.rows.length - 5} more rows`;
          }

          return {
            content: [
              {
                type: "text",
                text: response + csvText
              }
            ],
          };
        } else {
          response += `Content:\n${"=".repeat(50)}\n`;
          response += result.content;

          return {
            content: [
              {
                type: "text",
                text: response
              }
            ],
          };
        }

      case "list_directory":
        const { directory: dir = process.cwd(), show_hidden = false } = args;
        const resolvedDirPath = resolvePath(dir);

        try {
          const entries = await fs.readdir(resolvedDirPath, { withFileTypes: true });
          const files = [];

          for (const entry of entries) {
            if (!show_hidden && entry.name.startsWith('.')) {
              continue;
            }

            const fullPath = path.join(resolvedDirPath, entry.name);
            const info = await getFileInfo(fullPath);

            files.push({
              name: entry.name,
              path: fullPath,
              type: entry.isDirectory() ? 'directory' : 'file',
              size: info.sizeFormatted,
              modified: info.modified,
              extension: info.extension
            });
          }

          const sortedFiles = files.sort((a, b) => {
            // Directories first, then files
            if (a.type === 'directory' && b.type !== 'directory') return -1;
            if (a.type !== 'directory' && b.type === 'directory') return 1;
            return a.name.localeCompare(b.name);
          });

          let output = `Directory: ${resolvedPath}\n`;
          output += `Total items: ${sortedFiles.length}\n\n`;

          for (const file of sortedFiles) {
            const icon = file.type === 'directory' ? '📁' : '📄';
            output += `${icon} ${file.name.padEnd(30)} ${file.size.padEnd(10)} ${file.type}\n`;
          }

          return {
            content: [
              {
                type: "text",
                text: output
              }
            ],
          };
        } catch (error) {
          throw new Error(`Failed to list directory: ${error.message}`);
        }

      case "get_file_info":
        const { file_path: infoPath } = args;
        const resolvedInfoPath = resolvePath(infoPath);
        const info = await getFileInfo(resolvedInfoPath);

        let output = `File Information for: ${info.name}\n`;
        output += `Path: ${resolvedInfoPath}\n`;
        output += `Type: ${info.extension}\n`;
        output += `Size: ${info.sizeFormatted}\n`;
        output += `Modified: ${info.modified.toISOString()}\n`;
        output += `Readable: ${info.isReadable ? 'Yes' : 'No'}\n`;

        if (info.error) {
          output += `Error: ${info.error}\n`;
        }

        return {
          content: [
            {
              type: "text",
              text: output
            }
          ],
        };

      case "search_files":
        const { directory: searchDir = process.cwd(), pattern, file_type } = args;
        const resolvedSearchPath = resolvePath(searchDir);

        try {
          const entries = await fs.readdir(resolvedSearchPath, { withFileTypes: true });
          const matches = [];

          for (const entry of entries) {
            if (entry.isDirectory()) continue;

            const nameMatches = entry.name.toLowerCase().includes(pattern.toLowerCase());
            const typeMatches = !file_type || entry.name.toLowerCase().endsWith(file_type.toLowerCase());

            if (nameMatches && typeMatches) {
              const fullPath = path.join(resolvedSearchPath, entry.name);
              const info = await getFileInfo(fullPath);
              matches.push({
                name: entry.name,
                path: fullPath,
                size: info.sizeFormatted,
                type: info.extension
              });
            }
          }

          let output = `Search Results for "${pattern}" in ${resolvedPath}:\n`;
          output += `Found ${matches.length} matches\n\n`;

          for (const match of matches) {
            output += `📄 ${match.name.padEnd(30)} ${match.size.padEnd(10)} ${match.type}\n`;
          }

          return {
            content: [
              {
                type: "text",
                text: output
              }
            ],
          };
        } catch (error) {
          throw new Error(`Search failed: ${error.message}`);
        }

      default:
        throw new Error(`Unknown tool: ${name}`);
    }
  } catch (error) {
    return {
      content: [
        {
          type: "text",
          text: `Error: ${error.message}`
        }
      ],
      isError: true,
    };
  }
});

// Resource handlers
server.setRequestHandler(ListResourcesRequestSchema, async () => {
  return {
    resources: [
      {
        uri: "file://localhost/",
        name: "Local File System",
        description: "Access local files through resource protocol",
        mimeType: "text/plain"
      }
    ]
  };
});

server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
  const { uri } = request.params;

  if (!uri.startsWith("file://localhost/")) {
    throw new Error("Invalid resource URI");
  }

  const filePath = uri.replace("file://localhost/", "");
  const resolvedResourcePath = resolvePath(filePath);
  const result = await readFile(resolvedResourcePath);

  if (!result.success) {
    throw new Error(result.error);
  }

  return {
    contents: [
      {
        uri: uri,
        mimeType: result.type === 'image' ? result.mimeType : 'text/plain',
        blob: result.content
      }
    ]
  };
});

// Start server
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("Universal File Reader MCP server running...");
}

main().catch((error) => {
  console.error("[Universal Reader] Fatal error:", error);
  console.error("[Universal Reader] Stack trace:", error.stack);
  process.exit(1);
});
