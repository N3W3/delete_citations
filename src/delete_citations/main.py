"""Point d'entrée en ligne de commande pour delete-citations."""
import argparse
import sys
from typing import List, Optional

from delete_citations.file.file import File


def parse_args(args: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse les arguments de la ligne de commande."""
    parser = argparse.ArgumentParser(
        description="Supprime les citations [cite ...] des fichiers .tex, .org, etc."
    )
    parser.add_argument(
        "fichier",
        type=str,
        help="Chemin vers le fichier à traiter",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default=None,
        help="Chemin du fichier de sortie (écrase le fichier d'origine par défaut)",
    )
    return parser.parse_args(args)


def main(args: Optional[List[str]] = None) -> int:
    """Exécute le nettoyage sur le fichier fourni."""
    parsed = parse_args(args)
    fichier = File(parsed.fichier)

    if not fichier.chemin.exists():
        print(f"Erreur : Le fichier '{parsed.fichier}' n'existe pas.", file=sys.stderr)
        return 1

    citations = fichier.detection()
    print(f"{len(citations)} citation(s) détectée(s).")

    fichier.suppression()
    sortie = fichier.sauvegarde(destination=parsed.output)
    print(f"Fichier sauvegardé avec succès dans : {sortie}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
