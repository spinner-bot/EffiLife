from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "build_windows_native.ps1"


def test_windows_native_helper_initializes_msvc_before_cargo_or_tauri():
    source = SCRIPT.read_text(encoding="utf-8")
    assert "vswhere.exe" in source
    assert "Microsoft.VisualStudio.Component.VC.Tools.x86.x64" in source
    assert "vcvars64.bat" in source
    assert "call `\"$vcvars`\" -arch=x64" in source
    assert "@($vswhereCandidates)[0]" in source
    assert "$environmentLines" in source


def test_windows_native_helper_uses_managed_rust_and_node_defaults_with_overrides():
    source = SCRIPT.read_text(encoding="utf-8")
    assert "EFFILIFE_RUST_TOOLCHAIN_DIR" in source
    assert "EFFILIFE_NODE_DIR" in source
    assert "F:\\dev-tools\\rustup\\toolchains\\stable-x86_64-pc-windows-msvc\\bin" in source
    assert "F:\\dev-tools\\node" in source
    assert "cargo.exe'" in source
    assert "npm.cmd'" in source


def test_windows_native_helper_has_check_and_build_boundaries():
    source = SCRIPT.read_text(encoding="utf-8")
    assert "[ValidateSet('check', 'build')]" in source
    assert "cargo.exe') cargo check" not in source
    assert "--bundles $Bundle" in source
