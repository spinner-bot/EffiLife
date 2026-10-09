from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VITE = (ROOT / "time-helper" / "desk" / "vite.config.ts").read_text(encoding="utf-8")


def test_desktop_build_splits_stable_vendor_dependencies():
    assert "rollupOptions" in VITE
    assert "manualChunks(id)" in VITE
    for chunk in ("vendor-vue", "vendor-icons", "vendor-charts", "vendor-archive", "vendor-tauri"):
        assert f"return '{chunk}'" in VITE


def test_desktop_chunking_keeps_application_modules_out_of_vendor_buckets():
    assert "if (!moduleId.includes('/node_modules/')) return undefined" in VITE
    assert "moduleId.includes('/vue/')" in VITE
    assert "moduleId.includes('/jszip/')" in VITE
