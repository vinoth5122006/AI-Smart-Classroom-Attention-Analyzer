"""
Global Public Access Launcher for AI Smart Classroom Attention Analyzer.
Enables students anywhere in the world on any laptop, tablet, or phone (different Wi-Fi, 4G/5G, remote)
to connect via an encrypted HTTPS public link with zero router/port-forwarding setup.
Uses Cloudflare Quick Tunnel (Free, Zero Account Required).
"""

import os
import sys
import time
import re
import subprocess
import threading
import urllib.request
import webbrowser

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
CLOUDFLARED_BIN = os.path.join(PROJECT_DIR, "cloudflared.exe")
CLOUDFLARED_URL = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"

def ensure_cloudflared() -> str:
    """Checks for or downloads the cloudflared binary."""
    if os.path.exists(CLOUDFLARED_BIN):
        return CLOUDFLARED_BIN

    print("\n[+] Cloudflare Tunnel binary not found. Downloading standalone cloudflared.exe (55 MB)...")
    print("[+] Source: GitHub Cloudflare Releases (100% Free, Official)")

    try:
        req = urllib.request.Request(CLOUDFLARED_URL, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req) as response, open(CLOUDFLARED_BIN, "wb") as out_file:
            total_size = int(response.headers.get("Content-Length", 55366080))
            downloaded = 0
            block_size = 1024 * 256
            while True:
                chunk = response.read(block_size)
                if not chunk:
                    break
                out_file.write(chunk)
                downloaded += len(chunk)
                pct = min(100.0, (downloaded / total_size) * 100.0)
                sys.stdout.write(f"\r[+] Downloading: {pct:.1f}% ({downloaded / (1024*1024):.1f}/{total_size / (1024*1024):.1f} MB)")
                sys.stdout.flush()
        print("\n[+] cloudflared.exe downloaded successfully!\n")
        return CLOUDFLARED_BIN
    except Exception as e:
        print(f"\n[-] Error downloading cloudflared: {e}")
        if os.path.exists(CLOUDFLARED_BIN):
            try: os.remove(CLOUDFLARED_BIN)
            except: pass
        return ""

def kill_existing_cloudflared():
    """Terminates any previously orphaned cloudflared processes on Windows."""
    if os.name == 'nt':
        try:
            subprocess.run(["taskkill", "/F", "/IM", "cloudflared.exe"], capture_output=True)
        except Exception:
            pass

def run_global():
    port = int(os.environ.get("PORT", 8000))
    host = "127.0.0.1"

    print("\n" + "=" * 75)
    print(" SYNAPSE AI \u2022 SMART CLASSROOM GLOBAL ACCESS LAUNCHER ")
    print("=======================================================================")
    print("[*] Initializing telemetry server...")

    # Kill any dangling cloudflared processes from prior runs
    kill_existing_cloudflared()

    # 1. Start FastAPI server in background thread
    def start_uvicorn():
        import uvicorn
        from web_app import app
        uvicorn.run(app, host=host, port=port, log_level="warning")

    server_thread = threading.Thread(target=start_uvicorn, daemon=True)
    server_thread.start()

    # Wait for server to bind
    time.sleep(1.5)

    # 2. Ensure cloudflared is ready
    bin_path = ensure_cloudflared()
    if not bin_path or not os.path.exists(bin_path):
        print("[-] Could not launch global tunnel. Falling back to local mode at http://localhost:8000")
        webbrowser.open(f"http://localhost:{port}")
        server_thread.join()
        return

    # 3. Launch Cloudflare Tunnel with persistent pipe reading
    print("[*] Generating secure public global HTTPS tunnel...")
    tunnel_cmd = [bin_path, "tunnel", "--url", f"http://{host}:{port}"]
    
    process = subprocess.Popen(
        tunnel_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        universal_newlines=True
    )

    tunnel_url = None
    url_pattern = re.compile(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com")
    url_found_event = threading.Event()

    def continuous_pipe_reader():
        """Continuously reads stdout so the OS pipe buffer never fills and freezes cloudflared."""
        nonlocal tunnel_url
        try:
            for line in iter(process.stdout.readline, ''):
                if not line:
                    break
                if not tunnel_url:
                    match = url_pattern.search(line)
                    if match:
                        tunnel_url = match.group(0)
                        url_found_event.set()
        except Exception:
            pass

    reader_thread = threading.Thread(target=continuous_pipe_reader, daemon=True)
    reader_thread.start()

    # Wait for URL to appear (up to 15 seconds)
    url_found_event.wait(timeout=15)

    if tunnel_url:
        student_link = f"{tunnel_url}/join?room=CS-101"
        print("\n" + "=" * 75)
        print(" GLOBAL PUBLIC ACCESS ACTIVE (ANY DEVICE / ANY NETWORK / CELLULAR)")
        print("=" * 75)
        print(f" [ INSTRUCTOR CONSOLE] : {tunnel_url}")
        print(f" [ STUDENT JOIN LINK] : {student_link}")
        print(f" [ LOCAL ACCESS] : http://localhost:{port}")
        print("=" * 75)
        print("\n Send the Student Join Link to your students on mobile or laptop.")
        print(" Works on iPhones, Androids, 4G/5G, and separate Wi-Fi networks.")
        print(" IMPORTANT: KEEP THIS TERMINAL WINDOW OPEN WHILE STUDENTS ARE IN CLASS.")
        print(" (Closing this terminal terminates the tunnel and produces Error 1033).\n")

        # Automatically open instructor console
        webbrowser.open(tunnel_url)
    else:
        print("[-] Could not retrieve tunnel URL in time. Check internet connection.")
        webbrowser.open(f"http://localhost:{port}")

    try:
        while True:
            if process.poll() is not None:
                print("\n[-] Tunnel process exited. Restarting tunnel...")
                break
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[*] Shutting down global tunnel and server...")
        try: process.terminate()
        except: pass
        sys.exit(0)

if __name__ == "__main__":
    run_global()
