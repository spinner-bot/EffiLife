import copy
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLAN_HELPER = ROOT / "plan-helper"
if str(PLAN_HELPER) not in sys.path:
    sys.path.insert(0, str(PLAN_HELPER))

from modules.template import (  # noqa: E402
    TEMPLATES,
    localized_builtin_template,
)


def test_english_builtin_template_is_a_deep_localized_copy():
    original = copy.deepcopy(TEMPLATES["workday"])
    localized = localized_builtin_template("workday", TEMPLATES["workday"], "en-US")

    assert localized["name"] == "Workday plan"
    assert localized["sections"][0]["name"] == "Morning - Deep work"
    assert localized["sections"][0]["tasks"][0]["content"] == "Morning planning and review"
    assert localized["sections"][0]["groups"][0]["title"] == "Morning deep work"
    assert TEMPLATES["workday"] == original


def test_unknown_locale_and_custom_template_shape_keep_original_text():
    template = {"name": "用户模板", "sections": [{"name": "自定义分组", "tasks": []}]}
    assert localized_builtin_template("workday", TEMPLATES["workday"], "zh-CN")["name"] == "工作日计划"
    assert localized_builtin_template("custom", template, "en-US") == template


def test_template_http_route_forwards_optional_locale():
    server = (PLAN_HELPER / "web/server.py").read_text(encoding="utf-8")
    assert "locale=data.get(\"locale\")" in server
    spec = (PLAN_HELPER / "docs/API_SPEC.md").read_text(encoding="utf-8")
    assert "POST /api/plans/from-template" in spec
    assert "Creation language for built-in content" in spec
