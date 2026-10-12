from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VIEW = (ROOT / "time-helper" / "desk" / "src" / "views" / "EventManagerView.vue").read_text(encoding="utf-8")


def test_event_rule_modal_has_dialog_close_and_focus_management():
    assert 'ref="ruleModal"' in VIEW
    assert 'role="dialog"' in VIEW
    assert 'aria-modal="true"' in VIEW
    assert 'aria-labelledby="event-rule-modal-title"' in VIEW
    assert 'class="modal-close"' in VIEW
    assert '@keydown="onRuleModalKeydown"' in VIEW
    assert "if (event.key === 'Escape')" in VIEW
    assert "ruleReturnTarget" in VIEW
    assert "ruleModal.value?.querySelector<HTMLElement>('input, button')?.focus()" in VIEW


def test_event_rule_modal_close_label_exists_in_both_locales():
    i18n = (ROOT / "time-helper" / "desk" / "src" / "i18n" / "index.ts").read_text(encoding="utf-8")

    assert "'settings.close': '关闭'" in i18n
    assert "'settings.close': 'Close'" in i18n
