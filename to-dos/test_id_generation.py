import tempfile
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src import TodoAPI


def test_todo_ids_remain_unique_after_storage_reload():
    with tempfile.TemporaryDirectory() as data_dir:
        first = TodoAPI(data_dir).create_todo(title="first")
        second = TodoAPI(data_dir).create_todo(title="second")

        assert first["success"] and second["success"]
        assert first["data"]["id"] != second["data"]["id"]
        assert second["data"]["id"].endswith("0002")
