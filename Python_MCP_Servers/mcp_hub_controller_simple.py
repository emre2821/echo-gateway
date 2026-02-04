#!/usr/bin/env python3
"""
Eden MCP Hub Controller (Simple Version)
Central control hub for managing multiple MCP servers as separate processes.
"""

import json
import os
import signal
import subprocess
import sys
import time
from typing import Dict, Optional
import psutil
import logging as std_logging

# Setup logging
std_logging.basicConfig(level=std_logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = std_logging.getLogger(__name__)

# Configuration
CONFIG_FILE = "mcp_hub_config.json"
LOGS_DIR = "logs"

# Ensure directories exist
os.makedirs(LOGS_DIR, exist_ok=True)

# Server registry - stores running server processes
server_processes: Dict[str, subprocess.Popen] = {}

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

def start_server(server_id: str) -> str:
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

def stop_server(server_id: str) -> str:
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

def list_servers() -> str:
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

def start_all_enabled() -> str:
    """Start all enabled MCP servers with auto_start=True."""
    config = load_config()
    started = []
    failed = []
    
    for server_id, server_config in config["servers"].items():
        if server_config.get("enabled", True) and server_config.get("auto_start", False):
            if not is_server_running(server_id):
                result = start_server(server_id)
                if "Started" in result:
                    started.append(server_id)
                else:
                    failed.append(f"{server_id}: {result}")
    
    summary = f"Started {len(started)} servers: {', '.join(started) if started else 'None'}"
    if failed:
        summary += f"\nFailed to start {len(failed)} servers: {'; '.join(failed)}"
    
    return summary

def stop_all_servers() -> str:
    """Stop all running MCP servers."""
    running_servers = list(server_processes.keys())
    stopped = []
    failed = []
    
    for server_id in running_servers:
        result = stop_server(server_id)
        if "Stopped" in result:
            stopped.append(server_id)
        else:
            failed.append(f"{server_id}: {result}")
    
    summary = f"Stopped {len(stopped)} servers: {', '.join(stopped) if stopped else 'None'}"
    if failed:
        summary += f"\nFailed to stop {len(failed)} servers: {'; '.join(failed)}"
    
    return summary

def get_hub_status() -> str:
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

def show_help():
    """Show available commands."""
    help_text = """
Eden MCP Hub Controller - Simple CLI Mode

Available commands:
  list                     - List all servers and their status
  start <server_id>        - Start a specific server
  stop <server_id>         - Stop a specific server
  start-all               - Start all enabled servers
  stop-all                - Stop all running servers
  status                  - Show hub status
  help                    - Show this help message
  quit                    - Exit the hub controller

Example usage:
  start eden-context-window
  stop eden-llm-context
  list
"""
    print(help_text)

def main():
    """Main CLI loop."""
    print("=== Eden MCP Hub Controller ===")
    print("Type 'help' for available commands or 'quit' to exit")
    print("")
    
    # Auto-start enabled servers
    print("Auto-starting enabled servers...")
    result = start_all_enabled()
    print(result)
    print("")
    
    # Main command loop
    while True:
        try:
            command = input("hub> ").strip().lower()
            
            if not command:
                continue
                
            if command == "quit" or command == "exit":
                break
            elif command == "help":
                show_help()
            elif command == "list":
                result = list_servers()
                print(result)
            elif command == "status":
                result = get_hub_status()
                print(result)
            elif command == "start-all":
                result = start_all_enabled()
                print(result)
            elif command == "stop-all":
                result = stop_all_servers()
                print(result)
            elif command.startswith("start "):
                server_id = command[6:].strip()
                result = start_server(server_id)
                print(result)
            elif command.startswith("stop "):
                server_id = command[5:].strip()
                result = stop_server(server_id)
                print(result)
            else:
                print(f"Unknown command: {command}. Type 'help' for available commands.")
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")
    
    cleanup()
    print("Hub controller shutdown complete.")

if __name__ == "__main__":
    main()
