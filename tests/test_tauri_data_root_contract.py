from pathlib import Path


SOURCE = Path("time-helper/desk/src-tauri/src/lib.rs").read_text(encoding="utf-8")


def test_tauri_data_root_honors_shared_environment_contract():
    assert 'std::env::var("EFFILIFE_DATA_DIR")' in SOURCE
    assert 'let configured = configured.trim();' in SOURCE
    assert 'if !configured.is_empty()' in SOURCE
    assert 'return path;' in SOURCE


def test_tauri_keeps_platform_default_as_fallback():
    assert "dirs::data_local_dir()" in SOURCE
    assert 'path.push("EffiLife");' in SOURCE
    assert 'path.push("data");' in SOURCE


def test_tauri_sidecar_preserves_explicit_shared_root_but_unwraps_platform_fallback():
    assert "fn get_plan_helper_data_dir() -> PathBuf" in SOURCE
    assert 'std::env::var("EFFILIFE_DATA_DIR")' in SOURCE
    assert "return PathBuf::from(configured);" in SOURCE
    assert "let plan_runtime_root = get_plan_helper_data_dir();" in SOURCE
