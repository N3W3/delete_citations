"""Configuration globale et fixtures pour pytest.

Les fixtures pytest permettent de préparer des données ou des environnements réutilisables
dans les différents fichiers de tests sans dupliquer de code.
"""
from pathlib import Path
import pytest


@pytest.fixture
def sample_tex_content() -> str:
    """Retourne un exemple de contenu LaTeX avec plusieurs citations."""
    return (
        "\\documentclass{article}\n"
        "\\begin{document}\n"
        "Introduction à la physique quantique [cite 1].\n"
        "Des résultats remarquables ont été démontrés [cite 2] et confirmés plus tard [cite 3].\n"
        "Conclusion sans citation ici.\n"
        "\\end{document}\n"
    )


@pytest.fixture
def sample_org_content() -> str:
    """Retourne un exemple de contenu Org-mode avec syntaxe [cite:N]."""
    return (
        "* Mes Notes de Recherche\n"
        "Une référence importante [cite:10] est décrite ci-dessous.\n"
        "Deux citations consécutives : [cite:21] [cite:22].\n"
    )


@pytest.fixture
def sample_tex_file(tmp_path: Path, sample_tex_content: str) -> Path:
    """Crée un fichier temporaire .tex avec du contenu de test.

    `tmp_path` est une fixture intégrée à pytest qui fournit un dossier temporaire
    unique à chaque exécution de test et nettoyé automatiquement.
    """
    fichier = tmp_path / "document.tex"
    fichier.write_text(sample_tex_content, encoding="utf-8")
    return fichier


@pytest.fixture
def sample_clean_file(tmp_path: Path) -> Path:
    """Crée un fichier texte temporaire qui ne contient aucune citation."""
    fichier = tmp_path / "sans_citations.txt"
    fichier.write_text("Ceci est un fichier propre sans aucune citation.\nDeuxième ligne.\n", encoding="utf-8")
    return fichier
