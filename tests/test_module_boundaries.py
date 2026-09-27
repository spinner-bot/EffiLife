from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_plan_helper_web_does_not_reintroduce_calendar_ui():
    web_root = ROOT / "plan-helper" / "web"
    scanned = [
        path for path in web_root.rglob("*")
        if path.is_file() and path.suffix.lower() in {".html", ".css", ".js", ".ts", ".vue"}
    ]
    matches = []
    for path in scanned:
        text = path.read_text(encoding="utf-8", errors="ignore").lower()
        if "calendar" in text or "日历" in text:
            matches.append(str(path.relative_to(ROOT)))
    assert matches == [], f"plan-helper web contains calendar UI references: {matches}"


def test_time_helper_owns_the_calendar_route():
    router = (ROOT / "time-helper" / "desk" / "src" / "router" / "index.ts").read_text(encoding="utf-8")
    assert "path: '/calendar'" in router
