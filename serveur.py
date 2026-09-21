# Sert la page et relaie /voicevox vers le moteur local.
#
# Le relais existe pour une raison precise : VOICEVOX refuse (403) toute
# requete portant un en-tete Origin qui n'est pas une application locale.
# Un navigateur en envoie toujours un. On le retire donc ici, plutot que
# d'assouplir la politique CORS du moteur.
import http.server
import os
import socketserver
import sys
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.abspath(__file__))
ENGINE = "http://127.0.0.1:50021"
PREFIX = "/voicevox"
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8777


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=ROOT, **kw)

    def log_message(self, fmt, *args):
        pass

    def _proxy(self, method):
        target = ENGINE + self.path[len(PREFIX):]
        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length) if length else None
        # On ne recopie que le type de contenu : ni Origin, ni Referer, ni cookies.
        req = urllib.request.Request(target, data=body, method=method)
        ct = self.headers.get("Content-Type")
        if ct:
            req.add_header("Content-Type", ct)
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                data, status = r.read(), r.status
                ctype = r.headers.get("Content-Type", "application/octet-stream")
        except urllib.error.HTTPError as e:
            data, status, ctype = e.read(), e.code, "application/json"
        except Exception as e:
            data, status, ctype = str(e).encode(), 502, "text/plain; charset=utf-8"
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        try:
            self.wfile.write(data)
        except (BrokenPipeError, ConnectionAbortedError):
            pass          # l'onglet a ete ferme pendant la synthese

    def do_GET(self):
        if self.path.startswith(PREFIX):
            return self._proxy("GET")
        return super().do_GET()

    def do_POST(self):
        if self.path.startswith(PREFIX):
            return self._proxy("POST")
        self.send_error(405)


class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


if __name__ == "__main__":
    try:
        with Server(("127.0.0.1", PORT), Handler) as httpd:
            print("  Page servie sur http://127.0.0.1:%d/lecture.html" % PORT)
            print("  Moteur relaye : %s -> %s" % (PREFIX, ENGINE))
            print()
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n  Arrete.")
