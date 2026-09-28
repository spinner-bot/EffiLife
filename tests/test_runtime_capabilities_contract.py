from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DESK = ROOT / "time-helper" / "desk" / "src"


def test_runtime_capabilities_uses_tauri_v2_official_detection():
    source = (DESK / "services" / "runtimeCapabilities.ts").read_text(encoding="utf-8")
    assert "@tauri-apps/api/core" in source
    assert "isTauri as tauriIsTauri" in source
    assert "__TAURI__" not in source


def test_native_capability_consumers_share_the_runtime_boundary():
    consumers = [
        DESK / "services" / "ArchiveService.ts",
        DESK / "storage" / "backup.ts",
        DESK / "views" / "SettingsView.vue",
    ]
    for path in consumers:
        source = path.read_text(encoding="utf-8")
        assert "isTauriRuntime" in source
        assert "__TAURI__" not in source


def test_frontend_has_no_legacy_tauri_global_detection():
    for path in (DESK / "services").rglob("*.ts"):
        assert "__TAURI__" not in path.read_text(encoding="utf-8")
    for path in (DESK / "storage").rglob("*.ts"):
        assert "__TAURI__" not in path.read_text(encoding="utf-8")
    for path in (DESK / "views").rglob("*.vue"):
        assert "__TAURI__" not in path.read_text(encoding="utf-8")
