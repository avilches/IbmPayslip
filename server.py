#!/usr/bin/env python3
"""
Servidor HTTP local para el dashboard de nóminas.
Sirve archivos estáticos con CORS headers para permitir fetch desde el navegador.

Uso:
    uv run server.py          # Puerto 8000 por defecto
    uv run server.py 3000     # Puerto personalizado
"""
from http.server import HTTPServer, SimpleHTTPRequestHandler
import sys


class CORSHandler(SimpleHTTPRequestHandler):
    """Handler que añade CORS headers a todas las respuestas."""

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        """Handle preflight CORS requests."""
        self.send_response(200)
        self.end_headers()


if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    server = HTTPServer(('', port), CORSHandler)
    print(f"Servidor en http://localhost:{port}")
    print(f"Abrir http://localhost:{port}/dashboard.html")
    print("Ctrl+C para detener")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor detenido")
