from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VIEW = (ROOT / "time-helper" / "desk" / "src" / "views" / "TaskCenterView.vue").read_text(encoding="utf-8")


def test_category_mutations_share_a_busy_lock_and_release_it_on_failure():
    assert "const categoryMutationKey = ref<string | null>(null)" in VIEW
    assert "if (!categoryName.value.trim() || categoryMutationKey.value) return" in VIEW
    assert "if (categoryMutationKey.value) return" in VIEW
    assert VIEW.count("categoryMutationKey.value = null") >= 4


def test_category_manager_disables_conflicting_actions_while_mutating():
    manager = VIEW.split('<section v-if="showCategoryManager"', 1)[1]
    assert ':disabled="!categoryName.trim() || !!categoryMutationKey"' in manager
    assert ':disabled="!!categoryMutationKey"' in manager
    assert ':disabled="confirmationPending || !!categoryMutationKey"' in manager
