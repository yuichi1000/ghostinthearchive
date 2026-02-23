"""Unit tests for merch_agents/tools/design_tools.py - save_design_proposal."""

import json

from merch_agents.tools.design_tools import save_design_proposal
from tests.fakes import make_tool_context


class TestSaveDesignProposal:
    """Tests for save_design_proposal()."""

    def _make_valid_proposal(self) -> dict:
        return {
            "products": [
                {
                    "product_type": "tshirt",
                    "aspect_ratio": "1:1",
                    "catchphrase_en": "Whispers from the Archive",
                    "catchphrase_ja": "アーカイブからの囁き",
                    "color_palette": ["#1a1a2e", "#16213e", "#d4af37"],
                    "font_suggestion": "Playfair Display, serif, 700",
                    "composition": "Center-focused mandala pattern with archive motifs",
                    "imagen_prompts": {
                        "background": "Dark mandala pattern with golden archive motifs, vintage paper texture",
                        "decorative": "Ornate golden border with quill and scroll elements",
                    },
                    "style_reference": "fact",
                    "negative_prompt": "people, faces, text",
                },
                {
                    "product_type": "mug",
                    "aspect_ratio": "16:9",
                    "catchphrase_en": "Ghost in Every Page",
                    "catchphrase_ja": "全てのページに潜むゴースト",
                    "color_palette": ["#0f3460", "#533483", "#e94560"],
                    "font_suggestion": "Crimson Text, serif, 600",
                    "composition": "Panoramic archive corridor fading into mist",
                    "imagen_prompts": {
                        "background": "Misty library corridor with floating spectral pages",
                    },
                    "style_reference": "folklore",
                    "negative_prompt": "people, faces",
                },
            ],
        }

    def test_saves_to_session_state(self):
        """正常な JSON を session state に保存する。"""
        proposal = self._make_valid_proposal()
        ctx = make_tool_context()

        result = save_design_proposal(json.dumps(proposal), ctx)
        result_data = json.loads(result)

        assert result_data["status"] == "success"
        assert "structured_design_proposal" in ctx.state
        assert ctx.state["structured_design_proposal"] == proposal

    def test_returns_product_count(self):
        """製品数を返す。"""
        proposal = self._make_valid_proposal()
        ctx = make_tool_context()

        result = save_design_proposal(json.dumps(proposal), ctx)
        result_data = json.loads(result)

        assert result_data["product_count"] == 2

    def test_returns_product_types(self):
        """製品タイプのリストを返す。"""
        proposal = self._make_valid_proposal()
        ctx = make_tool_context()

        result = save_design_proposal(json.dumps(proposal), ctx)
        result_data = json.loads(result)

        assert result_data["product_types"] == ["tshirt", "mug"]

    def test_invalid_json_returns_error(self):
        """不正な JSON はエラーを返す。"""
        ctx = make_tool_context()

        result = save_design_proposal("not valid json {", ctx)
        result_data = json.loads(result)

        assert result_data["status"] == "error"
        assert "Invalid JSON" in result_data["error"]
        assert "structured_design_proposal" not in ctx.state

    def test_missing_products_returns_error(self):
        """products がない場合はエラーを返す。"""
        ctx = make_tool_context()

        result = save_design_proposal(json.dumps({"other": "data"}), ctx)
        result_data = json.loads(result)

        assert result_data["status"] == "error"
        assert "products" in result_data["error"]

    def test_empty_products_returns_error(self):
        """products が空配列の場合はエラーを返す。"""
        ctx = make_tool_context()

        result = save_design_proposal(json.dumps({"products": []}), ctx)
        result_data = json.loads(result)

        assert result_data["status"] == "error"
        assert "products" in result_data["error"]

    def test_warns_on_invalid_product_type(self):
        """不正な product_type で warning を含む。"""
        ctx = make_tool_context()
        proposal = self._make_valid_proposal()
        proposal["products"][0]["product_type"] = "poster"

        result = save_design_proposal(json.dumps(proposal), ctx)
        result_data = json.loads(result)

        assert result_data["status"] == "success"
        assert any("invalid product_type" in w for w in result_data["warnings"])

    def test_warns_on_empty_catchphrase_en(self):
        """catchphrase_en が空で warning を含む。"""
        ctx = make_tool_context()
        proposal = self._make_valid_proposal()
        proposal["products"][0]["catchphrase_en"] = ""

        result = save_design_proposal(json.dumps(proposal), ctx)
        result_data = json.loads(result)

        assert result_data["status"] == "success"
        assert any("catchphrase_en" in w for w in result_data["warnings"])

    def test_warns_on_empty_catchphrase_ja(self):
        """catchphrase_ja が空で warning を含む。"""
        ctx = make_tool_context()
        proposal = self._make_valid_proposal()
        proposal["products"][0]["catchphrase_ja"] = "  "

        result = save_design_proposal(json.dumps(proposal), ctx)
        result_data = json.loads(result)

        assert result_data["status"] == "success"
        assert any("catchphrase_ja" in w for w in result_data["warnings"])

    def test_warns_on_missing_color_palette(self):
        """color_palette がない場合に warning を含む。"""
        ctx = make_tool_context()
        proposal = self._make_valid_proposal()
        del proposal["products"][0]["color_palette"]

        result = save_design_proposal(json.dumps(proposal), ctx)
        result_data = json.loads(result)

        assert result_data["status"] == "success"
        assert any("color_palette" in w for w in result_data["warnings"])

    def test_warns_on_missing_imagen_prompts(self):
        """imagen_prompts がない場合に warning を含む。"""
        ctx = make_tool_context()
        proposal = self._make_valid_proposal()
        del proposal["products"][0]["imagen_prompts"]

        result = save_design_proposal(json.dumps(proposal), ctx)
        result_data = json.loads(result)

        assert result_data["status"] == "success"
        assert any("imagen_prompts" in w for w in result_data["warnings"])

    def test_warns_on_empty_imagen_background(self):
        """imagen_prompts.background が空で warning を含む。"""
        ctx = make_tool_context()
        proposal = self._make_valid_proposal()
        proposal["products"][0]["imagen_prompts"]["background"] = ""

        result = save_design_proposal(json.dumps(proposal), ctx)
        result_data = json.loads(result)

        assert result_data["status"] == "success"
        assert any("background" in w for w in result_data["warnings"])

    def test_warns_on_invalid_style_reference(self):
        """不正な style_reference で warning を含む。"""
        ctx = make_tool_context()
        proposal = self._make_valid_proposal()
        proposal["products"][0]["style_reference"] = "abstract"

        result = save_design_proposal(json.dumps(proposal), ctx)
        result_data = json.loads(result)

        assert result_data["status"] == "success"
        assert any("style_reference" in w for w in result_data["warnings"])

    def test_no_warnings_for_valid_proposal(self):
        """正常なプロポーザルでは warnings が空。"""
        ctx = make_tool_context()
        proposal = self._make_valid_proposal()

        result = save_design_proposal(json.dumps(proposal), ctx)
        result_data = json.loads(result)

        assert result_data["warnings"] == []

    def test_warns_on_non_dict_product(self):
        """products 要素が dict でない場合に warning を含む。"""
        ctx = make_tool_context()
        proposal = {"products": ["not_a_dict", self._make_valid_proposal()["products"][0]]}

        result = save_design_proposal(json.dumps(proposal), ctx)
        result_data = json.loads(result)

        assert result_data["status"] == "success"
        assert any("not a dict" in w for w in result_data["warnings"])
