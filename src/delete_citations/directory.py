"""Module de gestion et traitement récursif des dossiers."""
from dataclasses import dataclass, field
import os
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Union

from delete_citations.cleaner import DEFAULT_CITATION_PATTERN
from delete_citations.file.file import File

# Extensions textuelles couramment utilisées dans la rédaction et la recherche
DEFAULT_EXTENSIONS: Set[str] = {
    ".tex",
    ".org",
    ".md",
    ".markdown",
    ".txt",
    ".typ",
    ".rmd",
    ".rst",
    ".bib",
    ".html",
    ".xml",
    ".asciidoc",
    ".adoc",
}

# Dossiers techniques et caches ignorés par défaut lors de la récursion
DEFAULT_IGNORED_DIRS: Set[str] = {
    ".git",
    ".svn",
    ".hg",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".tox",
    "node_modules",
    "dist",
    "build",
    ".egg-info",
}


@dataclass
class FileReport:
    """Rapport d'analyse et de traitement pour un fichier donné."""
    source_path: Path
    output_path: Optional[Path] = None
    citations_count: int = 0
    modified: bool = False
    error: Optional[str] = None


@dataclass
class BatchResult:
    """Résultat consolidé du traitement d'un dossier."""
    total_files_scanned: int = 0
    total_files_modified: int = 0
    total_citations_removed: int = 0
    file_reports: List[FileReport] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


class Directory:
    """Gestionnaire de dossier pour la détection et suppression récursive de citations."""

    def __init__(
        self,
        chemin: Union[str, Path],
        extensions: Optional[Iterable[str]] = None,
        ignored_dirs: Optional[Iterable[str]] = None,
        recursive: bool = True,
    ):
        self.chemin = Path(chemin).resolve()
        self.recursive = recursive
        self.ignored_dirs = (
            set(ignored_dirs) if ignored_dirs is not None else set(DEFAULT_IGNORED_DIRS)
        )

        if extensions is not None:
            self.extensions: Optional[Set[str]] = {
                ext if ext == "*" else (ext.lower() if ext.startswith(".") else f".{ext.lower()}")
                for ext in extensions
            }
        else:
            self.extensions = None

    def _should_ignore_dir(self, dir_name: str) -> bool:
        """Détermine si un sous-dossier doit être ignoré."""
        return dir_name in self.ignored_dirs or dir_name.startswith(".")

    def _should_include_file(self, file_path: Path) -> bool:
        """Vérifie si un fichier correspond aux critères d'extension."""
        if file_path.name.startswith("."):
            return False

        if self.extensions is None:
            return file_path.suffix.lower() in DEFAULT_EXTENSIONS

        if "*" in self.extensions:
            return True

        return file_path.suffix.lower() in self.extensions

    def collect_files(self) -> List[Path]:
        """Collecte et retourne la liste des fichiers éligibles dans le dossier."""
        if not self.chemin.exists() or not self.chemin.is_dir():
            return []

        fichiers: List[Path] = []

        if self.recursive:
            for root_dir, dirs, files in os.walk(self.chemin):
                # Élaguer in-place les répertoires à ignorer pour ne pas y descendre
                dirs[:] = [d for d in dirs if not self._should_ignore_dir(d)]

                current_root = Path(root_dir)
                for filename in files:
                    file_path = current_root / filename
                    if self._should_include_file(file_path):
                        fichiers.append(file_path)
        else:
            for item in self.chemin.iterdir():
                if item.is_file() and self._should_include_file(item):
                    fichiers.append(item)

        return sorted(fichiers)

    def detection(self, pattern: str = DEFAULT_CITATION_PATTERN) -> Dict[Path, List[str]]:
        """Détecte les citations dans l'ensemble des fichiers éligibles."""
        resultats: Dict[Path, List[str]] = {}
        for fichier in self.collect_files():
            try:
                doc = File(fichier)
                citations = doc.detection(pattern=pattern)
                if citations:
                    resultats[fichier] = citations
            except (UnicodeDecodeError, OSError):
                continue
        return resultats

    def traiter(
        self,
        destination: Optional[Union[str, Path]] = None,
        replacement: str = "",
        pattern: str = DEFAULT_CITATION_PATTERN,
        dry_run: bool = False,
    ) -> BatchResult:
        """Traite tous les fichiers collectés (suppression ou remplacement)."""
        fichiers = self.collect_files()
        resultat = BatchResult(total_files_scanned=len(fichiers))
        dest_path = Path(destination).resolve() if destination else None

        for f_src in fichiers:
            # Calcul du chemin de destination si spécifié
            if dest_path:
                try:
                    rel = f_src.relative_to(self.chemin)
                except ValueError:
                    rel = f_src.name
                f_dst = dest_path / rel
            else:
                f_dst = f_src

            try:
                doc = File(f_src)
                citations = doc.detection(pattern=pattern)
                nb_citations = len(citations)

                report = FileReport(
                    source_path=f_src,
                    output_path=f_dst,
                    citations_count=nb_citations,
                )

                if nb_citations > 0:
                    if replacement:
                        doc.remplacer(replacement=replacement, pattern=pattern)
                    else:
                        doc.suppression(pattern=pattern)

                    if not dry_run:
                        doc.sauvegarde(destination=f_dst)

                    report.modified = True
                    resultat.total_files_modified += 1
                    resultat.total_citations_removed += nb_citations
                else:
                    # Si une destination est précisée, copier le fichier non modifié pour garder l'arbre complet
                    if dest_path and not dry_run:
                        doc.sauvegarde(destination=f_dst)

                resultat.file_reports.append(report)

            except UnicodeDecodeError:
                err_msg = f"Fichier binaire ou encodage non supporté ignoré : {f_src}"
                resultat.errors.append(err_msg)
                resultat.file_reports.append(
                    FileReport(source_path=f_src, error="UnicodeDecodeError")
                )
            except Exception as e:
                err_msg = f"Erreur lors du traitement de '{f_src}': {e}"
                resultat.errors.append(err_msg)
                resultat.file_reports.append(
                    FileReport(source_path=f_src, error=str(e))
                )

        return resultat

    def suppression(
        self,
        destination: Optional[Union[str, Path]] = None,
        pattern: str = DEFAULT_CITATION_PATTERN,
        dry_run: bool = False,
    ) -> BatchResult:
        """Supprime les citations dans tous les fichiers du dossier."""
        return self.traiter(
            destination=destination,
            replacement="",
            pattern=pattern,
            dry_run=dry_run,
        )

    def remplacer(
        self,
        replacement: str,
        destination: Optional[Union[str, Path]] = None,
        pattern: str = DEFAULT_CITATION_PATTERN,
        dry_run: bool = False,
    ) -> BatchResult:
        """Remplace les citations par une chaîne dans tous les fichiers du dossier."""
        return self.traiter(
            destination=destination,
            replacement=replacement,
            pattern=pattern,
            dry_run=dry_run,
        )
