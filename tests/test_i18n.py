from common import LOCALE_FALLBACKS
from common.i18n import I18n


def test_i18n_locale_fallback_and_interpolation():
    i18n = I18n("en-US")
    assert i18n.t("navigation.tasks") == "Tasks"
    assert i18n.t("missing.key") == "missing.key"
    assert i18n.translate("common.loading", "zh-CN") != "common.loading"

    i18n.set_locale("missing-locale")
    assert i18n.locale == "zh-CN"
    assert i18n.t("navigation.today") != "navigation.today"


def test_i18n_fallback_registry_matches_frontend_semantics(tmp_path):
    assert LOCALE_FALLBACKS == {"zh-CN": "zh-CN", "en-US": "zh-CN"}
    (tmp_path / "zh-CN.json").write_text(
        '{"only_zh": "ZH only", "shared": "ZH shared"}', encoding="utf-8"
    )
    (tmp_path / "en-US.json").write_text(
        '{"only_en": "English", "shared": "English version"}', encoding="utf-8"
    )

    i18n = I18n("en-US", catalog_dir=tmp_path)

    assert i18n.t("only_zh") == "ZH only"
    assert i18n.t("shared") == "English version"
    assert i18n.translate("only_zh", "unknown-locale") == "ZH only"
