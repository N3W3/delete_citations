from pathlib import Path
from typing import List, Optional, Union

from delete_citations.cleaner import (
    DEFAULT_CITATION_PATTERN,
    detect_citations,
    remove_citations,
    replace_citations,
)


class File:
    """Gestionnaire de fichier pour la détection et suppression de citations."""

    def __init__(self, chemin: Union[str, Path]):
        self.chemin = Path(chemin)
        self.lignes: List[str] = []
        if self.chemin.exists():
            self.lecture_fichier()

    def lecture_fichier(self) -> None:
        """Lit le fichier ligne par ligne en UTF-8."""
        with open(self.chemin, "r", encoding="utf-8") as f:
            self.lignes = f.readlines()

    @property
    def contenu(self) -> str:
        """Retourne le contenu complet sous forme de chaîne de caractères."""
        return "".join(self.lignes)

    def detection(self, pattern: str = DEFAULT_CITATION_PATTERN) -> List[str]:
        """Détecte et retourne toutes les citations présentes dans le fichier."""
        return detect_citations(self.contenu, pattern=pattern)

    def edition(self, pattern: str = DEFAULT_CITATION_PATTERN, replacement: str = "") -> None:
        """Remplace les citations ligne par ligne dans self.lignes."""
        self.lignes = [
            replace_citations(ligne, replacement=replacement, pattern=pattern)
            for ligne in self.lignes
        ]

    def supression(self, pattern: str = DEFAULT_CITATION_PATTERN) -> None:
        """Supprime toutes les citations du fichier (alias avec un seul p)."""
        self.edition(pattern=pattern, replacement="")

    def suppression(self, pattern: str = DEFAULT_CITATION_PATTERN) -> None:
        """Supprime toutes les citations du fichier (orthographe standard)."""
        self.supression(pattern=pattern)

    def remplacer(self, replacement: str, pattern: str = DEFAULT_CITATION_PATTERN) -> None:
        """Remplace toutes les citations par la chaîne spécifiée."""
        self.edition(pattern=pattern, replacement=replacement)

    def sauvegarde(self, destination: Optional[Union[str, Path]] = None) -> Path:
        """Sauvegarde les lignes modifiées dans le fichier cible ou d'origine."""
        cible = Path(destination) if destination else self.chemin
        cible.parent.mkdir(parents=True, exist_ok=True)
        with open(cible, "w", encoding="utf-8") as f:
            f.writelines(self.lignes)
        return cible
