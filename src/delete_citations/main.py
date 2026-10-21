"""Point d'entrée en ligne de commande pour delete-citations."""
import argparse
from pathlib import Path
import sys
from typing import List, Optional

from delete_citations.cleaner import DEFAULT_CITATION_PATTERN
from delete_citations.directory import DEFAULT_EXTENSIONS, Directory
from delete_citations.file.file import File

__version__ = "0.2.0"


def parse_args(args: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse les arguments de la ligne de commande."""
    parser = argparse.ArgumentParser(
        prog="delete-citations",
        description=(
            "Supprime ou remplace les citations [cite ...] dans les fichiers "
            "ou de manière récursive dans toute une arborescence de dossiers."
        ),
    )
    parser.add_argument(
        "chemin",
        type=str,
        metavar="CHEMIN",
        help="Chemin vers le fichier ou dossier à traiter",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default=None,
        help="Chemin du fichier ou dossier de sortie (modifie sur place par défaut)",
    )
    parser.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        default=True,
        help="Parcourt récursivement les sous-dossiers (activé par défaut pour les dossiers)",
    )
    parser.add_argument(
        "--no-recursive",
        dest="recursive",
        action="store_false",
        help="Désactive le parcours récursif des sous-dossiers",
    )
    parser.add_argument(
        "-e",
        "--extension",
        "--ext",
        nargs="+",
        default=None,
        help=f"Extensions de fichiers à filtrer (ex: .tex .org .md). Par défaut : {', '.join(sorted(DEFAULT_EXTENSIONS))}",
    )
    parser.add_argument(
        "-a",
        "--all",
        action="store_true",
        default=False,
        help="Traiter tous les fichiers sans filtrer par extension",
    )
    parser.add_argument(
        "-n",
        "--dry-run",
        action="store_true",
        default=False,
        help="Mode simulation : affiche ce qui serait fait sans écrire sur le disque",
    )
    parser.add_argument(
        "-p",
        "--pattern",
        type=str,
        default=DEFAULT_CITATION_PATTERN,
        help="Expression régulière personnalisée pour détecter les citations",
    )
    parser.add_argument(
        "--replace",
        type=str,
        default="",
        help="Texte de remplacement pour les citations (par défaut : suppression vide)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        default=False,
        help="Affiche le détail de chaque fichier traité",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        default=False,
        help="Mode silencieux : affiche uniquement les erreurs",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    return parser.parse_args(args)


def main(args: Optional[List[str]] = None) -> int:
    """Point d'entrée principal : traite un fichier unique ou un dossier complet."""
    parsed = parse_args(args)
    cible = Path(parsed.chemin)

    if not cible.exists():
        print(f"Erreur : Le fichier ou dossier '{parsed.chemin}' n'existe pas.", file=sys.stderr)
        return 1

    # Cas 1 : Traitement d'un fichier unique
    if cible.is_file():
        fichier = File(cible)
        citations = fichier.detection(pattern=parsed.pattern)

        if not parsed.quiet:
            print(f"{len(citations)} citation(s) détectée(s).")

        if parsed.replace:
            fichier.remplacer(parsed.replace, pattern=parsed.pattern)
        else:
            fichier.suppression(pattern=parsed.pattern)

        if not parsed.dry_run:
            sortie = fichier.sauvegarde(destination=parsed.output)
            if not parsed.quiet:
                print(f"Fichier sauvegardé avec succès dans : {sortie}")
        else:
            if not parsed.quiet:
                print(f"[Simulation] Fichier analysé : {cible}")
        return 0

    # Cas 2 : Traitement d'un dossier
    elif cible.is_dir():
        extensions = ["*"] if parsed.all else parsed.extension
        dossier = Directory(
            cible,
            extensions=extensions,
            recursive=parsed.recursive,
        )

        resultat = dossier.traiter(
            destination=parsed.output,
            replacement=parsed.replace,
            pattern=parsed.pattern,
            dry_run=parsed.dry_run,
        )

        if parsed.verbose and not parsed.quiet:
            for report in resultat.file_reports:
                if report.error:
                    print(f"  [ERREUR] {report.source_path} : {report.error}")
                elif report.modified:
                    action = "remplacée(s)" if parsed.replace else "supprimée(s)"
                    print(f"  [MODIFIÉ] {report.source_path} : {report.citations_count} citation(s) {action}")
                else:
                    print(f"  [INTACT]  {report.source_path} : 0 citation")

        if not parsed.quiet:
            prefix = "[Simulation] " if parsed.dry_run else ""
            action = "remplacée(s)" if parsed.replace else "supprimée(s)"
            print(
                f"{prefix}Traitement terminé : {resultat.total_files_scanned} fichier(s) analysé(s), "
                f"{resultat.total_files_modified} modifié(s), "
                f"{resultat.total_citations_removed} citation(s) {action}."
            )
            if parsed.output and not parsed.dry_run:
                print(f"Dossier sauvegardé avec succès dans : {parsed.output}")

        if resultat.errors and not parsed.quiet:
            for err in resultat.errors:
                print(f"Avertissement : {err}", file=sys.stderr)

        return 0

    return 1



if __name__ == "__main__":
    sys.exit(main())
