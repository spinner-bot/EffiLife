from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "tauri-mobile-boundary.yml"


def test_mobile_boundary_workflow_runs_configuration_and_frontend_contracts():
    source = WORKFLOW.read_text(encoding="utf-8")
    assert "cancel-in-progress: true" in source
    assert "effilife-mobile-boundary-${{ github.ref }}" in source
    assert "python scripts/check_mobile_release_config.py" in source
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
    assert workflow.count("timeout-minutes: 45") == 2
    assert workflow.count("actions/setup-python@v6") == 2
    assert workflow.count("python -m pip install --disable-pip-version-check pytest") == 2
    assert workflow.count("python scripts/check_mobile_release_config.py") == 2
    assert workflow.count("tests/test_mobile_build_scripts.py tests/test_mobile_release_config.py tests/test_mobile_workflow.py") == 2
    assert workflow.count("name: Build shared mobile frontend") == 2
    assert workflow.count("python scripts/build_frontend.py") == 2
    assert "npm run tauri -- android init --ci --skip-targets-install --config src-tauri/tauri.mobile.conf.json" in workflow
    assert "python scripts/check_build_environment.py --target android" in workflow
    assert "npm run mobile:android:build" in workflow
    assert "actions/upload-artifact@v4" in workflow
    assert "gen/android/app/build/outputs/apk/**/*.apk" in workflow
    assert "python scripts/verify_mobile_artifacts.py" in workflow
    assert "--target android" in workflow
    assert "python scripts/generate_checksums.py" in workflow
    assert "release-checksums/EffiLife-android.sha256" in workflow
    assert "python scripts/generate_release_manifest.py" in workflow
    assert "release-checksums/EffiLife-android.manifest.json" in workflow
    assert "npm run tauri -- ios init --ci --skip-targets-install --config src-tauri/tauri.mobile.conf.json" in workflow
    assert "python scripts/check_build_environment.py --target ios" in workflow
    assert "npm run mobile:ios:build -- --debug" in workflow
    assert "gen/apple/build/**/*.app" in workflow
    assert "--target ios" in workflow
    assert "release-checksums/EffiLife-ios.sha256" in workflow
    assert "release-checksums/EffiLife-ios.manifest.json" in workflow
    assert workflow.count("--version-file time-helper/VERSION") == 4


def test_mobile_build_workflow_does_not_use_desktop_sidecar():
    workflow = (ROOT / ".github" / "workflows" / "tauri-mobile-build.yml").read_text(encoding="utf-8")
    assert "build:sidecar" not in workflow
    assert "tauri-desktop-release" not in workflow
