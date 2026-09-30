from pathlib import Path


SOURCE = (Path(__file__).resolve().parents[1] / "time-helper/desk/src/guide/GuideOverlay.vue").read_text(encoding="utf-8")


def test_guide_skip_uses_themed_confirm_service():
    assert "import { requestConfirm } from '@/services/confirmService'" in SOURCE
    assert "async function skipGuide()" in SOURCE
    assert "await requestConfirm(t('guide.skipConfirm'))" in SOURCE
    assert "if (confirm(t('guide.skipConfirm')))" not in SOURCE
