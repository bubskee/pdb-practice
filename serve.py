"""Serve the practice range on loopback with headers for interactive pdb."""
import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote, urlsplit

from build import ROOT, build


class Handler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Cross-Origin-Opener-Policy', 'same-origin')
        self.send_header('Cross-Origin-Embedder-Policy', 'require-corp')
        self.send_header('Cross-Origin-Resource-Policy', 'same-origin')
        self.send_header('Cache-Control', 'no-store')
        super().end_headers()

    def send_head(self):
        # A directory index could expose incidental development files.
        path = (ROOT / 'web').resolve()
        target = self.translate_path(self.path)
        from pathlib import Path
        resolved = Path(target).resolve()
        if not resolved.is_relative_to(path):
            self.send_error(403)
            return None
        if any(part.startswith('.') for part in unquote(urlsplit(self.path).path).split('/') if part):
            self.send_error(404)
            return None
        return super().send_head()

    def list_directory(self, path):
        self.send_error(404)
        return None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8000)
    args = parser.parse_args()
    build()
    handler = partial(Handler, directory=str(ROOT / 'web'))
    try:
        server = ThreadingHTTPServer(('127.0.0.1', args.port), handler)
    except OSError as error:
        parser.exit(1, f'Cannot listen on port {args.port}: {error}\nTry --port 8001.\n')
    print(f'Practice range: http://127.0.0.1:{server.server_port}/', flush=True)
    print('Press Ctrl+C to stop. Your editor saves remain in this browser.', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
