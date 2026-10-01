from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _workflow(name: str) -> str:
    return (ROOT / ".github" / "workflows" / name).read_text(encoding="utf-8")


def test_main_ci_syncs_lock_metadata_before_frontend_install():
    workflow = _workflow("ci.yml")
    assert "python scripts/sync_desktop_version.py" in workflow
    assert workflow.index("python scripts/sync_desktop_version.py") < workflow.index("working-directory: time-helper/desk")
    assert workflow.index("python scripts/sync_desktop_version.py") < workflow.index("run: npm ci")


def test_mobile_boundary_syncs_lock_metadata_before_frontend_install():
    workflow = _workflow("tauri-mobile-boundary.yml")
    assert "python scripts/sync_desktop_version.py" in workflow
    assert workflow.index("python scripts/sync_desktop_version.py") < workflow.index("run: npm ci")


def test_manual_mobile_build_syncs_each_platform_job_before_npm_ci():
    workflow = _workflow("tauri-mobile-build.yml")
    for job in ("\n  android:", "\n  ios:"):
        job_source = workflow.split(job, 1)[1]
        assert "python scripts/sync_desktop_version.py" in job_source
        assert job_source.index("python scripts/sync_desktop_version.py") < job_source.index("uses: actions/setup-node@v5")
        assert job_source.index("python scripts/sync_desktop_version.py") < job_source.index("run: npm ci")


def test_ci_runs_the_real_unified_cross_module_integration_suite():
    workflow = _workflow("ci.yml")
    assert "python scripts/run_integration.py test" in workflow
    assert workflow.index("python scripts/run_integration.py test") > workflow.index("run: python -m pytest -q")


def test_desktop_release_runs_the_real_unified_cross_module_integration_suite():
    workflow = _workflow("tauri-desktop-release.yml")
    assert "python scripts/run_integration.py test" in workflow
    assert workflow.index("python scripts/run_integration.py test") > workflow.index("run: python -m pytest -q")
