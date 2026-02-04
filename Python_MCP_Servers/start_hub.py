#!/usr/bin/env python3
"""
Quick startup script for Eden MCP Hub Controller
"""

import subprocess
import sys
import os

def install_dependencies():
    """Install required dependencies"""
    print("Installing dependencies...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "psutil"], check=True)
        subprocess.run([sys.executable, "-m", "pip", "install", "mcp"], check=True)
        print("Dependencies installed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {e}")
        return False
    return True

def start_hub():
    """Start the MCP Hub Controller"""
    print("Starting Eden MCP Hub Controller...")
    
    # Create necessary directories
    os.makedirs("logs", exist_ok=True)
    os.makedirs("mcp_servers", exist_ok=True)
    
    # Start the hub controller
    try:
        subprocess.run([sys.executable, "mcp_hub_controller.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error starting hub: {e}")
        return False
    except KeyboardInterrupt:
        print("\nHub stopped by user")
        return True
    
    return True

if __name__ == "__main__":
    if install_dependencies():
        start_hub()
    else:
        print("Failed to install dependencies. Please install them manually:")
        print("pip install psutil mcp")
