from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/ci.yml"


def test_general_ci_runs_on_main_push_and_pull_request():
    source = WORKFLOW.read_text(encoding="utf-8")
    assert "branches: [main]" in source
    assert "pull_request:" in source
    assert "workflow_dispatch:" in source


def test_general_ci_covers_full_python_suite_and_desktop_build():
    source = WORKFLOW.read_text(encoding="utf-8")
    assert "python -m pytest -q" in source
    assert "python scripts/check_release_config.py" in source
    assert "python scripts/check_mobile_release_config.py" in source
    assert "working-directory: time-helper/desk" in source
    assert "run: npm ci" in source
    assert "python scripts/build_todos_ui.py" in source
    assert "working-directory: to-dos/ui" in source


def test_general_ci_runs_the_unified_workspace_startup_smoke_check():
    source = WORKFLOW.read_text(encoding="utf-8")
    assert "python scripts/smoke_startup.py" in source
    assert source.index("python scripts/smoke_startup.py") > source.index("python scripts/run_integration.py test")


def test_general_ci_collects_launcher_diagnostics_after_failures():
    source = WORKFLOW.read_text(encoding="utf-8")
    assert "if: ${{ failure() }}" in source
    assert "python launcher/start.py --diagnose > ci-launcher-diagnostics.json" in source
    assert "actions/upload-artifact@v4" in source
    assert "effilife-ci-diagnostics-${{ github.run_id }}" in source


def test_general_ci_uses_pinned_current_action_majors_and_cancellation():
    source = WORKFLOW.read_text(encoding="utf-8")
    assert "actions/checkout@v5" in source
    assert "actions/setup-python@v6" in source
    assert "actions/setup-node@v5" in source
    assert "cancel-in-progress: true" in source
