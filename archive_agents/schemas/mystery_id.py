"""Mystery ID schema and classification codes.

Defines the naming convention for mystery article IDs:
    {Classification}-{StateCode}-{AreaCode}-{Timestamp}
    Example: OCC-MA-617-20260207143025

References:
- Classification: Project-specific 3-letter codes
- State Code: USPS/ISO 3166-2:US standard (2 letters)
- Area Code: US telephone area codes (3 digits)
- Timestamp: UTC datetime as YYYYMMDDHHMMSS
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


# Common US area codes by city (reference for agents)
# Format: "CITY_NAME": ("STATE_CODE", "AREA_CODE")
AREA_CODES = {
    # Northeast
    "BOSTON": ("MA", "617"),
    "CAMBRIDGE": ("MA", "617"),
    "SALEM": ("MA", "978"),
    "NEW_YORK": ("NY", "212"),
    "MANHATTAN": ("NY", "212"),
    "BROOKLYN": ("NY", "718"),
    "PHILADELPHIA": ("PA", "215"),
    "PITTSBURGH": ("PA", "412"),
    "PROVIDENCE": ("RI", "401"),
    "HARTFORD": ("CT", "860"),
    # Southeast
    "WASHINGTON_DC": ("DC", "202"),
    "BALTIMORE": ("MD", "410"),
    "RICHMOND": ("VA", "804"),
    "CHARLESTON": ("SC", "843"),
    "SAVANNAH": ("GA", "912"),
    "ATLANTA": ("GA", "404"),
    "NEW_ORLEANS": ("LA", "504"),
    "MIAMI": ("FL", "305"),
    # Midwest
    "CHICAGO": ("IL", "312"),
    "DETROIT": ("MI", "313"),
    "CLEVELAND": ("OH", "216"),
    "CINCINNATI": ("OH", "513"),
    "ST_LOUIS": ("MO", "314"),
    "MILWAUKEE": ("WI", "414"),
    "MINNEAPOLIS": ("MN", "612"),
    # Southwest
    "DALLAS": ("TX", "214"),
    "HOUSTON": ("TX", "713"),
    "SAN_ANTONIO": ("TX", "210"),
    "AUSTIN": ("TX", "512"),
    "PHOENIX": ("AZ", "602"),
    "ALBUQUERQUE": ("NM", "505"),
    "DENVER": ("CO", "303"),
    # West Coast
    "LOS_ANGELES": ("CA", "213"),
    "SAN_FRANCISCO": ("CA", "415"),
    "SAN_DIEGO": ("CA", "619"),
    "SEATTLE": ("WA", "206"),
    "PORTLAND": ("OR", "503"),
    # Pacific
    "HONOLULU": ("HI", "808"),
    "ANCHORAGE": ("AK", "907"),
}


def validate_mystery_id(mystery_id: str) -> bool:
    """Validate mystery ID format.

    Args:
        mystery_id: ID string to validate.

    Returns:
        True if valid format, False otherwise.

    Expected format: {CLS}-{ST}-{AREA}-{YYYYMMDDHHMMSS}
    Example: OCC-MA-617-20260207143025
    """
    parts = mystery_id.split("-")
    if len(parts) != 4:
        return False

    classification, state, area, timestamp = parts

    # Validate classification (3 uppercase letters)
    if len(classification) != 3 or not classification.isupper():
        return False

    # Validate state code (2 uppercase letters)
    if len(state) != 2 or not state.isupper():
        return False

    # Validate area code (3 digits)
    if len(area) != 3 or not area.isdigit():
        return False

    # Validate timestamp (14 digits)
    if len(timestamp) != 14 or not timestamp.isdigit():
        return False

    return True


def parse_mystery_id(mystery_id: str) -> dict | None:
    """Parse mystery ID into components.

    Args:
        mystery_id: ID string to parse.

    Returns:
        Dictionary with classification, state, area, timestamp, or None if invalid.
    """
    if not validate_mystery_id(mystery_id):
        return None

    parts = mystery_id.split("-")
    return {
        "classification": parts[0],
        "state": parts[1],
        "area": parts[2],
        "timestamp": parts[3],
    }
