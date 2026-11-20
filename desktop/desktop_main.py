"""
Pocket Mechanic - Native macOS Desktop Application Wrapper
Integrates the Flask backend with native macOS WebKit Cocoa window.
"""

import os
import sys
import time
import socket
import threading
import urllib.request

# Ensure project root is at the beginning of sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import webview
from app import create_app

PORT = 5001
HOST = "127.0.0.1"

def is_port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((HOST, port)) == 0

def start_flask_server():
    """Starts the offline Flask application in a background daemon thread."""
    flask_app = create_app()
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    flask_app.run(host=HOST, port=PORT, debug=False, use_reloader=False)

def wait_for_server(timeout: float = 6.0) -> bool:
    """Waits until the backend health endpoint responds."""
    start_time = time.time()
    url = f"http://{HOST}:{PORT}/health"
    while time.time() - start_time < timeout:
        try:
            with urllib.request.urlopen(url, timeout=0.5) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            time.sleep(0.1)
    return False

def main():
    # 1. Start server if not already running on port 5001
    if not is_port_in_use(PORT):
        server_thread = threading.Thread(target=start_flask_server, daemon=True)
        server_thread.start()
        if not wait_for_server():
            print("Warning: Backend health check took longer than expected; launching window anyway.")
    else:
        print(f"Backend already running on {HOST}:{PORT}.")

    # 2. Window configuration
    start_url = f"http://{HOST}:{PORT}/dashboard"

    window = webview.create_window(
        title="Pocket Mechanic",
        url=start_url,
        width=1280,
        height=840,
        min_size=(1024, 680),
        resizable=True,
        background_color="#191919",
        text_select=True,
        zoomable=True
    )

    # 3. Start native Cocoa WebKit runtime
    print("Launching Pocket Mechanic macOS Desktop Application...")
    webview.start(debug=False)

if __name__ == "__main__":
    main()
