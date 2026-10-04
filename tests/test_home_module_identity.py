from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOME = (ROOT / "time-helper" / "desk" / "src" / "views" / "HomeView.vue").read_text(encoding="utf-8")
I18N = (ROOT / "time-helper" / "desk" / "src" / "i18n" / "index.ts").read_text(encoding="utf-8")


def test_home_summary_labels_keep_th_ph_td_distinct():
    for key in ("home.timeModuleSummary", "home.planModuleSummary", "home.todoModuleSummary"):
        minimum_uses = 2 if key != "home.todoModuleSummary" else 1
        assert HOME.count(f"t('{key}')") >= minimum_uses
        assert I18N.count(f"'{key}':") == 2
    for code in ("TH", "PH", "TD"):
        assert f"<small>{code}</small>" in HOME
        assert f'class="home-module-code">{code}</span>' in HOME
