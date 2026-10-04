import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
I18N_SOURCE = ROOT / "time-helper" / "desk" / "src" / "i18n" / "index.ts"


def _catalog_keys(locale: str, source: str) -> set[str]:
    if locale == "zh-CN":
        match = re.search(r"'zh-CN':\s*\{(?P<body>.*?)\n  \},\n  'en-US':", source, re.S)
    else:
        match = re.search(r"'en-US':\s*\{(?P<body>.*?)\n  \},\n\}", source, re.S)
    assert match is not None, f"missing {locale} catalog"
    return set(re.findall(r"^\s*'([^']+)':", match.group("body"), re.M))


def test_frontend_locale_catalogs_have_matching_keys():
    source = I18N_SOURCE.read_text(encoding="utf-8")
    zh_keys = _catalog_keys("zh-CN", source)
    en_keys = _catalog_keys("en-US", source)

    assert zh_keys == en_keys, (
        f"frontend locale catalogs differ: "
        f"missing in zh-CN={sorted(en_keys - zh_keys)}, "
        f"missing in en-US={sorted(zh_keys - en_keys)}"
    )


def test_generic_form_validation_messages_are_registered_in_both_locales():
    source = (ROOT / "time-helper" / "desk" / "src" / "i18n" / "index.ts").read_text(encoding="utf-8")
    for key in (
        "validation.required",
        "validation.minString",
        "validation.minNumber",
        "validation.maxString",
        "validation.maxNumber",
        "validation.pattern",
        "validation.invalid",
    ):
        assert source.count(f"'{key}':") == 2
