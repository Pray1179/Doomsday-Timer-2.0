#!/usr/bin/env python3
"""Doomsday Fan Hub — Local Development Server with NVIDIA NIM Proxy.

Serves the site on http://localhost:8000 and provides a local /api/nvidia-proxy
endpoint that bypasses browser CORS restrictions for NVIDIA NIM APIs.

Usage:
    python3 scripts/serve.py [port]
"""
import http.server
import json
import os
import ssl
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8000


class DoomsdayHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def do_OPTIONS(self):
        """Handle CORS preflight requests."""
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Access-Control-Max-Age", "86400")
        self.end_headers()

    def do_POST(self):
        """Handle /api/nvidia-proxy requests."""
        if self.path == "/api/nvidia-proxy":
            self.handle_nvidia_proxy()
        else:
            self.send_error(404, "Endpoint not found")

    def handle_nvidia_proxy(self):
        content_len = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_len) if content_len > 0 else b""
        auth_header = self.headers.get("Authorization", "")

        target_url = "https://integrate.api.nvidia.com/v1/chat/completions"
        req = urllib.request.Request(target_url, data=body, method="POST")
        req.add_header("Content-Type", "application/json")
        if auth_header:
            req.add_header("Authorization", auth_header)

        # Allow SSL unverified context for local python environments
        ctx = ssl._create_unverified_context()

        try:
            with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
                resp_data = resp.read()
                self.send_response(resp.status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(resp_data)
        except urllib.error.HTTPError as e:
            err_data = e.read()
            self.send_response(e.code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(err_data)
        except Exception as e:
            err_json = json.dumps({"error": str(e)}).encode("utf-8")
            self.send_response(502)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(err_json)


def run():
    os.chdir(ROOT)
    server_address = ("", PORT)
    httpd = http.server.HTTPServer(server_address, DoomsdayHTTPRequestHandler)
    print(f"\n=======================================================")
    print(f"  DOOMSDAY FAN HUB — LOCAL DEV SERVER (CORS PROXY ENABLED)")
    print(f"  Serving at: http://localhost:{PORT}")
    print(f"  Futures Simulator: http://localhost:{PORT}/explore/futures.html")
    print(f"  NVIDIA NIM Proxy:  http://localhost:{PORT}/api/nvidia-proxy")
    print(f"=======================================================\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
        httpd.server_close()


if __name__ == "__main__":
    run()
