from pathlib import Path
from functools import partial
from http.server import ThreadingHTTPServer
from importlib.util import module_from_spec, spec_from_file_location
from threading import Thread
from urllib.request import urlopen


ROOT = Path(__file__).resolve().parents[1]
SERVER = ROOT / "launcher" / "static_server.py"


def load_server_module():
    spec = spec_from_file_location("effilife_static_server", SERVER)
    module = module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_static_server_has_spa_fallback_and_asset_passthrough():
    source = SERVER.read_text(encoding="utf-8")
    assert "class SpaRequestHandler" in source
    assert "candidate.exists()" in source
    assert "self.path = \"/index.html\"" in source
    assert "ThreadingHTTPServer" in source


def test_static_server_serves_client_side_routes(tmp_path):
    module = load_server_module()
    (tmp_path / "index.html").write_text("<html>app</html>", encoding="utf-8")
    (tmp_path / "assets").mkdir()
    (tmp_path / "assets" / "app.js").write_text("console.log('ok')", encoding="utf-8")
    server = ThreadingHTTPServer(("127.0.0.1", 0), partial(module.SpaRequestHandler, directory=str(tmp_path)))
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        base = f"http://127.0.0.1:{server.server_port}"
        assert urlopen(f"{base}/tasks", timeout=2).read() == b"<html>app</html>"
        assert urlopen(f"{base}/assets/app.js", timeout=2).read() == b"console.log('ok')"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
