import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SERVICE = ROOT / "time-helper" / "desk" / "src" / "services" / "todoService.ts"
I18N = ROOT / "time-helper" / "desk" / "src" / "i18n" / "index.ts"


def test_todo_service_domain_errors_use_localized_keys():
    service = SERVICE.read_text(encoding="utf-8")
    catalog = I18N.read_text(encoding="utf-8")
    keys = set(re.findall(r"translate\('([^']+)'", service))

    assert keys
    assert all(key.startswith("tasks.") for key in keys)
    for key in keys:
        assert re.search(rf"'{re.escape(key)}':", catalog), f"missing todo i18n key: {key}"

