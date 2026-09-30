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


def test_date_detail_returns_to_records_after_calendar_removal():
    catalog = (ROOT / "time-helper" / "desk" / "src" / "i18n" / "index.ts").read_text(encoding="utf-8")
    assert "'dayDetail.back': '返回记录'" in catalog
    assert "'dayDetail.back': 'Back to records'" in catalog
    assert "'dayDetail.back': '返回日历'" not in catalog
    assert "'dayDetail.back': 'Back to calendar'" not in catalog


def test_i18n_does_not_retain_retired_calendar_dictionary():
    catalog = (ROOT / "time-helper" / "desk" / "src" / "i18n" / "index.ts").read_text(encoding="utf-8")
    assert "'nav.calendar':" not in catalog
    assert "'calendar." not in catalog
