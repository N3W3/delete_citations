"""Tests unitaires et d'intégration pour la classe `Directory`.

Ce fichier teste le parcours récursif, le filtrage par extension, l'exclusion
des dossiers techniques, ainsi que le nettoyage par lot et la sauvegarde.
"""
from pathlib import Path
import pytest

from delete_citations.directory import (
    DEFAULT_EXTENSIONS,
    DEFAULT_IGNORED_DIRS,
    BatchResult,
    Directory,
)


@pytest.fixture
def sample_tree(tmp_path: Path) -> Path:
    """Crée une arborescence de fichiers de test pour tester la récursivité."""
    root = tmp_path / "projet"
    root.mkdir()

    # Fichiers à la racine
    (root / "racine.tex").write_text("Texte racine [cite 1].", encoding="utf-8")
    (root / "racine_propre.txt").write_text("Texte racine sans citation.", encoding="utf-8")
    (root / "image.png").write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR")

    # Sous-dossier niveau 1
    sub1 = root / "chapitre1"
    sub1.mkdir()
    (sub1 / "intro.md").write_text("Intro [cite 2] et suite [cite:3].", encoding="utf-8")
    (sub1 / "notes.org").write_text("* Note [cite 4]", encoding="utf-8")

    # Sous-dossier niveau 2
    sub2 = sub1 / "annexes"
    sub2.mkdir()
    (sub2 / "annexe.tex").write_text("Annexe [cite 5].", encoding="utf-8")

    # Dossiers techniques devant être ignorés
    git_dir = root / ".git"
    git_dir.mkdir()
    (git_dir / "config.tex").write_text("Ignoré [cite 999].", encoding="utf-8")

    venv_dir = root / ".venv"
    venv_dir.mkdir()
    (venv_dir / "lib.tex").write_text("Ignoré [cite 999].", encoding="utf-8")

    pycache_dir = sub1 / "__pycache__"
    pycache_dir.mkdir()
    (pycache_dir / "cache.tex").write_text("Ignoré [cite 999].", encoding="utf-8")

    return root


class TestDirectoryCollection:
    """Vérifie la collecte et le filtrage des fichiers dans l'arborescence."""

    def test_collect_files_recursive_par_defaut(self, sample_tree: Path):
        d = Directory(sample_tree)
        fichiers = d.collect_files()
        noms = [f.name for f in fichiers]

        # Fichiers attendus
        assert "racine.tex" in noms
        assert "racine_propre.txt" in noms
        assert "intro.md" in noms
        assert "notes.org" in noms
        assert "annexe.tex" in noms

        # Les binaires / extensions non supportées par défaut ne doivent pas être collectés
        assert "image.png" not in noms

        # Les dossiers techniques (.git, .venv, __pycache__) doivent être ignorés
        assert "config.tex" not in noms
        assert "lib.tex" not in noms
        assert "cache.tex" not in noms

    def test_collect_files_non_recursive(self, sample_tree: Path):
        d = Directory(sample_tree, recursive=False)
        fichiers = d.collect_files()
        noms = [f.name for f in fichiers]

        assert "racine.tex" in noms
        assert "racine_propre.txt" in noms
        # Les fichiers des sous-dossiers ne doivent pas apparaître
        assert "intro.md" not in noms
        assert "annexe.tex" not in noms

    def test_collect_files_filtre_extensions(self, sample_tree: Path):
        d = Directory(sample_tree, extensions=[".tex"])
        fichiers = d.collect_files()
        noms = [f.name for f in fichiers]

        assert "racine.tex" in noms
        assert "annexe.tex" in noms
        assert "intro.md" not in noms
        assert "racine_propre.txt" not in noms

    def test_collect_files_filtre_extensions_sans_point(self, sample_tree: Path):
        d = Directory(sample_tree, extensions=["org", "md"])
        fichiers = d.collect_files()
        noms = [f.name for f in fichiers]

        assert "intro.md" in noms
        assert "notes.org" in noms
        assert "racine.tex" not in noms

    def test_collect_files_all_extensions(self, sample_tree: Path):
        d = Directory(sample_tree, extensions=["*"])
        fichiers = d.collect_files()
        noms = [f.name for f in fichiers]

        assert "image.png" in noms
        assert "racine.tex" in noms
        assert "config.tex" not in noms  # .git toujours ignoré


class TestDirectoryDetection:
    """Vérifie la détection globale des citations dans un dossier."""

    def test_detection_multi_fichiers(self, sample_tree: Path):
        d = Directory(sample_tree)
        resultats = d.detection()

        # Fichiers ayant des citations
        fichiers_avec_citations = {p.name: cites for p, cites in resultats.items()}
        assert "racine.tex" in fichiers_avec_citations
        assert fichiers_avec_citations["racine.tex"] == ["[cite 1]"]
        assert fichiers_avec_citations["intro.md"] == ["[cite 2]", "[cite:3]"]
        assert fichiers_avec_citations["annexe.tex"] == ["[cite 5]"]

        # Fichier propre ne doit pas avoir de citations
        assert "racine_propre.txt" not in fichiers_avec_citations


class TestDirectorySuppression:
    """Vérifie la suppression de citations sur l'ensemble d'un dossier."""

    def test_suppression_sur_place(self, sample_tree: Path):
        d = Directory(sample_tree)
        rapport = d.suppression()

        assert isinstance(rapport, BatchResult)
        assert rapport.total_files_scanned == 5
        assert rapport.total_files_modified == 4  # racine.tex, intro.md, notes.org, annexe.tex
        assert rapport.total_citations_removed == 5

        # Vérification directe sur disque
        contenu_racine = (sample_tree / "racine.tex").read_text(encoding="utf-8")
        assert "[cite 1]" not in contenu_racine
        assert "Texte racine ." in contenu_racine

        contenu_annexe = (sample_tree / "chapitre1" / "annexes" / "annexe.tex").read_text(encoding="utf-8")
        assert "[cite 5]" not in contenu_annexe

    def test_suppression_avec_dossier_destination(self, sample_tree: Path, tmp_path: Path):
        dossier_sortie = tmp_path / "projet_propre"
        d = Directory(sample_tree)
        rapport = d.suppression(destination=dossier_sortie)

        assert rapport.total_files_modified == 4
        assert rapport.total_citations_removed == 5

        # L'arborescence doit être répliquée
        assert (dossier_sortie / "racine.tex").exists()
        assert (dossier_sortie / "chapitre1" / "intro.md").exists()
        assert (dossier_sortie / "chapitre1" / "annexes" / "annexe.tex").exists()
        assert (dossier_sortie / "racine_propre.txt").exists()

        # Le dossier de sortie est nettoyé
        contenu_sortie = (dossier_sortie / "racine.tex").read_text(encoding="utf-8")
        assert "[cite 1]" not in contenu_sortie

        # Les fichiers sources n'ont pas été touchés
        contenu_source = (sample_tree / "racine.tex").read_text(encoding="utf-8")
        assert "[cite 1]" in contenu_source

    def test_remplacer_dans_dossier(self, sample_tree: Path):
        d = Directory(sample_tree)
        rapport = d.remplacer(replacement="[REF]")

        assert rapport.total_citations_removed == 5
        contenu = (sample_tree / "racine.tex").read_text(encoding="utf-8")
        assert "[REF]" in contenu
        assert "[cite 1]" not in contenu

    def test_dry_run_ne_modifie_rien(self, sample_tree: Path):
        d = Directory(sample_tree)
        rapport = d.suppression(dry_run=True)

        assert rapport.total_files_modified == 4
        assert rapport.total_citations_removed == 5

        # Fichier d'origine intact
        contenu = (sample_tree / "racine.tex").read_text(encoding="utf-8")
        assert "[cite 1]" in contenu


class TestDirectoryCasLimites:
    """Vérifie la robustesse face à des cas d'erreur ou fichiers non textuels."""

    def test_fichier_binaire_avec_option_all(self, sample_tree: Path):
        # image.png ne doit pas planter l'exécution même si collectée
        d = Directory(sample_tree, extensions=["*"])
        rapport = d.suppression(dry_run=True)

        # Doit continuer et avoir traité les autres fichiers
        assert rapport.total_files_modified == 4

    def test_dossier_vide(self, tmp_path: Path):
        vide = tmp_path / "vide"
        vide.mkdir()
        d = Directory(vide)
        rapport = d.suppression()

        assert rapport.total_files_scanned == 0
        assert rapport.total_files_modified == 0
        assert rapport.total_citations_removed == 0

    def test_dossier_inexistant(self, tmp_path: Path):
        inexistant = tmp_path / "dossier_fantome"
        d = Directory(inexistant)
        assert d.collect_files() == []
        assert d.detection() == {}

    def test_chemin_est_un_fichier(self, sample_tree: Path):
        fichier = sample_tree / "racine.tex"
        d = Directory(fichier)
        assert d.collect_files() == []

    def test_destination_fichier_externe(self, sample_tree: Path, tmp_path: Path):
        d = Directory(sample_tree)
        # Forcer un fichier collecté hors arborescence pour tester ValueError dans relative_to
        externe = tmp_path / "externe.tex"
        externe.write_text("Ext [cite 1]", encoding="utf-8")
        d.collect_files = lambda: [externe]
        rapport = d.suppression(destination=tmp_path / "sortie")
        assert (tmp_path / "sortie" / "externe.tex").exists()


    def test_detection_avec_fichier_binaire(self, sample_tree: Path):
        # En forçant la collecte des binaires
        d = Directory(sample_tree, extensions=["*"])
        resultat = d.detection()
        assert any("racine.tex" in str(p) for p in resultat)

    def test_traiter_avec_erreur_os(self, sample_tree: Path, monkeypatch: pytest.MonkeyPatch):
        d = Directory(sample_tree)

        def declencher_erreur(*args, **kwargs):
            raise PermissionError("Accès refusé simulé")

        monkeypatch.setattr(Path, "mkdir", declencher_erreur)
        rapport = d.suppression(destination=sample_tree.parent / "non_autorise")
        assert len(rapport.errors) > 0
        assert any("PermissionError" in err or "Accès refusé" in err for err in rapport.errors)

