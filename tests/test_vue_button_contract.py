import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VUE_ROOT = ROOT / "time-helper" / "desk" / "src"


def test_all_vue_buttons_declare_an_explicit_button_type():
    opening_button = re.compile(r"<button\b[\s\S]*?>")
    missing_type = []
    for path in VUE_ROOT.rglob("*.vue"):
        # Vue directives may contain arrow functions such as `item => item.id`;
        # normalize that token so the lightweight tag scanner does not mistake
        # its `>` for the end of the opening element.
        source = path.read_text(encoding="utf-8").replace("=>", "__VUE_ARROW__")
        source = re.sub(r"\s>\s", " __VUE_GT__ ", source)
        for match in opening_button.finditer(source):
            if not re.search(r"\btype\s*=", match.group(0)):
                missing_type.append(f"{path}:{source.count(chr(10), 0, match.start()) + 1}")
    assert not missing_type, "Buttons without explicit type: " + ", ".join(missing_type)
