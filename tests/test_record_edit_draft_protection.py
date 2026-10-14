from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VIEW = (ROOT / "time-helper" / "desk" / "src" / "views" / "RecordsView.vue").read_text(encoding="utf-8")
I18N = (ROOT / "time-helper" / "desk" / "src" / "i18n" / "index.ts").read_text(encoding="utf-8")


def test_time_record_form_protects_unsaved_changes():
    assert "import { onBeforeRouteLeave, useRoute, useRouter } from 'vue-router'" in VIEW
    assert "const recordInitialDraft = ref('')" in VIEW
    assert "function currentRecordDraft(): string" in VIEW
    assert "function isRecordDraftDirty(): boolean" in VIEW
    assert "async function closeForm(force = false): Promise<void>" in VIEW
    assert "t('records.discardEditConfirm')" in VIEW
    assert '@click.self="void closeForm()"' in VIEW
    assert '@click="void closeForm()"' in VIEW
    assert "await closeForm(true)" in VIEW
    assert "onBeforeRouteLeave(async () =>" in VIEW


def test_time_record_discard_confirmation_is_localized():
    assert "'records.discardEditConfirm': '当前时间记录有未保存的修改，确定放弃吗？'" in I18N
    assert "'records.discardEditConfirm': 'This time record has unsaved changes. Discard them?'" in I18N
