"""Small SPA-aware static server used by the development launcher fallback."""

from __future__ import annotations

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit


class SpaRequestHandler(SimpleHTTPRequestHandler):
    """Serve static assets normally and route client-side paths to index.html."""

    def do_GET(self):  # noqa: N802 - required by http.server
        requested_path = unquote(urlsplit(self.path).path)
        candidate = Path(self.translate_path(requested_path))
        filename = candidate.name
        is_asset = "." in filename
        if requested_path != "/" and not candidate.exists() and not is_asset:
            self.path = "/index.html"
        return super().do_GET()

    def log_message(self, format, *args):
        # Keep launcher output concise while retaining normal request errors.
        if args and str(args[1]).startswith("4"):
            super().log_message(format, *args)


def main() -> None:
    parser = argparse.ArgumentParser(description="Serve an EffiLife SPA build")
    parser.add_argument("--directory", required=True, type=Path)
    parser.add_argument("--bind", default="127.0.0.1")
    parser.add_argument("--port", required=True, type=int)
    args = parser.parse_args()
    handler = partial(SpaRequestHandler, directory=str(args.directory))
    server = ThreadingHTTPServer((args.bind, args.port), handler)
    print(f"Serving {args.directory} at http://{args.bind}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
