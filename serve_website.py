"""
Local HTTP Server for Bio-Satellite Lander Web Showcase.
Serves the web dashboard on http://localhost:8080
"""

import http.server
import socketserver
import webbrowser
from pathlib import Path

PORT = 8080
WEB_DIR = Path(__file__).parent / "web"


class CustomHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB_DIR), **kwargs)

    def log_message(self, format, *args):
        # Concise logging
        pass


def main():
    with socketserver.TCPServer(("", PORT), CustomHandler) as httpd:
        url = f"http://localhost:{PORT}"
        print(f"============================================================")
        print(f"  Bio-Satellite Web Sitesi Yayinda!")
        print(f"  Tarayicinizda acmak icin:")
        print(f"  -> {url}")
        print(f"============================================================")
        print("Sunucuyu durdurmak için: Ctrl + C")
        
        try:
            webbrowser.open(url)
        except Exception:
            pass

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nSunucu kapatıldı.")


if __name__ == "__main__":
    main()
