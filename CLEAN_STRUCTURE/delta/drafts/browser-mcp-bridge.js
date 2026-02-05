#!/usr/bin/env node

/**
 * Browser MCP Bridge - For ChatGPT, Grok, GPT4All in browser
 * Converts HTTP requests to MCP stdio protocol
 */

import { spawn } from 'child_process';
import { createServer } from 'http';
import { URL } from 'url';

const PORT = process.env.BRIDGE_PORT || 8083;
const MCP_SERVER = process.env.MCP_SERVER_PATH || 'c:\\Eden_Codeblocks\\Eden_CodeBlocks\\CascadeProjects\\MCP_server\\eden-context-window-mcp\\src\\index.js';

let mcpProcess = null;

// Start MCP server in stdio mode
function startMcpServer() {
    if (mcpProcess) {
        mcpProcess.kill();
    }

    mcpProcess = spawn('node', [MCP_SERVER], {
        stdio: ['pipe', 'pipe', 'pipe'],
        env: { ...process.env, NODE_ENV: 'production' }
    });

    mcpProcess.stdout.on('data', (data) => {
        console.log('MCP stdout:', data.toString());
    });

    mcpProcess.stderr.on('data', (data) => {
        console.log('MCP stderr:', data.toString());
    });

    mcpProcess.on('error', (error) => {
        console.error('MCP process error:', error);
    });

    return mcpProcess;
}

// HTTP Server for browser AI platforms
const server = createServer((req, res) => {
    // Enable CORS
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

    if (req.method === 'OPTIONS') {
        res.writeHead(200);
        res.end();
        return;
    }

    if (req.method === 'GET' && req.url === '/health') {
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({
            status: 'healthy',
            mcpServer: mcpProcess ? 'running' : 'stopped',
            timestamp: Date.now()
        }));
        return;
    }

    if (req.method === 'POST' && (req.url === '/mcp' || req.url === '/')) {
        let body = '';
        req.on('data', chunk => {
            body += chunk.toString();
        });

        req.on('end', () => {
            try {
                const request = JSON.parse(body);

                // Forward to MCP process
                if (mcpProcess && mcpProcess.stdin) {
                    mcpProcess.stdin.write(JSON.stringify(request) + '\n');

                    // Collect response
                    let responseData = '';
                    const collectResponse = (data) => {
                        responseData += data.toString();
                        if (responseData.includes('\n')) {
                            const lines = responseData.split('\n');
                            for (const line of lines) {
                                if (line.trim()) {
                                    try {
                                        const response = JSON.parse(line);
                                        res.writeHead(200, { 'Content-Type': 'application/json' });
                                        res.end(JSON.stringify(response));
                                        mcpProcess.stdout.off('data', collectResponse);
                                        return;
                                    } catch (e) {
                                        // Skip invalid JSON lines
                                    }
                                }
                            }
                        }
                    };

                    mcpProcess.stdout.once('data', collectResponse);

                    // Timeout after 30 seconds
                    setTimeout(() => {
                        mcpProcess.stdout.off('data', collectResponse);
                        res.writeHead(200, { 'Content-Type': 'application/json' });
                        res.end(JSON.stringify({
                            error: { code: -32603, message: 'Request timeout' },
                            id: request.id
                        }));
                    }, 30000);
                } else {
                    res.writeHead(500, { 'Content-Type': 'application/json' });
                    res.end(JSON.stringify({
                        error: { code: -32603, message: 'MCP server not running' }
                    }));
                }
            } catch (error) {
                res.writeHead(400, { 'Content-Type': 'application/json' });
                res.end(JSON.stringify({
                    error: { code: -32700, message: 'Invalid JSON' }
                }));
            }
        });
        return;
    }

    // Static file serving for web interface
    if (req.method === 'GET' && req.url === '/') {
        res.writeHead(200, { 'Content-Type': 'text/html' });
        res.end(`
<!DOCTYPE html>
<html>
<head>
    <title>Browser MCP Bridge</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .container { max-width: 800px; margin: 0 auto; }
        .status { padding: 10px; margin: 10px 0; border-radius: 5px; }
        .healthy { background: #d4edda; color: #155724; }
        .unhealthy { background: #f8d7da; color: #721c24; }
        button { padding: 10px 20px; margin: 5px; border: none; border-radius: 3px; cursor: pointer; }
        .start { background: #28a745; color: white; }
        .stop { background: #dc3545; color: white; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Browser MCP Bridge</h1>
        <div id="status" class="status">Checking status...</div>
        <button class="start" onclick="startServer()">Start MCP Server</button>
        <button class="stop" onclick="stopServer()">Stop MCP Server</button>
        <h2>Usage</h2>
        <p>Send POST requests to <code>/mcp</code> with MCP JSON-RPC 2.0 format.</p>
        <p>Health check: <code>GET /health</code></p>
        <h2>Example</h2>
        <pre>
curl -X POST http://localhost:8083/mcp \
  -H "Content-Type: application/json" \\
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'
        </pre>
    </div>

    <script>
        function updateStatus() {
            fetch('/health')
                .then(response => response.json())
                .then(data => {
                    const statusDiv = document.getElementById('status');
                    if (data.mcpServer === 'running') {
                        statusDiv.className = 'status healthy';
                        statusDiv.textContent = 'MCP Server: Running';
                    } else {
                        statusDiv.className = 'status unhealthy';
                        statusDiv.textContent = 'MCP Server: Stopped';
                    }
                })
                .catch(error => {
                    document.getElementById('status').className = 'status unhealthy';
                    document.getElementById('status').textContent = 'Error: ' + error.message;
                });
        }

        function startServer() {
            fetch('/mcp', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    jsonrpc: '2.0',
                    id: Date.now(),
                    method: 'initialize',
                    params: {
                        protocolVersion: '2025-06-18',
                        capabilities: { tools: {} },
                        clientInfo: { name: 'browser-bridge', version: '1.0.0' }
                    }
                })
            }).then(updateStatus);
        }

        function stopServer() {
            fetch('/mcp', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    jsonrpc: '2.0',
                    id: Date.now(),
                    method: 'shutdown',
                    params: {}
                })
            }).then(updateStatus);
        }

        // Update status every 5 seconds
        setInterval(updateStatus, 5000);
        updateStatus();
    </script>
</body>
</html>
        `);
        return;
    }

    // 404 for other routes
    res.writeHead(404, { 'Content-Type': 'text/plain' });
    res.end('Not Found');
});

// Start the bridge server
server.listen(PORT, () => {
    console.log(`Browser MCP Bridge running on http://localhost:8083`);
    console.log(`MCP Server: ${MCP_SERVER}`);
    console.log('Web interface: http://localhost:8083/');
    console.log('MCP endpoint: http://localhost:8083/mcp');
    console.log('Health check: http://localhost:8083/health');
});

// Auto-start MCP server
startMcpServer();

// Graceful shutdown
process.on('SIGINT', () => {
    if (mcpProcess) {
        mcpProcess.kill();
    }
    process.exit(0);
});

process.on('SIGTERM', () => {
    if (mcpProcess) {
        mcpProcess.kill();
    }
    process.exit(0);
});
