from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STORE = (ROOT / "time-helper" / "desk" / "src" / "stores" / "app.ts").read_text(encoding="utf-8")
HOME = (ROOT / "time-helper" / "desk" / "src" / "views" / "HomeView.vue").read_text(encoding="utf-8")


def test_app_store_reuses_initialization_and_allows_retry_after_failure():
    assert "let initPromise: Promise<void> | null = null" in STORE
    assert "if (initPromise) return initPromise" in STORE
    assert "initPromise = null" in STORE


def test_home_does_not_initialize_the_shared_store_again():
    mounted = HOME[HOME.index("onMounted(async () => {"):HOME.index("onUnmounted(() => {")]
    assert "appStore.init()" not in mounted
