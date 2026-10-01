import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "time-helper" / "desk" / "src"
CATALOG = SRC / "i18n" / "index.ts"


def test_all_static_frontend_translation_calls_exist_in_both_locales():
    catalog = CATALOG.read_text(encoding="utf-8")
    used = set()
    for path in SRC.rglob("*"):
        if path.suffix not in {".ts", ".vue"} or path == CATALOG:
            continue
        used.update(re.findall(r"(?:\bt|\btranslate)\(\s*['\"]([^'\"]+)['\"]", path.read_text(encoding="utf-8")))

    missing = sorted(key for key in used if catalog.count(f"'{key}'") < 2)
    assert not missing, f"missing bilingual frontend translation keys: {missing}"


def test_runtime_event_service_localizes_missed_checkin_copy():
    event_system = (SRC / "audio" / "EventSystem.ts").read_text(encoding="utf-8")
    assert "entry.title = translate('settings.events.runtime.missedCheckinTitle')" in event_system
    assert "entry.message = translate('settings.events.runtime.missedCheckinMessage', { date, planName })" in event_system


def test_dynamic_translation_key_families_exist_in_both_locales():
    catalog = CATALOG.read_text(encoding="utf-8")
    dynamic_keys = {
        *(f"tasks.iconTab.{name}" for name in ("icons", "ascii", "colors")),
        *(f"settings.archive.planSource.{name}" for name in ("live", "cache", "snapshot", "unavailable")),
    }
    missing = sorted(key for key in dynamic_keys if catalog.count(f"'{key}'") < 2)
    assert not missing, f"missing bilingual dynamic translation keys: {missing}"


def test_unified_workspace_templates_do_not_embed_visible_cjk_text():
    """Visible copy in the active shell must remain translatable.

    Comments and script/style code are intentionally excluded. Compatibility
    checks in script blocks may still contain legacy data labels; they are not
    rendered user-facing copy.
    """
    template_text_pattern = re.compile(r">([^<>{}]*[\u4e00-\u9fff][^<]*)<")
    for name in ("HomeView.vue", "PlansHubView.vue", "TaskCenterView.vue", "RecordsView.vue", "SettingsView.vue"):
        source = (SRC / "views" / name).read_text(encoding="utf-8")
        template = source.split("<template>", 1)[1].split("</template>", 1)[0]
        template = re.sub(r"<!--.*?-->", "", template, flags=re.DOTALL)
        assert not template_text_pattern.search(template), f"hard-coded visible copy in {name}"
