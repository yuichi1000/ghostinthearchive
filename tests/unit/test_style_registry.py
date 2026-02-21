"""Unit tests for style_registry."""

from mystery_agents.tools.style_registry import (
    ArtStyle,
    CONTENT_TYPE_FACT,
    CONTENT_TYPE_FOLKLORE,
    FALLBACK_REGION,
    get_all_regions,
    get_art_style,
    get_style_description,
)


class TestGetArtStyle:
    """get_art_style の正常系テスト。"""

    def test_us_fact(self):
        """US + fact → B&W 銀塩写真スタイル。"""
        style = get_art_style("US", "fact")
        assert isinstance(style, ArtStyle)
        assert style.region == "US"
        assert style.content_type == "fact"
        assert "silver gelatin" in style.style_prefix.lower()

    def test_us_folklore(self):
        """US + folklore → アメリカ木版画スタイル。"""
        style = get_art_style("US", "folklore")
        assert style.region == "US"
        assert style.content_type == "folklore"
        assert "woodcut" in style.style_prefix.lower()

    def test_jp_fact(self):
        """JP + fact → 明治アルビュメンプリント。"""
        style = get_art_style("JP", "fact")
        assert style.region == "JP"
        assert "meiji" in style.style_prefix.lower() or "albumen" in style.style_prefix.lower()

    def test_jp_folklore(self):
        """JP + folklore → 浮世絵スタイル。"""
        style = get_art_style("JP", "folklore")
        assert style.region == "JP"
        assert "ukiyo" in style.style_prefix.lower()

    def test_gb_fact(self):
        """GB + fact → ヴィクトリア湿板写真。"""
        style = get_art_style("GB", "fact")
        assert style.region == "GB"
        assert "victorian" in style.style_prefix.lower() or "wet plate" in style.style_prefix.lower()

    def test_gb_folklore(self):
        """GB + folklore → ゴシック・ペン画。"""
        style = get_art_style("GB", "folklore")
        assert style.region == "GB"
        assert "gothic" in style.style_prefix.lower()

    def test_nl_fact(self):
        """NL + fact → オランダ黄金時代油彩。"""
        style = get_art_style("NL", "fact")
        assert style.region == "NL"
        assert "dutch golden age" in style.style_prefix.lower() or "vermeer" in style.style_prefix.lower()

    def test_nl_folklore(self):
        """NL + folklore → フランドル写本装飾。"""
        style = get_art_style("NL", "folklore")
        assert style.region == "NL"
        assert "flemish" in style.style_prefix.lower()

    def test_au_fact(self):
        """AU + fact → 植民地リトグラフ。"""
        style = get_art_style("AU", "fact")
        assert style.region == "AU"
        assert "colonial" in style.style_prefix.lower() or "lithograph" in style.style_prefix.lower()

    def test_au_folklore(self):
        """AU + folklore → ブッシュ風景エッチング。"""
        style = get_art_style("AU", "folklore")
        assert style.region == "AU"
        assert "bush" in style.style_prefix.lower() or "etching" in style.style_prefix.lower()

    def test_nz_fact(self):
        """NZ + fact → 植民地測量写真。"""
        style = get_art_style("NZ", "fact")
        assert style.region == "NZ"

    def test_nz_folklore(self):
        """NZ + folklore → 在来植物風景エッチング。"""
        style = get_art_style("NZ", "folklore")
        assert style.region == "NZ"

    def test_de_fact(self):
        """DE + fact → ダゲレオタイプ。"""
        style = get_art_style("DE", "fact")
        assert style.region == "DE"
        assert "daguerreotype" in style.style_prefix.lower()

    def test_de_folklore(self):
        """DE + folklore → ドイツ表現主義木版画。"""
        style = get_art_style("DE", "folklore")
        assert style.region == "DE"
        assert "expressionist" in style.style_prefix.lower()

    def test_fr_fact(self):
        """FR + fact → アジェ風ドキュメンタリー写真。"""
        style = get_art_style("FR", "fact")
        assert style.region == "FR"
        assert "atget" in style.style_prefix.lower()

    def test_fr_folklore(self):
        """FR + folklore → アール・ヌーヴォー。"""
        style = get_art_style("FR", "folklore")
        assert style.region == "FR"
        assert "art nouveau" in style.style_prefix.lower()

    def test_es_fact(self):
        """ES + fact → 宮廷肖像エッチング。"""
        style = get_art_style("ES", "fact")
        assert style.region == "ES"

    def test_es_folklore(self):
        """ES + folklore → ゴヤ・カプリチョス風。"""
        style = get_art_style("ES", "folklore")
        assert style.region == "ES"
        assert "goya" in style.style_prefix.lower() or "caprichos" in style.style_prefix.lower()

    def test_pt_fact(self):
        """PT + fact → 大航海時代海図。"""
        style = get_art_style("PT", "fact")
        assert style.region == "PT"
        assert "nautical" in style.style_prefix.lower() or "exploration" in style.style_prefix.lower()

    def test_pt_folklore(self):
        """PT + folklore → 海洋エングレービング。"""
        style = get_art_style("PT", "folklore")
        assert style.region == "PT"
        assert "maritime" in style.style_prefix.lower() or "engraving" in style.style_prefix.lower()

    def test_eu_fact(self):
        """EU + fact → カルト・ド・ヴィジット。"""
        style = get_art_style("EU", "fact")
        assert style.region == "EU"
        assert "carte de visite" in style.style_prefix.lower()

    def test_eu_folklore(self):
        """EU + folklore → ルネサンス銅版画。"""
        style = get_art_style("EU", "folklore")
        assert style.region == "EU"
        assert "renaissance" in style.style_prefix.lower() or "copperplate" in style.style_prefix.lower()


class TestGetArtStyleFallback:
    """フォールバック動作のテスト。"""

    def test_unknown_region_falls_back_to_eu(self):
        """不明リージョンは EU にフォールバック。"""
        style = get_art_style("XX", "fact")
        assert style.region == FALLBACK_REGION
        assert style.content_type == "fact"

    def test_unknown_region_folklore_falls_back_to_eu(self):
        """不明リージョン + folklore → EU folklore。"""
        style = get_art_style("ZZ", "folklore")
        assert style.region == FALLBACK_REGION
        assert style.content_type == "folklore"

    def test_invalid_content_type_falls_back_to_fact(self):
        """不正 content_type → fact にフォールバック。"""
        style = get_art_style("US", "invalid")
        assert style.content_type == "fact"

    def test_empty_content_type_falls_back_to_fact(self):
        """空 content_type → fact にフォールバック。"""
        style = get_art_style("JP", "")
        assert style.content_type == "fact"

    def test_case_insensitive_region(self):
        """小文字リージョンも正しく解決される。"""
        style = get_art_style("jp", "fact")
        assert style.region == "JP"


class TestGetAllRegions:
    """get_all_regions のテスト。"""

    def test_returns_11_regions(self):
        """11リージョンを返す。"""
        regions = get_all_regions()
        assert len(regions) == 11

    def test_includes_all_expected_regions(self):
        """全リージョンコードが含まれる。"""
        regions = get_all_regions()
        expected = {"US", "JP", "GB", "NL", "AU", "NZ", "DE", "FR", "ES", "PT", "EU"}
        assert set(regions) == expected

    def test_sorted(self):
        """ソート済みで返る。"""
        regions = get_all_regions()
        assert regions == sorted(regions)


class TestGetStyleDescription:
    """get_style_description のテスト。"""

    def test_returns_non_empty_string(self):
        """全リージョン×タイプで空でない説明文を返す。"""
        for region in get_all_regions():
            for ct in ("fact", "folklore"):
                desc = get_style_description(region, ct)
                assert isinstance(desc, str)
                assert len(desc) > 10


class TestArtStyleAttributes:
    """ArtStyle dataclass の属性テスト。"""

    def test_has_negative_prompt(self):
        """全スタイルが negative_prompt を持つ。"""
        for region in get_all_regions():
            for ct in ("fact", "folklore"):
                style = get_art_style(region, ct)
                assert style.negative_prompt
                assert len(style.negative_prompt) > 5

    def test_style_prefix_ends_with_space(self):
        """style_prefix はスペースで終わる（プロンプト連結時の都合）。"""
        for region in get_all_regions():
            for ct in ("fact", "folklore"):
                style = get_art_style(region, ct)
                assert style.style_prefix.endswith(" "), f"{region}/{ct}: style_prefix should end with space"

    def test_frozen_dataclass(self):
        """ArtStyle は frozen（不変）。"""
        style = get_art_style("US", "fact")
        try:
            style.region = "XX"  # type: ignore[misc]
            assert False, "Should have raised FrozenInstanceError"
        except AttributeError:
            pass
