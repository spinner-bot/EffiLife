from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VIEW = (ROOT / "time-helper" / "desk" / "src" / "views" / "TaskCenterView.vue").read_text(encoding="utf-8")


def test_task_quick_create_uses_one_native_submit_path():
    create_block = VIEW.split('<form class="task-create theme-card"', 1)[1].split('</form>', 1)[0]

    assert '@submit.prevent="AudioManager.playSound(\'click\'); addTodo()"' in create_block
    assert '<button type="submit" class="task-add"' in create_block
    assert '@keyup.enter="addTodo"' not in create_block
    assert create_block.count("addTodo()") == 1
