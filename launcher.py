#!/usr/bin/env python3
"""
POCKET MECHANIC: Desktop Application Launcher
Starts local Flask backend server and opens the native macOS desktop window.
"""

import sys
import os
import subprocess

def main():
    print("=" * 70)
    print("   POCKET MECHANIC — NATIVE MACOS DESKTOP APPLICATION             ")
    print("   Intelligent Motorcycle Health Monitoring & Predictive Maintenance")
    print("=" * 70)

    desktop_script = os.path.join(os.path.dirname(__file__), "desktop", "desktop_main.py")
    cmd = [sys.executable, desktop_script] + sys.argv[1:]

    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n[Launcher] Shutting down Pocket Mechanic safely.")

if __name__ == "__main__":
    main()
