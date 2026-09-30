from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
API = (ROOT / "plan-helper" / "modules" / "api.py").read_text(encoding="utf-8")
DATA = (ROOT / "plan-helper" / "modules" / "data.py").read_text(encoding="utf-8")
TEXT = (ROOT / "plan-helper" / "modules" / "text.py").read_text(encoding="utf-8")
TEMPLATE = (ROOT / "plan-helper" / "modules" / "template.py").read_text(encoding="utf-8")
PLAN = (ROOT / "plan-helper" / "modules" / "plan.py").read_text(encoding="utf-8")


def test_core_section_letter_conversion_supports_multi_character_modules():
    namespace: dict[str, object] = {}
    exec(compile(PLAN, "plan.py", "exec"), namespace)
    plan = namespace["Plan"]
    assert plan.num2char(0) == "A"
    assert plan.num2char(25) == "Z"
    assert plan.num2char(26) == "AA"
    assert plan.num2char(27) == "AB"


def test_all_python_section_renderers_reuse_core_conversion():
    assert "plan_module.Plan.num2char(i)" in API
    assert API.count("plan_module.Plan.num2char(sec_idx)") >= 2
    assert "plan_module.Plan.num2char(sec_idx)" in DATA
    assert "plan_module.Plan.num2char(sec_idx)" in TEXT
    assert "plan_module.Plan.num2char(sec_idx)" in TEMPLATE
    assert "chr(ord('A') + sec_idx)" not in "\n".join((API, DATA, TEXT, TEMPLATE))
