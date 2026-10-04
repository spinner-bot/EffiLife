from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VIEWS = ROOT / "time-helper" / "desk" / "src" / "views"


def test_app_shell_owns_the_single_main_landmark():
    app = (ROOT / "time-helper" / "desk" / "src" / "App.vue").read_text(encoding="utf-8")
    assert app.count('<main ref="mainContent" id="main-content"') == 1


def test_route_views_do_not_nest_additional_main_landmarks():
    for view in VIEWS.glob("*.vue"):
        source = view.read_text(encoding="utf-8")
        assert "<main" not in source, f"nested main landmark remains in {view.name}"
