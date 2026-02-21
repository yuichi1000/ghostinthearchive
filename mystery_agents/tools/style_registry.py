"""地域アートスタイルレジストリ。

(region, content_type) → ArtStyle のルックアップテーブル。
Illustrator が記事の地域に応じた画像スタイルを適用するために使用する。
"""

from dataclasses import dataclass

# コンテンツタイプ定数
CONTENT_TYPE_FACT = "fact"
CONTENT_TYPE_FOLKLORE = "folklore"

# フォールバックリージョン
FALLBACK_REGION = "EU"


@dataclass(frozen=True)
class ArtStyle:
    """画像生成スタイル定義。"""

    region: str  # ISO 3166-1 alpha-2
    content_type: str  # "fact" | "folklore"
    style_prefix: str  # Imagen プロンプトに付加
    negative_prompt: str
    description: str  # validate_image 用


# 11リージョン × 2タイプ = 22種
_STYLE_REGISTRY: dict[tuple[str, str], ArtStyle] = {
    # --- US: アメリカ ---
    ("US", CONTENT_TYPE_FACT): ArtStyle(
        region="US",
        content_type=CONTENT_TYPE_FACT,
        style_prefix=(
            "Black and white archival photograph style, monochrome, "
            "high contrast, vintage silver gelatin print texture, "
            "documentary photography aesthetic. "
        ),
        negative_prompt="color, modern elements, digital artifacts, cartoon, illustration",
        description="Black and white archival photograph, monochrome, silver gelatin print",
    ),
    ("US", CONTENT_TYPE_FOLKLORE): ArtStyle(
        region="US",
        content_type=CONTENT_TYPE_FOLKLORE,
        style_prefix=(
            "19th century American woodcut engraving illustration style, "
            "cross-hatching technique, sepia toned, aged paper texture, "
            "vintage newspaper illustration aesthetic. "
        ),
        negative_prompt="photograph, modern elements, digital art, 3D render, color photography",
        description="19th century American woodcut engraving, cross-hatching, sepia toned",
    ),
    # --- JP: 日本 ---
    ("JP", CONTENT_TYPE_FACT): ArtStyle(
        region="JP",
        content_type=CONTENT_TYPE_FACT,
        style_prefix=(
            "Meiji-era albumen print photograph style, sepia-toned monochrome, "
            "soft focus, faded edges, vintage Japanese documentary photography, "
            "hand-tinted details. "
        ),
        negative_prompt="modern elements, digital artifacts, cartoon, anime, bright colors",
        description="Meiji-era albumen print photograph, sepia-toned, soft focus, vintage Japanese photography",
    ),
    ("JP", CONTENT_TYPE_FOLKLORE): ArtStyle(
        region="JP",
        content_type=CONTENT_TYPE_FOLKLORE,
        style_prefix=(
            "Ukiyo-e woodblock print style, bold outlines, flat color areas, "
            "traditional Japanese color palette, washi paper texture, "
            "Edo-period artistic aesthetic. "
        ),
        negative_prompt="photograph, 3D render, realistic, modern elements, Western art style",
        description="Ukiyo-e woodblock print, bold outlines, traditional Japanese color palette",
    ),
    # --- GB: イギリス ---
    ("GB", CONTENT_TYPE_FACT): ArtStyle(
        region="GB",
        content_type=CONTENT_TYPE_FACT,
        style_prefix=(
            "Victorian wet plate collodion photograph style, monochrome, "
            "long exposure softness, dark vignetting, glass plate negative aesthetic, "
            "mid-19th century British documentary photography. "
        ),
        negative_prompt="color, modern elements, digital artifacts, sharp digital focus, cartoon",
        description="Victorian wet plate collodion photograph, monochrome, dark vignetting",
    ),
    ("GB", CONTENT_TYPE_FOLKLORE): ArtStyle(
        region="GB",
        content_type=CONTENT_TYPE_FOLKLORE,
        style_prefix=(
            "Gothic pen and ink illustration style, fine crosshatching, "
            "dark atmospheric shadows, Victorian book illustration aesthetic, "
            "intricate linework on aged vellum. "
        ),
        negative_prompt="photograph, modern elements, bright colors, digital art, 3D render",
        description="Gothic pen and ink illustration, fine crosshatching, Victorian book illustration",
    ),
    # --- NL: オランダ ---
    ("NL", CONTENT_TYPE_FACT): ArtStyle(
        region="NL",
        content_type=CONTENT_TYPE_FACT,
        style_prefix=(
            "Dutch Golden Age oil painting style, Vermeer-inspired lighting, "
            "rich chiaroscuro, warm amber tones, linen canvas texture, "
            "17th century Netherlandish realism. "
        ),
        negative_prompt="photograph, modern elements, digital art, flat colors, cartoon",
        description="Dutch Golden Age oil painting, Vermeer-inspired lighting, rich chiaroscuro",
    ),
    ("NL", CONTENT_TYPE_FOLKLORE): ArtStyle(
        region="NL",
        content_type=CONTENT_TYPE_FOLKLORE,
        style_prefix=(
            "Flemish manuscript illumination style, gold leaf accents, "
            "rich jewel-toned pigments, intricate border decorations, "
            "medieval Netherlandish book art aesthetic. "
        ),
        negative_prompt="photograph, modern elements, digital art, 3D render, monochrome",
        description="Flemish manuscript illumination, gold leaf accents, medieval Netherlandish book art",
    ),
    # --- AU: オーストラリア ---
    ("AU", CONTENT_TYPE_FACT): ArtStyle(
        region="AU",
        content_type=CONTENT_TYPE_FACT,
        style_prefix=(
            "Colonial-era lithograph style, hand-tinted stone print, "
            "muted earth tones, fine detail engraving, "
            "19th century Australian survey illustration aesthetic. "
        ),
        negative_prompt="photograph, modern elements, digital art, bright neon colors, cartoon",
        description="Colonial-era lithograph, hand-tinted stone print, Australian survey illustration",
    ),
    ("AU", CONTENT_TYPE_FOLKLORE): ArtStyle(
        region="AU",
        content_type=CONTENT_TYPE_FOLKLORE,
        style_prefix=(
            "Australian bush landscape etching style, fine line engraving, "
            "dramatic light and shadow, eucalyptus and outback scenery, "
            "colonial-era naturalist illustration aesthetic. "
        ),
        negative_prompt="photograph, modern elements, digital art, 3D render, urban setting",
        description="Australian bush landscape etching, fine line engraving, naturalist illustration",
    ),
    # --- NZ: ニュージーランド ---
    ("NZ", CONTENT_TYPE_FACT): ArtStyle(
        region="NZ",
        content_type=CONTENT_TYPE_FACT,
        style_prefix=(
            "Colonial survey photograph style, sepia-toned monochrome, "
            "frontier documentation aesthetic, early gelatin silver print, "
            "New Zealand landscape survey photography. "
        ),
        negative_prompt="color, modern elements, digital artifacts, cartoon, illustration",
        description="Colonial survey photograph, sepia-toned, New Zealand frontier documentation",
    ),
    ("NZ", CONTENT_TYPE_FOLKLORE): ArtStyle(
        region="NZ",
        content_type=CONTENT_TYPE_FOLKLORE,
        style_prefix=(
            "Native flora landscape etching style, botanical illustration technique, "
            "fine line engraving of fern forests and volcanic terrain, "
            "19th century New Zealand naturalist aesthetic. "
        ),
        negative_prompt="photograph, modern elements, digital art, 3D render, urban setting",
        description="Native flora landscape etching, botanical illustration, New Zealand naturalist",
    ),
    # --- DE: ドイツ ---
    ("DE", CONTENT_TYPE_FACT): ArtStyle(
        region="DE",
        content_type=CONTENT_TYPE_FACT,
        style_prefix=(
            "Daguerreotype photograph style, mirror-like silver surface, "
            "sharp central focus with soft edges, copper plate aesthetic, "
            "early 19th century German portrait photography. "
        ),
        negative_prompt="color, modern elements, digital artifacts, cartoon, illustration, paper texture",
        description="Daguerreotype photograph, mirror-like silver surface, early German photography",
    ),
    ("DE", CONTENT_TYPE_FOLKLORE): ArtStyle(
        region="DE",
        content_type=CONTENT_TYPE_FOLKLORE,
        style_prefix=(
            "German Expressionist woodcut print style, bold angular forms, "
            "stark black and white contrast, emotional intensity, "
            "Die Brücke movement aesthetic, rough-hewn linework. "
        ),
        negative_prompt="photograph, soft colors, realistic, digital art, smooth gradients",
        description="German Expressionist woodcut, bold angular forms, stark black and white contrast",
    ),
    # --- FR: フランス ---
    ("FR", CONTENT_TYPE_FACT): ArtStyle(
        region="FR",
        content_type=CONTENT_TYPE_FACT,
        style_prefix=(
            "Eugène Atget-style documentary photograph, matte albumen print, "
            "soft morning light, empty Parisian streets aesthetic, "
            "early 20th century French architectural photography. "
        ),
        negative_prompt="color, modern elements, digital artifacts, cartoon, illustration, people",
        description="Atget-style documentary photograph, matte albumen print, early French photography",
    ),
    ("FR", CONTENT_TYPE_FOLKLORE): ArtStyle(
        region="FR",
        content_type=CONTENT_TYPE_FOLKLORE,
        style_prefix=(
            "Art Nouveau illustration style, flowing organic lines, "
            "Mucha-inspired decorative borders, muted jewel tones, "
            "Belle Époque poster aesthetic, sinuous botanical motifs. "
        ),
        negative_prompt="photograph, modern elements, geometric shapes, 3D render, monochrome",
        description="Art Nouveau illustration, flowing organic lines, Belle Époque poster aesthetic",
    ),
    # --- ES: スペイン ---
    ("ES", CONTENT_TYPE_FACT): ArtStyle(
        region="ES",
        content_type=CONTENT_TYPE_FACT,
        style_prefix=(
            "Spanish court portrait etching style, fine intaglio engraving, "
            "formal composition, rich dark tones, copperplate line quality, "
            "Habsburg-era Iberian printmaking aesthetic. "
        ),
        negative_prompt="color photography, modern elements, digital art, cartoon, bright colors",
        description="Spanish court portrait etching, fine intaglio engraving, Habsburg-era printmaking",
    ),
    ("ES", CONTENT_TYPE_FOLKLORE): ArtStyle(
        region="ES",
        content_type=CONTENT_TYPE_FOLKLORE,
        style_prefix=(
            "Goya Los Caprichos-inspired aquatint style, dramatic tonal gradations, "
            "grotesque and fantastical elements, dark satirical atmosphere, "
            "Spanish Romantic printmaking aesthetic. "
        ),
        negative_prompt="photograph, modern elements, digital art, bright cheerful colors, 3D render",
        description="Goya Caprichos-inspired aquatint, dramatic tonal gradations, Spanish Romantic printmaking",
    ),
    # --- PT: ポルトガル ---
    ("PT", CONTENT_TYPE_FACT): ArtStyle(
        region="PT",
        content_type=CONTENT_TYPE_FACT,
        style_prefix=(
            "Age of Exploration nautical chart style, hand-drawn cartography, "
            "compass roses, sea monsters at margins, parchment background, "
            "Portuguese maritime illustration aesthetic. "
        ),
        negative_prompt="photograph, modern elements, digital art, 3D render, monochrome photograph",
        description="Age of Exploration nautical chart, hand-drawn cartography, Portuguese maritime illustration",
    ),
    ("PT", CONTENT_TYPE_FOLKLORE): ArtStyle(
        region="PT",
        content_type=CONTENT_TYPE_FOLKLORE,
        style_prefix=(
            "Maritime engraving illustration style, copper-line ship details, "
            "wave patterns in fine crosshatching, aged nautical document aesthetic, "
            "Portuguese Age of Discovery printmaking. "
        ),
        negative_prompt="photograph, modern elements, digital art, 3D render, bright colors",
        description="Maritime engraving, copper-line details, Portuguese Age of Discovery printmaking",
    ),
    # --- EU: ヨーロッパ（フォールバック） ---
    ("EU", CONTENT_TYPE_FACT): ArtStyle(
        region="EU",
        content_type=CONTENT_TYPE_FACT,
        style_prefix=(
            "Carte de visite photograph style, small-format albumen print, "
            "oval vignette framing, studio backdrop, "
            "19th century European portrait photography aesthetic. "
        ),
        negative_prompt="color, modern elements, digital artifacts, cartoon, illustration",
        description="Carte de visite photograph, small-format albumen print, 19th century European photography",
    ),
    ("EU", CONTENT_TYPE_FOLKLORE): ArtStyle(
        region="EU",
        content_type=CONTENT_TYPE_FOLKLORE,
        style_prefix=(
            "Renaissance copperplate engraving style, fine burin linework, "
            "classical composition, detailed hatching technique, "
            "Albrecht Dürer-inspired European printmaking aesthetic. "
        ),
        negative_prompt="photograph, modern elements, digital art, bright colors, 3D render",
        description="Renaissance copperplate engraving, fine burin linework, Dürer-inspired printmaking",
    ),
}


def get_art_style(region: str, content_type: str) -> ArtStyle:
    """リージョンとコンテンツタイプに応じたアートスタイルを返す。

    不明なリージョンは EU にフォールバック。
    不正な content_type は fact にフォールバック。

    Args:
        region: ISO 3166-1 alpha-2 国コード（例: "US", "JP", "GB"）
        content_type: "fact" または "folklore"

    Returns:
        対応する ArtStyle
    """
    # content_type の正規化
    if content_type not in (CONTENT_TYPE_FACT, CONTENT_TYPE_FOLKLORE):
        content_type = CONTENT_TYPE_FACT

    region = region.upper()

    # 完全一致
    key = (region, content_type)
    if key in _STYLE_REGISTRY:
        return _STYLE_REGISTRY[key]

    # リージョン不明 → EU フォールバック
    fallback_key = (FALLBACK_REGION, content_type)
    return _STYLE_REGISTRY[fallback_key]


def get_all_regions() -> list[str]:
    """登録済みの全リージョンコードを返す。"""
    return sorted({style.region for style in _STYLE_REGISTRY.values()})


def get_style_description(region: str, content_type: str) -> str:
    """リージョンとコンテンツタイプに応じたスタイル説明文を返す。"""
    return get_art_style(region, content_type).description
