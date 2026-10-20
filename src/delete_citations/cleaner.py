"""Module de détection et suppression des citations dans les chaînes de texte."""
import re
from typing import List

# Expression régulière par défaut pour capturer [cite 1], [cite:1], [cite 123], etc.
DEFAULT_CITATION_PATTERN = r"\[cite:?\s*[0-9]+\]"


def detect_citations(text: str, pattern: str = DEFAULT_CITATION_PATTERN) -> List[str]:
    """Retourne la liste de toutes les citations trouvées dans le texte.

    Exemple:
        >>> detect_citations("Texte [cite 1] et [cite:2]")
        ['[cite 1]', '[cite:2]']
    """
    return re.findall(pattern, text)


def remove_citations(text: str, pattern: str = DEFAULT_CITATION_PATTERN) -> str:
    """Supprime les citations trouvées dans le texte.

    Exemple:
        >>> remove_citations("Texte [cite 1] avec citation.")
        'Texte  avec citation.'
    """
    return re.sub(pattern, "", text)


def replace_citations(text: str, replacement: str = "", pattern: str = DEFAULT_CITATION_PATTERN) -> str:
    """Remplace les citations trouvées par une chaîne de remplacement donnée.

    Exemple:
        >>> replace_citations("Texte [cite 1]", replacement="(ref)")
        'Texte (ref)'
    """
    return re.sub(pattern, replacement, text)
