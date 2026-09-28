from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GATEWAY = ROOT / "time-helper" / "desk" / "src" / "services" / "planGateway.ts"
I18N = ROOT / "time-helper" / "desk" / "src" / "i18n" / "index.ts"


def test_mobile_plan_fallback_name_uses_i18n():
    source = GATEWAY.read_text(encoding="utf-8")
    assert "translate('plans.unnamed', { id })" in source
    assert "`Plan ${id}`" not in source


def test_plan_fallback_name_exists_in_both_locales():
    source = I18N.read_text(encoding="utf-8")
    assert source.count("'plans.unnamed'") == 2
