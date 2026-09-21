"""
    ====== web/server.py ======
    Web server for plan-helper UI.
    Uses Flask to serve a modern single-page application.
    Runs without Flask as fallback using Python's built-in http.server.
        by spinner-bot
"""

import sys
import os
import json
import urllib.parse
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
from datetime import datetime

# Add parent directory to path so we can import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules import api
from modules import template as tmpl
from modules import data as dt


# ==========================================
# Static file serving + API routing
# ==========================================

WEB_DIR = Path(__file__).parent
STATIC_DIR = WEB_DIR / "static"


class PlanHelperHandler(SimpleHTTPRequestHandler):
    """Custom HTTP handler that serves static files and handles API routes."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB_DIR), **kwargs)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        # API routes
        if path.startswith("/api/"):
            self._handle_api_get(path, parsed.query)
            return

        # Serve static files or index.html for SPA routing
        if path == "/" or path == "":
            self._serve_file("index.html", "text/html")
        elif path == "/calendar":
            self._serve_file("index.html", "text/html")
        elif path == "/templates":
            self._serve_file("index.html", "text/html")
        else:
            # Try to serve as static file
            super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path.startswith("/api/"):
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8') if content_length > 0 else ""
            try:
                data = json.loads(body) if body else {}
            except json.JSONDecodeError:
                data = {}
            self._handle_api_post(path, data)
        else:
            self.send_error(404)

    def do_PUT(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path.startswith("/api/"):
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8') if content_length > 0 else ""
            try:
                data = json.loads(body) if body else {}
            except json.JSONDecodeError:
                data = {}
            self._handle_api_put(path, data)
        else:
            self.send_error(404)

    def do_DELETE(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path.startswith("/api/"):
            self._handle_api_delete(path)
        else:
            self.send_error(404)

    def _serve_file(self, filename, content_type):
        filepath = WEB_DIR / filename
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read().encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", f"{content_type}; charset=utf-8")
            self.send_header("Content-Length", len(content))
            self.end_headers()
            self.wfile.write(content)
        except FileNotFoundError:
            self.send_error(404)

    def _send_json(self, response):
        content = response.to_json().encode("utf-8")
        self.send_response(response.code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", len(content))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(content)

    def _handle_api_get(self, path, query_string):
        params = dict(urllib.parse.parse_qsl(query_string))

        if path == "/api/plans":
            resp = api.list_plans()
        elif path.startswith("/api/plans/") and path.count("/") == 3:
            plan_id = path.split("/")[-1]
            resp = api.get_plan(plan_id)
        elif path.startswith("/api/plans/") and path.endswith("/full"):
            plan_id = path.split("/")[-2]
            resp = api.get_plan_full(plan_id)
        elif path.startswith("/api/plans/") and path.endswith("/progress"):
            plan_id = path.split("/")[-2]
            resp = api.get_progress(plan_id)
        elif path.startswith("/api/plans/") and path.endswith("/sections"):
            plan_id = path.split("/")[-2]
            resp = api.get_sections(plan_id)
        elif path.startswith("/api/plans/") and path.endswith("/tasks"):
            parts = path.split("/")
            plan_id = parts[2]
            resp = api.get_tasks(plan_id)
        elif path.startswith("/api/plans/") and path.endswith("/logs"):
            plan_id = path.split("/")[-2]
            resp = api.get_logs(plan_id)
        elif path.startswith("/api/plans/") and path.endswith("/conflicts"):
            plan_id = path.split("/")[-2]
            resp = tmpl.detect_conflicts(plan_id)
        elif path == "/api/templates":
            resp = tmpl.list_templates()
        elif path.startswith("/api/templates/"):
            template_id = path.split("/")[-1]
            resp = tmpl.get_template(template_id)
        elif path == "/api/suggestions":
            resp = tmpl.suggest_plan_based_on_history()
        elif path == "/api/backups":
            resp = dt.list_backups()
        elif path == "/api/validate":
            plan_id = params.get("plan_id")
            if plan_id:
                resp = api.validate_plan(plan_id) if hasattr(api, 'validate_plan') else dt.validate_plan(plan_id)
            else:
                resp = dt.validate_all_plans()
        elif path == "/api/tests":
            resp = dt.run_boundary_tests()
        else:
            resp = api.error_response("Unknown API endpoint", code=404)

        self._send_json(resp)

    def _handle_api_post(self, path, data):
        if path == "/api/plans":
            resp = api.create_plan(
                name=data.get("name"),
                date_tuple=tuple(data["date"]) if data.get("date") else None,
                plan_id=data.get("plan_id"),
                sections=data.get("sections", []),
            )
        elif path == "/api/plans/from-template":
            resp = tmpl.apply_template(
                data.get("template_id", "workday"),
                plan_name=data.get("name"),
                plan_date=tuple(data["date"]) if data.get("date") else None,
                plan_id=data.get("plan_id"),
            )
        elif path == "/api/plans/copy-yesterday":
            resp = tmpl.copy_yesterday_plan()
        elif path.startswith("/api/plans/") and path.endswith("/sections"):
            plan_id = path.split("/")[2]
            resp = api.add_section(plan_id, data.get("name", ""), data.get("info", ""))
        elif path.startswith("/api/plans/") and path.endswith("/tasks"):
            parts = path.split("/")
            plan_id = parts[2]
            resp = api.add_task(
                plan_id,
                data.get("section_index", 0),
                data.get("content", ""),
                data.get("time_minutes", 30),
            )
        elif path.startswith("/api/plans/") and path.endswith("/complete"):
            parts = path.split("/")
            plan_id = parts[2]
            resp = api.complete_task(
                plan_id,
                data.get("task_id", ""),
                day=data.get("day", 0),
                time_tuple=tuple(data["time"]) if data.get("time") else None,
            )
        elif path.startswith("/api/plans/") and path.endswith("/logs"):
            plan_id = path.split("/")[2]
            resp = api.add_log(
                plan_id,
                data.get("day", 0),
                data.get("task_id", "base"),
                data.get("time", "acc"),
                data.get("content", ""),
            )
        elif path == "/api/plans/import":
            json_str = data.get("json", "")
            resp = dt.import_plan_from_json(json_str, data.get("new_id"))
        elif path == "/api/backup":
            resp = dt.create_backup()
        elif path.startswith("/api/backup/restore/"):
            backup_file = data.get("file", "")
            resp = dt.restore_from_backup(backup_file)
        else:
            resp = api.error_response("Unknown API endpoint", code=404)

        self._send_json(resp)

    def _handle_api_put(self, path, data):
        parts = path.split("/")
        if path.startswith("/api/plans/") and path.count("/") == 3:
            plan_id = path.split("/")[-1]
            date_tuple = tuple(data["date"]) if data.get("date") else None
            resp = api.update_plan(plan_id, data.get("name"), date_tuple)
        elif len(parts) == 6 and parts[1:3] == ["api", "plans"] and parts[4] == "sections":
            resp = api.update_section(parts[3], parts[5], data.get("name"), data.get("info"))
        elif len(parts) == 6 and parts[1:3] == ["api", "plans"] and parts[4] == "tasks":
            resp = api.update_task(parts[3], parts[5], data.get("content"), data.get("time_minutes"))
        else:
            resp = api.error_response("Unknown API endpoint", code=404)
        self._send_json(resp)

    def _handle_api_delete(self, path):
        if path.startswith("/api/plans/") and path.count("/") == 3:
            plan_id = path.split("/")[-1]
            resp = api.delete_plan(plan_id)
        else:
            resp = api.error_response("Unknown API endpoint", code=404)
        self._send_json(resp)

    def log_message(self, format, *args):
        """Custom log format."""
        sys.stderr.write(f"[{datetime.now().strftime('%H:%M:%S')}] {format % args}\n")


def run_server(host="127.0.0.1", port=8765):
    """Start the web server."""
    server = HTTPServer((host, port), PlanHelperHandler)
    print(f"""
╔══════════════════════════════════════════════╗
║         plan-helper Web UI v0.2.0            ║
║                                              ║
║   Local:   http://{host}:{port}             ║
║                                              ║
║   Press Ctrl+C to stop                       ║
╚══════════════════════════════════════════════╝
""")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
        server.server_close()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="plan-helper Web UI Server")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8765, help="Port to listen on")
    args = parser.parse_args()

    run_server(args.host, args.port)
