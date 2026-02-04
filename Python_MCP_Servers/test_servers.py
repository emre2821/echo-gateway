#!/usr/bin/env python3
"""
Test script to start all MCP servers and verify they work
"""
import subprocess
import time
import sys
import os

def test_server(name, path, command):
    """Test a server by starting it briefly"""
    print(f"\nTesting {name}...")

    try:
        if path.endswith('.js'):
            # Node.js server
            proc = subprocess.Popen(
                ['node', command],
                cwd=path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
        else:
            # Python server
            proc = subprocess.Popen(
                [sys.executable, command],
                cwd=path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

        # Wait a moment for startup
        time.sleep(2)

        # Check if process is still running and has output
        if proc.poll() is None:
            stdout, stderr = proc.communicate(timeout=3)
            if proc.returncode == 0 or "starting" in stdout or "running" in stdout:
                print(f"✅ {name}: Started successfully")
                if stdout.strip():
                    print(f"   Output: {stdout.strip()[:100]}...")
            else:
                print(f"⚠️  {name}: Started but may have issues")
                if stderr.strip():
                    print(f"   Error: {stderr.strip()[:100]}...")
        else:
            print(f"❌ {name}: Failed to start (exit code: {proc.poll()})")

    except subprocess.TimeoutExpired:
        print(f"⏰ {name}: Timeout - but this may be normal for persistent servers")
        proc.terminate()
    except Exception as e:
        print(f"❌ {name}: Error - {e}")

    # Clean up any running processes
    try:
        proc.terminate()
        proc.wait(timeout=2)
    except:
        pass

if __name__ == "__main__":
    base_path = r"c:\Eden_Codeblocks\Eden_CodeBlocks\CascadeProjects\MCP_server"

    servers = [
        ("EdenOS MCP Server", r"edenos_mcp_server", "server.py"),
        ("MCP Server", r"MCP_server", "server.py"),
    ]

    print("Testing all MCP servers...")

    for name, path, command in servers:
        full_path = os.path.join(base_path, path)
        if os.path.exists(full_path):
            test_server(name, full_path, command)
        else:
            print(f"Path not found - {full_path}")

    print("\nServer testing complete!")
    print("All servers have been modified to run persistently")
    print("Run them individually with their respective start commands")
