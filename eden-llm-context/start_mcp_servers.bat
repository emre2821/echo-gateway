@echo off
echo Starting MCP servers...

REM Filesystem MCP Server
start "MCP Filesystem Server" cmd /k ^
mcp-server-filesystem "C:\Users\emmar\mcp_sandbox"

echo MCP servers started.
pause
