from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLANS = (ROOT / "time-helper/desk/src/views/PlansHubView.vue").read_text(encoding="utf-8")
I18N = (ROOT / "time-helper/desk/src/i18n/index.ts").read_text(encoding="utf-8")
SMOKE = (ROOT / "scripts/smoke_browser_workspace.py").read_text(encoding="utf-8")


def test_ph_creation_paths_expose_bilingual_success_feedback():
    assert PLANS.count("notifyToast(t('plans.created'), 'success')") == 2
    assert I18N.count("'plans.created':") == 2


def test_ph_browser_smoke_requires_creation_success_feedback():
    create_block = SMOKE.split('create_modal.locator("button.plans-primary").click', 1)[1].split(
        'page.wait_for_timeout(1000)', 1
    )[0]
    assert 'page.locator(".toast-success").wait_for(state="visible", timeout=3000)' in create_block
