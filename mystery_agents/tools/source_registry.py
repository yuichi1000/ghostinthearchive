"""アーカイブソースの動的レジストリ。

各 API ツールファイル末尾で register_source() を呼び出し、
ArchiveSource インスタンスを自動登録する。
Source Router は Registry を動的にスキャンして言語に応じたソースを解決する。
"""

from __future__ import annotations

import importlib
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .archive_source_base import ArchiveSource

logger = logging.getLogger(__name__)

# ソースレジストリ（source_key → ArchiveSource インスタンス）
_registry: dict[str, ArchiveSource] = {}

# 全モジュールのロード済みフラグ
_all_loaded = False

# 登録対象の API ツールモジュール（パッケージ内の相対パス）
_SOURCE_MODULES = [
    "mystery_agents.tools.loc_digital",
    "mystery_agents.tools.dpla",
    "mystery_agents.tools.nypl_digital",
    "mystery_agents.tools.internet_archive",
    "mystery_agents.tools.ddb",
    "mystery_agents.tools.europeana",
    "mystery_agents.tools.chronicling_america",
    "mystery_agents.tools.trove",
    "mystery_agents.tools.delpher",
    "mystery_agents.tools.ndl_search",
    "mystery_agents.tools.wellcome_collection",
    "mystery_agents.tools.digitalnz",
]


def register_source(source: ArchiveSource) -> None:
    """ソースをレジストリに登録する。"""
    if source.source_key in _registry:
        logger.warning("ソース '%s' は既に登録済み（上書き）", source.source_key)
    _registry[source.source_key] = source
    logger.debug("ソース登録: %s (%s)", source.source_key, source.source_name)


def get_source(key: str) -> ArchiveSource | None:
    """source_key でソースを取得する。"""
    ensure_all_loaded()
    return _registry.get(key)


def get_all_sources() -> dict[str, ArchiveSource]:
    """全登録ソースを返す。"""
    ensure_all_loaded()
    return dict(_registry)


def resolve_sources(lang_code: str) -> list[ArchiveSource]:
    """言語コードに対応するソースを動的に解決する。

    各 ArchiveSource の supported_languages を参照し、
    指定言語を含むソースのリストを返す。

    Args:
        lang_code: ISO 639-1 言語コード（例: "en", "de"）

    Returns:
        対応するソースのリスト
    """
    ensure_all_loaded()
    return [
        source
        for source in _registry.values()
        if lang_code in source.supported_languages
    ]


def resolve_newspaper_sources(lang_code: str) -> list[ArchiveSource]:
    """言語コードに対応する新聞ソースを解決する。"""
    return [
        source
        for source in resolve_sources(lang_code)
        if source.is_newspaper_source
    ]


def ensure_all_loaded() -> None:
    """全 API ツールモジュールを import してソース登録を確実にする。

    モジュールが既に import 済みでも、_instance 変数からソースを再登録する。
    これにより _reset_registry() 後のテストでも正しく動作する。
    """
    global _all_loaded
    if _all_loaded:
        return
    for module_path in _SOURCE_MODULES:
        try:
            mod = importlib.import_module(module_path)
            # モジュールの _instance 変数から自動登録（再 import 時の対策）
            instance = getattr(mod, "_instance", None)
            if instance is not None and instance.source_key not in _registry:
                register_source(instance)
        except ImportError as e:
            logger.warning("モジュール %s のロード失敗: %s", module_path, e)
    _all_loaded = True


def _reset_registry() -> None:
    """テスト用: レジストリをリセットする。"""
    global _all_loaded
    _registry.clear()
    _all_loaded = False
