from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "tauri-mobile-boundary.yml"


def test_mobile_boundary_workflow_runs_configuration_and_frontend_contracts():
    source = WORKFLOW.read_text(encoding="utf-8")
    assert "cancel-in-progress: true" in source
    assert "timeout-minutes: 15" in source
    assert "effilife-mobile-boundary-${{ github.ref }}" in source
    assert "python scripts/check_mobile_release_config.py" in source
    assert "npm audit --audit-level=high --package-lock-only" in source
    assert "tests/test_mobile_build_scripts.py tests/test_mobile_release_config.py" in source
    assert "python scripts/build_frontend.py" in source


def test_mobile_boundary_workflow_does_not_claim_to_publish_installers():
    source = WORKFLOW.read_text(encoding="utf-8").lower()
    assert "upload-artifact" not in source
    assert "release create" not in source


def test_mobile_build_workflow_is_manual_and_builds_platform_artifacts():
    workflow = (ROOT / ".github" / "workflows" / "tauri-mobile-build.yml").read_text(encoding="utf-8")
    assert "workflow_dispatch:" in workflow
    assert "effilife-mobile-build-${{ github.ref }}-${{ inputs.target }}" in workflow
    assert "cancel-in-progress: false" in workflow
    assert "default: android" in workflow
    assert "          - android" in workflow
    assert "          - ios" not in workflow
    assert "  ios:" not in workflow
    assert workflow.count("timeout-minutes: 45") == 1
    assert workflow.count("actions/setup-python@v6") == 1
    assert workflow.count("python -m pip install --disable-pip-version-check pytest") == 1
    assert workflow.count("python scripts/check_mobile_release_config.py") == 1
    assert workflow.count("npm audit --audit-level=high --package-lock-only") == 1
    assert workflow.count("tests/test_mobile_build_scripts.py tests/test_mobile_release_config.py tests/test_mobile_workflow.py") == 1
    assert workflow.count("name: Build shared mobile frontend") == 1
    assert workflow.count("python scripts/build_frontend.py") == 1
    assert "npm run tauri -- android init --ci --skip-targets-install --config src-tauri/tauri.mobile.conf.json" in workflow
    assert "python scripts/check_build_environment.py --target android" in workflow
    assert "npm run mobile:android:build -- --split-per-abi" in workflow
    assert "actions/upload-artifact@v6" in workflow
    assert "gen/android/app/build/outputs/apk/**/*.apk" in workflow
    assert "python scripts/verify_mobile_artifacts.py" in workflow
    assert "--target android" in workflow
    assert "Sign Android APK for formal release" in workflow
    assert "EFFILIFE_ANDROID_KEYSTORE_BASE64" in workflow
    assert "python scripts/sign_android_artifact.py" in workflow
    assert 'mapfile -t unsigned_apks' in workflow
    assert 'test "${#unsigned_apks[@]}" -gt 0' in workflow
    assert 'for apk in "${unsigned_apks[@]}"; do' in workflow
    assert workflow.count('python scripts/sign_android_artifact.py') == 1
    assert "apksigner" in workflow
    assert "python scripts/generate_checksums.py" in workflow
    assert "release-checksums/EffiLife-android.sha256" in workflow
    assert "python scripts/generate_release_manifest.py" in workflow
    assert "release-checksums/EffiLife-android.manifest.json" in workflow
    assert "npm run tauri -- ios init --ci --skip-targets-install --config src-tauri/tauri.mobile.conf.json" not in workflow
    assert "python scripts/check_build_environment.py --target ios" not in workflow
    assert "npm run mobile:ios:build -- --debug" not in workflow
    assert "release-checksums/EffiLife-ios.sha256" not in workflow
    assert "release-checksums/EffiLife-ios.manifest.json" not in workflow
    assert workflow.count("--version-file time-helper/VERSION") == 2


def test_mobile_build_workflow_does_not_use_desktop_sidecar():
    workflow = (ROOT / ".github" / "workflows" / "tauri-mobile-build.yml").read_text(encoding="utf-8")
    assert "build:sidecar" not in workflow
    assert "tauri-desktop-release" not in workflow


def test_android_workflow_installs_the_sdk_and_ndk_versions_used_by_tauri():
    workflow = (ROOT / ".github/workflows/tauri-mobile-build.yml").read_text(encoding="utf-8")
    assert '"platforms;android-36"' in workflow
    assert '"build-tools;36.0.0"' in workflow
    assert '"ndk;25.2.9519653"' in workflow
