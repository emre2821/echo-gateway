Write-Host "Starting MCP servers..." -ForegroundColor Cyan

# Filesystem MCP Server
Start-Process -NoNewWindow -FilePath "mcp-server-filesystem" `
    -ArgumentList '"C:\Users\emmar\mcp_sandbox"'

Write-Host "MCP servers started." -ForegroundColor Green
