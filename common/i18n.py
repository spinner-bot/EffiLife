"""EffiLife 多语言基础设施。

当前提供无依赖的服务端/共享层翻译能力。前端可以读取同一套 JSON 资源，
各模块不再需要自行约定 locale、回退和参数插值规则。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping


DEFAULT_LOCALE = "zh-CN"
LOCALE_FALLBACKS: dict[str, str] = {
    "zh-CN": "zh-CN",
    "en-US": "zh-CN",
}


class I18n:
    """带默认回退的轻量翻译目录。"""

    def __init__(self, locale: str = DEFAULT_LOCALE, catalog_dir: str | Path | None = None):
        self.catalog_dir = Path(catalog_dir) if catalog_dir else Path(__file__).parent / "locales"
        self.catalogs: dict[str, dict[str, Any]] = {}
        self.locale = DEFAULT_LOCALE
        self.load_catalogs()
        self.set_locale(locale)

    def load_catalogs(self) -> None:
        self.catalogs = {}
        if not self.catalog_dir.exists():
            return
        for path in sorted(self.catalog_dir.glob("*.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, UnicodeDecodeError, json.JSONDecodeError):
                continue
            if isinstance(data, dict):
                self.catalogs[path.stem] = data

    def available_locales(self) -> list[str]:
        return sorted(self.catalogs)

    def set_locale(self, locale: str) -> str:
        candidate = str(locale or "").strip()
        if candidate not in self.catalogs:
            fallback = LOCALE_FALLBACKS.get(DEFAULT_LOCALE, DEFAULT_LOCALE)
            candidate = DEFAULT_LOCALE if DEFAULT_LOCALE in self.catalogs else fallback
        self.locale = candidate
        return self.locale

    @staticmethod
    def _lookup(catalog: Mapping[str, Any], key: str) -> Any:
        value: Any = catalog
        for part in str(key).split("."):
            if not isinstance(value, Mapping) or part not in value:
                return None
            value = value[part]
        return value

    def translate(self, key: str, locale: str | None = None, **params: Any) -> str:
        requested = locale or self.locale
        value = self._lookup(self.catalogs.get(requested, {}), key)
        fallback = LOCALE_FALLBACKS.get(requested, DEFAULT_LOCALE)
        if value is None and requested != fallback:
            value = self._lookup(self.catalogs.get(fallback, {}), key)
        if value is None:
            value = key
        if not isinstance(value, str):
            return str(value)
        try:
            return value.format(**params)
        except (KeyError, IndexError, ValueError):
            return value

    def t(self, key: str, **params: Any) -> str:
        return self.translate(key, **params)
