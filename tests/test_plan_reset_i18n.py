from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SERVICE = ROOT / "time-helper" / "desk" / "src" / "services" / "planReset.ts"
I18N = ROOT / "time-helper" / "desk" / "src" / "i18n" / "index.ts"


def test_plan_reset_fallback_error_uses_i18n():
    source = SERVICE.read_text(encoding="utf-8")
    assert "translate('plans.resetSyncFailed', { status: response.status })" in source
    assert "payload.error ||" in source


def test_plan_reset_error_translation_exists_in_both_locales():
    source = I18N.read_text(encoding="utf-8")
    assert source.count("'plans.resetSyncFailed'") == 2
