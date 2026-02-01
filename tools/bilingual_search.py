"""Bilingual keyword expansion for historical archive searches."""

from typing import Dict, List

# English-Spanish keyword pairs for historical mystery themes
KEYWORD_PAIRS: Dict[str, str] = {
    # Core mystery terms
    "conspiracy": "conspiración",
    "disappearance": "desaparición",
    "secret": "secreto",
    "mystery": "misterio",
    "hidden": "oculto",
    # Maritime terms
    "smuggling": "contrabando",
    "piracy": "piratería",
    "shipwreck": "naufragio",
    "mutiny": "motín",
    "cargo": "cargamento",
    "vessel": "buque",
    "harbor": "puerto",
    "captain": "capitán",
    # Crime and intrigue
    "assassination": "asesinato",
    "murder": "asesinato",
    "spy": "espía",
    "espionage": "espionaje",
    "fugitive": "fugitivo",
    "theft": "robo",
    # Political terms
    "rebellion": "rebelión",
    "treaty": "tratado",
    "exile": "exilio",
    "diplomat": "diplomático",
    "ambassador": "embajador",
    # Treasure and trade
    "treasure": "tesoro",
    "gold": "oro",
    "silver": "plata",
    "merchant": "comerciante",
    # Geographic
    "spain": "españa",
    "spanish": "español",
    "cuba": "cuba",
    "florida": "florida",
    # Folklore and supernatural
    "ghost": "fantasma",
    "specter": "espectro",
    "apparition": "aparición",
    "legend": "leyenda",
    "tale": "cuento",
    "lore": "tradición",
    "curse": "maldición",
    "cursed": "maldito",
    "superstition": "superstición",
    "belief": "creencia",
    "strange": "extraño",
    "mysterious": "misterioso",
    "unexplained": "inexplicable",
    "forbidden": "prohibido",
    "taboo": "tabú",
    "haunted": "embrujado",
    "witch": "bruja",
    "witchcraft": "brujería",
    "demon": "demonio",
    "omen": "presagio",
    "prophecy": "profecía",
}


def expand_keywords_bilingual(keywords: List[str]) -> Dict[str, List[str]]:
    """Expand keywords to include both English and Spanish variants.

    Args:
        keywords: List of keywords in either language

    Returns:
        Dict with 'en' and 'es' keys containing expanded keyword lists
    """
    english_keywords = set()
    spanish_keywords = set()

    # Create reverse lookup for Spanish to English
    reverse_pairs = {v: k for k, v in KEYWORD_PAIRS.items()}

    for keyword in keywords:
        keyword_lower = keyword.lower().strip()

        # Check if it's an English keyword
        if keyword_lower in KEYWORD_PAIRS:
            english_keywords.add(keyword_lower)
            spanish_keywords.add(KEYWORD_PAIRS[keyword_lower])
        # Check if it's a Spanish keyword (reverse lookup)
        elif keyword_lower in reverse_pairs:
            english_keywords.add(reverse_pairs[keyword_lower])
            spanish_keywords.add(keyword_lower)
        else:
            # Unknown keyword - add to both (might be a proper noun or location)
            english_keywords.add(keyword_lower)
            spanish_keywords.add(keyword_lower)

    return {"en": list(english_keywords), "es": list(spanish_keywords)}


def get_all_keywords() -> Dict[str, str]:
    """Return all available keyword pairs.

    Returns:
        Dictionary mapping English keywords to Spanish equivalents
    """
    return KEYWORD_PAIRS.copy()
