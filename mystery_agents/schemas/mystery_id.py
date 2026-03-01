"""Mystery ID schema and classification codes.

Defines the naming convention for mystery article IDs:
    {Classification}-{CountryISO2}-{RegionIATA}-{Timestamp}
    Example: OCC-US-BOS-20260207143025

References:
- Classification: Project-specific 3-letter codes
- Country Code: ISO 3166-1 alpha-2 standard (2 letters)
- Region Code: IATA airport code or abbreviation (3-5 uppercase letters)
- Timestamp: UTC datetime as YYYYMMDDHHMMSS

Note: v1 形式（{CLS}-{StateCode}-{AreaCode3digits}-{Timestamp}, 例: OCC-MA-617-...）は
廃止済み。既存 ID は Firestore に後方互換として残るが、新規生成は v2 のみ。
"""

from enum import Enum


class ClassificationCode(str, Enum):
    """Article classification codes (3 letters).

    Based on Library of Congress Classification principles,
    adapted for the Ghost in the Archive project.
    """

    HIS = "HIS"  # History - historical record discrepancies, missing persons
    FLK = "FLK"  # Folklore - local traditions, festivals, oral traditions
    ANT = "ANT"  # Anthropology - rituals, social structures, material culture
    OCC = "OCC"  # Occult - unexplainable phenomena, supernatural events
    URB = "URB"  # Urban Legend - modern rumors, contemporary ghost stories
    CRM = "CRM"  # Crime - unsolved crimes, disappearances
    REL = "REL"  # Religion - religious taboos, curses, cults
    LOC = "LOC"  # Locus - place-bound anomalies, haunted locations


# Classification code descriptions (for agent instructions)
CLASSIFICATION_DESCRIPTIONS = {
    ClassificationCode.HIS: "歴史的記録の矛盾、消失した人物、文書の欠落",
    ClassificationCode.FLK: "地方伝承、祭り、口承伝統、民間信仰",
    ClassificationCode.ANT: "儀礼、社会構造、物質文化、異文化接触",
    ClassificationCode.OCC: "説明不能な現象、超常的事象、怪異",
    ClassificationCode.URB: "近代の噂話、現代の怪談、都市伝説",
    ClassificationCode.CRM: "未解決犯罪、失踪事件、謎の死",
    ClassificationCode.REL: "宗教的タブー、呪い、カルト、禁忌",
    ClassificationCode.LOC: "特定の場所に紐づく怪異、心霊スポット",
}

# Classification code descriptions in English (for Curator prompts)
CLASSIFICATION_DESCRIPTIONS_EN = {
    ClassificationCode.HIS: "Historical record discrepancies, missing persons, document gaps",
    ClassificationCode.FLK: "Local traditions, festivals, oral traditions, folk beliefs",
    ClassificationCode.ANT: "Rituals, social structures, material culture, cross-cultural contact",
    ClassificationCode.OCC: "Unexplainable phenomena, supernatural events",
    ClassificationCode.URB: "Modern rumors, contemporary ghost stories",
    ClassificationCode.CRM: "Unsolved crimes, disappearances, mysterious deaths",
    ClassificationCode.REL: "Religious taboos, curses, cults",
    ClassificationCode.LOC: "Place-bound anomalies, haunted locations",
}


# 国際都市の地域コード
# Format: "CITY_NAME": ("COUNTRY_ISO2", "IATA_CODE")
REGION_CODES = {
    # United States
    "BOSTON": ("US", "BOS"),
    "CAMBRIDGE": ("US", "BOS"),
    "SALEM": ("US", "BOS"),
    "NEW_YORK": ("US", "JFK"),
    "MANHATTAN": ("US", "JFK"),
    "BROOKLYN": ("US", "JFK"),
    "PHILADELPHIA": ("US", "PHL"),
    "PITTSBURGH": ("US", "PIT"),
    "PROVIDENCE": ("US", "PVD"),
    "HARTFORD": ("US", "BDL"),
    "WASHINGTON_DC": ("US", "IAD"),
    "BALTIMORE": ("US", "BWI"),
    "RICHMOND": ("US", "RIC"),
    "CHARLESTON": ("US", "CHS"),
    "SAVANNAH": ("US", "SAV"),
    "ATLANTA": ("US", "ATL"),
    "NEW_ORLEANS": ("US", "MSY"),
    "MIAMI": ("US", "MIA"),
    "CHICAGO": ("US", "ORD"),
    "DETROIT": ("US", "DTW"),
    "CLEVELAND": ("US", "CLE"),
    "CINCINNATI": ("US", "CVG"),
    "ST_LOUIS": ("US", "STL"),
    "MILWAUKEE": ("US", "MKE"),
    "MINNEAPOLIS": ("US", "MSP"),
    "DALLAS": ("US", "DFW"),
    "HOUSTON": ("US", "IAH"),
    "SAN_ANTONIO": ("US", "SAT"),
    "AUSTIN": ("US", "AUS"),
    "PHOENIX": ("US", "PHX"),
    "ALBUQUERQUE": ("US", "ABQ"),
    "DENVER": ("US", "DEN"),
    "LOS_ANGELES": ("US", "LAX"),
    "SAN_FRANCISCO": ("US", "SFO"),
    "SAN_DIEGO": ("US", "SAN"),
    "SEATTLE": ("US", "SEA"),
    "PORTLAND": ("US", "PDX"),
    "HONOLULU": ("US", "HNL"),
    "ANCHORAGE": ("US", "ANC"),
    # United Kingdom / Ireland
    "LONDON": ("GB", "LHR"),
    "EDINBURGH": ("GB", "EDI"),
    "GLASGOW": ("GB", "GLA"),
    "DUBLIN": ("IE", "DUB"),
    "MANCHESTER": ("GB", "MAN"),
    "LIVERPOOL": ("GB", "LPL"),
    "OXFORD": ("GB", "OXF"),
    "CAMBRIDGE_UK": ("GB", "CBG"),
    # Germany / Austria / Switzerland
    "BERLIN": ("DE", "BER"),
    "MUNICH": ("DE", "MUC"),
    "HAMBURG": ("DE", "HAM"),
    "COLOGNE": ("DE", "CGN"),
    "FRANKFURT": ("DE", "FRA"),
    "VIENNA": ("AT", "VIE"),
    "ZURICH": ("CH", "ZRH"),
    "HEIDELBERG": ("DE", "FRA"),
    # Spain
    "MADRID": ("ES", "MAD"),
    "BARCELONA": ("ES", "BCN"),
    "SEVILLE": ("ES", "SVQ"),
    "TOLEDO": ("ES", "MAD"),
    # France / Belgium
    "PARIS": ("FR", "CDG"),
    "LYON": ("FR", "LYS"),
    "MARSEILLE": ("FR", "MRS"),
    "BRUSSELS": ("BE", "BRU"),
    "STRASBOURG": ("FR", "SXB"),
    # Netherlands
    "AMSTERDAM": ("NL", "AMS"),
    "ROTTERDAM": ("NL", "RTM"),
    "THE_HAGUE": ("NL", "AMS"),
    "LEIDEN": ("NL", "AMS"),
    # Portugal / Brazil
    "LISBON": ("PT", "LIS"),
    "PORTO": ("PT", "OPO"),
    "RIO_DE_JANEIRO": ("BR", "GIG"),
    "SAO_PAULO": ("BR", "GRU"),
    "SALVADOR": ("BR", "SSA"),
    # Japan
    "TOKYO": ("JP", "NRT"),
    "KYOTO": ("JP", "KIX"),
    "OSAKA": ("JP", "KIX"),
    "NARA": ("JP", "KIX"),
    # Other
    "CAIRO": ("EG", "CAI"),
    "ISTANBUL": ("TR", "IST"),
    "ROME": ("IT", "FCO"),
    "FLORENCE": ("IT", "FLR"),
    "VENICE": ("IT", "VCE"),
    "ATHENS": ("GR", "ATH"),
    "MEXICO_CITY": ("MX", "MEX"),
    "LIMA": ("PE", "LIM"),
    "BUENOS_AIRES": ("AR", "EZE"),
    "HAVANA": ("CU", "HAV"),
    "MUMBAI": ("IN", "BOM"),
    "BEIJING": ("CN", "PEK"),
    "SYDNEY": ("AU", "SYD"),
    "CAPE_TOWN": ("ZA", "CPT"),
    "NAIROBI": ("KE", "NBO"),
    "MARRAKECH": ("MA", "RAK"),
}


def validate_mystery_id(mystery_id: str) -> bool:
    """Validate mystery ID format.

    Args:
        mystery_id: ID string to validate.

    Returns:
        True if valid format, False otherwise.

    Expected format: {CLS}-{CC}-{REGION}-{YYYYMMDDHHMMSS}
    Example: OCC-US-BOS-20260207143025
    """
    parts = mystery_id.split("-")
    if len(parts) != 4:
        return False

    classification, country, region, timestamp = parts

    # 分類コード（3文字大文字）
    if len(classification) != 3 or not classification.isupper():
        return False

    # 国コード（2文字大文字）
    if len(country) != 2 or not country.isupper():
        return False

    # 地域コード（3-5文字大文字アルファベット）
    if not region.isalpha() or not region.isupper():
        return False
    if not (3 <= len(region) <= 5):
        return False

    # タイムスタンプ（14桁数字）
    if len(timestamp) != 14 or not timestamp.isdigit():
        return False

    return True


def parse_mystery_id(mystery_id: str) -> dict | None:
    """Parse mystery ID into components.

    Args:
        mystery_id: ID string to parse.

    Returns:
        Dictionary with classification, country_code, region_code, timestamp,
        or None if invalid.
    """
    if not validate_mystery_id(mystery_id):
        return None

    parts = mystery_id.split("-")
    return {
        "classification": parts[0],
        "country_code": parts[1],
        "region_code": parts[2],
        "timestamp": parts[3],
    }
