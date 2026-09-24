from http.client import HTTPConnection
from http.server import HTTPServer
from pathlib import Path
import sys
from threading import Thread


PLAN_HELPER_DIR = Path(__file__).resolve().parents[1] / "plan-helper"
sys.path.insert(0, str(PLAN_HELPER_DIR))

from web.server import PlanHelperHandler  # noqa: E402


def test_plan_api_answers_cors_preflight():
    server = HTTPServer(("127.0.0.1", 0), PlanHelperHandler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        connection = HTTPConnection("127.0.0.1", server.server_port, timeout=3)
        connection.request(
            "OPTIONS",
            "/api/plans",
            headers={
                "Origin": "http://127.0.0.1:1420",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
        )
        response = connection.getresponse()
        assert response.status == 204
        assert response.getheader("Access-Control-Allow-Origin") == "*"
        assert "POST" in response.getheader("Access-Control-Allow-Methods")
        assert "Content-Type" in response.getheader("Access-Control-Allow-Headers")
        connection.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)
