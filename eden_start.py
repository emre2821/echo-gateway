#!/usr/bin/env python3
"""
Eden Launcher
Starts the complete Eden system with one double-click.
"""

import subprocess
import sys
import os
import time
import socket

BASE = os.path.dirname(os.path.abspath(__file__))
HUB_PATH = os.path.join(BASE, "CLEAN_STRUCTURE", "spark", "services", "mcp_server_hub.py")

def test_gateway_connection():
    """Test if Local Event Gateway is listening."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex(("127.0.0.1", 8765))
        sock.close()
        return result == 0
    except Exception:
        return False

def run(name, path):
    """Start a process and return the process handle."""
    print(f"[Eden] Starting {name}...")
    return subprocess.Popen([sys.executable, path], cwd=BASE)

if __name__ == "__main__":
    processes = []

    print("🌱 Eden System Starting...")
    print("=" * 50)

    # 1) Start MCP Hub (this also boots gateway + engines)
    if os.path.exists(HUB_PATH):
        processes.append(run("MCP Hub", HUB_PATH))
        time.sleep(5)  # Give gateway more time to fully start accepting connections
        
        # Test if gateway is actually listening
        print("[Eden] Testing Local Event Gateway connection...")
        for i in range(6):  # Reduce retries since we waited longer
            if test_gateway_connection():
                print("[Eden] ✅ Local Event Gateway is listening!")
                break
            else:
                print(f"[Eden] Gateway not ready yet, retrying... ({i+1}/6)")
                time.sleep(2)  # Shorter delay since we waited longer initially
        else:
            print("[Eden] ⚠️  Local Event Gateway may not be listening")
    else:
        print(f"[Eden] ERROR: Hub not found at {HUB_PATH}")
        sys.exit(1)

    # 2) Start Chronicler agent
    chron_path = os.path.join(BASE, "agents", "chronicler.py")
    if os.path.exists(chron_path):
        processes.append(run("Chronicler", chron_path))
        time.sleep(1)
    else:
        print("[Eden] Chronicler not found - continuing without it")

    print("\n🌟 Eden is ONLINE")
    print("🧠 Event nervous system active")
    print("🔌 Local Event Gateway listening on ws://127.0.0.1:8765")
    print("📝 Chronicler observing and remembering")
    print("\n[Eden] Close this window to stop everything.\n")

    try:
        # Wait for all processes
        for p in processes:
            p.wait()
    except KeyboardInterrupt:
        print("\n[Eden] Shutting down...")
        for p in processes:
            try:
                p.terminate()
            except Exception:
                pass  # Process already closed or crashed
        print("[Eden] Goodbye! 🌱")
