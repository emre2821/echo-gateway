#!/usr/bin/env python3
"""
Eden MCP Hub Controller
Central control hub for managing multiple MCP servers as separate processes.

This hub can:
- Start/stop individual MCP servers
- Monitor server status
- Route requests to specific servers
- Manage server configurations
- Handle server dependencies

Author: Cascade AI Assistant
"""

import asyncio
import json
import os
import signal
import subprocess
import sys
import time
from typing import Dict, Optional
import psutil
import logging as std_logging  # Use alias to avoid conflicts

from mcp.server import Server

# Initialize MCP server
server = Server("eden-mcp-hub-controller")

# Configuration
CONFIG_FILE = "mcp_hub_config.json"
SERVERS_DIR = "mcp_servers"
LOGS_DIR = "logs"

# Ensure directories exist
os.makedirs(SERVERS_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

# Setup logging
std_logging.basicConfig(
    level=std_logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        std_logging.FileHandler(os.path.join(LOGS_DIR, 'hub_controller.log')),
        std_logging.StreamHandler()
    ]
)
logger = std_logging.getLogger(__name__)

# Server registry - stores running server processes
server_processes: Dict[str, subprocess.Popen] = {}
server_configs: Dict[str, Dict] = {}

def load_config():
    """Load hub configuration."""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Error loading config: {e}")
    
    # Default configuration
    default_config = {
        "servers": {
            "eden-context-window": {
                "name": "Eden Context Window MCP",
                "command": "node",
                "args": ["eden-context-window-mcp/src/index.js"],
                "port": 3001,
                "enabled": True,
                "auto_start": True,
                "dependencies": [],
                "description": "Context window management and symbolic memory"
            },
            "eden-llm-context": {
                "name": "Eden LLM Context MCP", 
                "command": "node",
                "args": ["eden-llm-context/src/index.js"],
                "port": 3002,
                "enabled": True,
                "auto_start": True,
                "dependencies": [],
                "description": "LLM context management and processing"
            },
            "eden-mcp-forge": {
                "name": "Eden MCP Forge",
                "command": "node", 
                "args": ["eden-mcp-forge/dist/cli.js"],
                "port": 3003,
                "enabled": True,
                "auto_start": False,
                "dependencies": [],
                "description": "MCP server development and forging tools"
            },
            "edenos-mcp-server": {
                "name": "EdenOS MCP Server",
                "command": "python",
                "args": ["edenos_mcp_server_bundle.py"],
                "port": 3004,
                "enabled": True,
                "auto_start": False,
                "dependencies": [],
                "description": "EdenOS filesystem and system operations"
            },
            "browser-mcp-bridge": {
                "name": "Browser MCP Bridge",
                "command": "node",
                "args": ["browser-mcp-bridge.js"],
                "port": 3005,
                "enabled": True,
                "auto_start": False,
                "dependencies": [],
                "description": "Browser automation and web interaction"
            }
        },
        "hub_settings": {
            "auto_restart": True,
            "health_check_interval": 30,
            "max_retries": 3,
            "log_level": "INFO"
        }
    }
    
    save_config(default_config)
    return default_config

def save_config(config):
    """Save hub configuration."""
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving config: {e}")

def is_server_running(server_id: str) -> bool:
    """Check if a server process is running."""
    if server_id not in server_processes:
        return False
    
    process = server_processes[server_id]
    if process.poll() is not None:
        # Process has terminated
        del server_processes[server_id]
        return False
    
    return True

def get_server_pid(server_id: str) -> Optional[int]:
    """Get PID of a server process."""
    if server_id in server_processes:
        return server_processes[server_id].pid
    return None

def check_port_available(port: int) -> bool:
    """Check if a port is available."""
    try:
        for conn in psutil.net_connections():
            if conn.laddr.port == port:
                return False
        return True
    except Exception:
        return True

@server.tool()
async def list_servers() -> str:
    """List all configured MCP servers and their status."""
    config = load_config()
    servers_info = []
    
    for server_id, server_config in config["servers"].items():
        status = "running" if is_server_running(server_id) else "stopped"
        pid = get_server_pid(server_id)
        port = server_config.get("port", "N/A")
        
        servers_info.append({
            "id": server_id,
            "name": server_config["name"],
            "status": status,
            "pid": pid,
            "port": port,
            "enabled": server_config.get("enabled", True),
            "auto_start": server_config.get("auto_start", False),
            "description": server_config.get("description", "")
        })
    
    return json.dumps(servers_info, indent=2)

@server.tool()
async def start_server(server_id: str) -> str:
    """Start a specific MCP server."""
    config = load_config()
    
    if server_id not in config["servers"]:
        return f"Error: Server '{server_id}' not found in configuration"
    
    if is_server_running(server_id):
        return f"Server '{server_id}' is already running (PID: {get_server_pid(server_id)})"
    
    server_config = config["servers"][server_id]
    
    if not server_config.get("enabled", True):
        return f"Server '{server_id}' is disabled"
    
    # Check dependencies
    dependencies = server_config.get("dependencies", [])
    for dep_id in dependencies:
        if not is_server_running(dep_id):
            return f"Dependency '{dep_id}' is not running. Please start it first."
    
    # Check port availability
    port = server_config.get("port")
    if port and not check_port_available(port):
        return f"Port {port} is already in use"
    
    try:
        command = server_config["command"]
        args = server_config["args"]
        
        # Create log file for this server
        log_file = os.path.join(LOGS_DIR, f"{server_id}.log")
        
        # Start the process
        process = subprocess.Popen(
            [command] + args,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            cwd=os.getcwd()
        )
        
        server_processes[server_id] = process
        
        # Start logging thread
        def log_output():
            with open(log_file, "a") as f:
                f.write(f"\n--- Server {server_id} started at {time.ctime()} ---\n")
                for line in process.stdout:
                    f.write(line)
                    f.flush()
        
        import threading
        log_thread = threading.Thread(target=log_output, daemon=True)
        log_thread.start()
        
        # Wait a moment to see if process starts successfully
        time.sleep(1)
        
        if process.poll() is None:
            logger.info(f"Started server '{server_id}' with PID {process.pid}")
            return f"Started server '{server_id}' (PID: {process.pid}, Port: {port})"
        else:
            # Process failed to start
            del server_processes[server_id]
            return_code = process.returncode
            return f"Failed to start server '{server_id}'. Return code: {return_code}"
            
    except Exception as e:
        logger.error(f"Error starting server {server_id}: {e}")
        return f"Error starting server '{server_id}': {str(e)}"

@server.tool()
async def stop_server(server_id: str) -> str:
    """Stop a specific MCP server."""
    if server_id not in server_processes:
        return f"Server '{server_id}' is not running"
    
    process = server_processes[server_id]
    pid = process.pid
    
    try:
        # Try graceful shutdown first
        process.terminate()
        
        # Wait for graceful shutdown
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            # Force kill if graceful shutdown fails
            process.kill()
            process.wait()
        
        del server_processes[server_id]
        logger.info(f"Stopped server '{server_id}' (PID: {pid})")
        return f"Stopped server '{server_id}' (PID: {pid})"
        
    except Exception as e:
        logger.error(f"Error stopping server {server_id}: {e}")
        return f"Error stopping server '{server_id}': {str(e)}"

@server.tool()
async def restart_server(server_id: str) -> str:
    """Restart a specific MCP server."""
    if is_server_running(server_id):
        stop_result = await stop_server(server_id)
        if "Error" in stop_result:
            return stop_result
    
    # Wait a moment before starting
    await asyncio.sleep(1)
    
    return await start_server(server_id)

@server.tool()
async def start_all_enabled() -> str:
    """Start all enabled MCP servers with auto_start=True."""
    config = load_config()
    started = []
    failed = []
    
    for server_id, server_config in config["servers"].items():
        if server_config.get("enabled", True) and server_config.get("auto_start", False):
            if not is_server_running(server_id):
                result = await start_server(server_id)
                if "Started" in result:
                    started.append(server_id)
                else:
                    failed.append(f"{server_id}: {result}")
    
    summary = f"Started {len(started)} servers: {', '.join(started) if started else 'None'}"
    if failed:
        summary += f"\nFailed to start {len(failed)} servers: {'; '.join(failed)}"
    
    return summary

@server.tool()
async def stop_all_servers() -> str:
    """Stop all running MCP servers."""
    running_servers = list(server_processes.keys())
    stopped = []
    failed = []
    
    for server_id in running_servers:
        result = await stop_server(server_id)
        if "Stopped" in result:
            stopped.append(server_id)
        else:
            failed.append(f"{server_id}: {result}")
    
    summary = f"Stopped {len(stopped)} servers: {', '.join(stopped) if stopped else 'None'}"
    if failed:
        summary += f"\nFailed to stop {len(failed)} servers: {'; '.join(failed)}"
    
    return summary

@server.tool()
async def get_server_logs(server_id: str, lines: int = 50) -> str:
    """Get recent logs for a specific server."""
    log_file = os.path.join(LOGS_DIR, f"{server_id}.log")
    
    if not os.path.exists(log_file):
        return f"No log file found for server '{server_id}'"
    
    try:
        with open(log_file, "r") as f:
            log_lines = f.readlines()
        
        # Return last N lines
        recent_lines = log_lines[-lines:] if len(log_lines) > lines else log_lines
        return "".join(recent_lines)
        
    except Exception as e:
        return f"Error reading logs for '{server_id}': {str(e)}"

@server.tool()
async def enable_server(server_id: str) -> str:
    """Enable a server in configuration."""
    config = load_config()
    
    if server_id not in config["servers"]:
        return f"Error: Server '{server_id}' not found"
    
    config["servers"][server_id]["enabled"] = True
    save_config(config)
    
    return f"Enabled server '{server_id}'"

@server.tool()
async def disable_server(server_id: str) -> str:
    """Disable a server in configuration."""
    config = load_config()
    
    if server_id not in config["servers"]:
        return f"Error: Server '{server_id}' not found"
    
    # Stop server if running
    if is_server_running(server_id):
        await stop_server(server_id)
    
    config["servers"][server_id]["enabled"] = False
    save_config(config)
    
    return f"Disabled server '{server_id}'"

@server.tool()
async def set_auto_start(server_id: str, auto_start: bool) -> str:
    """Set auto_start flag for a server."""
    config = load_config()
    
    if server_id not in config["servers"]:
        return f"Error: Server '{server_id}' not found"
    
    config["servers"][server_id]["auto_start"] = auto_start
    save_config(config)
    
    status = "enabled" if auto_start else "disabled"
    return f"Auto-start {status} for server '{server_id}'"

@server.tool()
async def get_hub_status() -> str:
    """Get overall hub status and statistics."""
    config = load_config()
    running_count = len(server_processes)
    total_count = len(config["servers"])
    enabled_count = sum(1 for s in config["servers"].values() if s.get("enabled", True))
    
    status = {
        "hub_controller": "running",
        "total_servers": total_count,
        "enabled_servers": enabled_count,
        "running_servers": running_count,
        "stopped_servers": total_count - running_count,
        "server_processes": [
            {
                "id": sid,
                "pid": proc.pid,
                "name": config["servers"].get(sid, {}).get("name", sid)
            }
            for sid, proc in server_processes.items()
        ]
    }
    
    return json.dumps(status, indent=2)

# Cleanup function for graceful shutdown
def cleanup():
    """Cleanup all server processes on hub shutdown."""
    logger.info("Shutting down hub controller...")
    for server_id in list(server_processes.keys()):
        try:
            stop_server(server_id)
        except Exception as e:
            logger.error(f"Error stopping server {server_id} during cleanup: {e}")

# Signal handlers for graceful shutdown
def signal_handler(signum, frame):
    """Handle shutdown signals."""
    cleanup()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

if __name__ == "__main__":
    # Load initial configuration
    config = load_config()
    logger.info("Eden MCP Hub Controller starting...")
    
    # Auto-start enabled servers
    async def auto_start():
        await start_all_enabled()
    
    # Run auto-start in background
    asyncio.create_task(auto_start())
    
    logger.info("MCP Hub Controller ready. Use tools to manage servers.")
    
    # Run the MCP server
    server.run()
