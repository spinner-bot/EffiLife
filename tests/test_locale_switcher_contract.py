from pathlib import Path


SWITCHER = (Path(__file__).parents[1] / "time-helper" / "desk" / "src" / "components" / "LocaleSwitcher.vue").read_text(encoding="utf-8")
I18N = (Path(__file__).parents[1] / "time-helper" / "desk" / "src" / "i18n" / "index.ts").read_text(encoding="utf-8")


def test_locale_switcher_delegates_changes_to_set_locale_without_direct_mutation():
    assert ':value="locale"' in SWITCHER
    assert '@change="setLocale(($event.target as HTMLSelectElement).value)"' in SWITCHER
    assert 'v-model="locale"' not in SWITCHER


def test_set_locale_remains_the_single_persistence_and_workspace_sync_boundary():
    assert "localStorage.setItem(STORAGE_KEY, currentLocale.value)" in I18N
    assert "if (changed) notifyWorkspaceChanged('settings')" in I18N
