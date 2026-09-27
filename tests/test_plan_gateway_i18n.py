import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GATEWAY = ROOT / "time-helper" / "desk" / "src" / "services" / "planGateway.ts"
RUNTIME = ROOT / "time-helper" / "desk" / "src" / "services" / "runtimeCapabilities.ts"
I18N = ROOT / "time-helper" / "desk" / "src" / "i18n" / "index.ts"


def test_plan_gateway_generic_errors_use_localized_catalog_keys():
    gateway = GATEWAY.read_text(encoding="utf-8")
    runtime = RUNTIME.read_text(encoding="utf-8")
    catalog = I18N.read_text(encoding="utf-8")

    keys = set(re.findall(r"translate\('([^']+)'", gateway))
    keys.update(re.findall(r"translate\('([^']+)'", runtime))
    assert any(key.startswith("plans.") for key in keys)
    for key in keys:
        assert re.search(rf"'{re.escape(key)}':", catalog), f"missing plan gateway i18n key: {key}"

