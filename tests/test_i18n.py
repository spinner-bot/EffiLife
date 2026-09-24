from common.i18n import I18n


def test_i18n_locale_fallback_and_interpolation():
    i18n = I18n("en-US")
    assert i18n.t("navigation.tasks") == "Tasks"
    assert i18n.t("missing.key") == "missing.key"
    assert i18n.translate("common.loading", "zh-CN") == "加载中…"

    i18n.set_locale("missing-locale")
    assert i18n.locale == "zh-CN"
    assert i18n.t("navigation.today") == "今日"
