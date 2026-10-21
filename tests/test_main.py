"""Tests d'intégration pour le point d'entrée CLI (main.py).

Ce fichier teste l'interface en ligne de commande pour les fichiers uniques,
les répertoires récursifs, les options d'export, de simulation et de filtrage.
"""
from pathlib import Path
import pytest

from delete_citations.main import main, parse_args


@pytest.fixture
def sample_cli_directory(tmp_path: Path) -> Path:
    """Crée une arborescence complète pour les tests de commande CLI."""
    base = tmp_path / "projet_cli"
    base.mkdir()

    (base / "doc1.tex").write_text("Introduction [cite 1].", encoding="utf-8")
    (base / "propre.tex").write_text("Document sans citation.", encoding="utf-8")

    sub = base / "chapitre"
    sub.mkdir()
    (sub / "partie1.md").write_text("Markdown [cite 2] et suite [cite:3].", encoding="utf-8")
    (sub / "ignore.bin").write_bytes(b"\x00\x01\x02\x03")

    sub_cache = base / "__pycache__"
    sub_cache.mkdir()
    (sub_cache / "cached.tex").write_text("Cache [cite 99].", encoding="utf-8")

    return base


class TestCLIFiles:
    """Tests du point d'entrée CLI pour des fichiers individuels."""

    def test_main_fichier_existant(self, sample_tex_file: Path, capsys: pytest.CaptureFixture):
        code_retour = main([str(sample_tex_file)])
        captured = capsys.readouterr()

        assert code_retour == 0
        assert "3 citation(s) détectée(s)" in captured.out
        assert "sauvegardé avec succès" in captured.out

        contenu = sample_tex_file.read_text(encoding="utf-8")
        assert "[cite 1]" not in contenu

    def test_main_fichier_avec_sortie_personnalisee(
        self, sample_tex_file: Path, tmp_path: Path, capsys: pytest.CaptureFixture
    ):
        sortie = tmp_path / "sortie_nettoyee.tex"
        code_retour = main([str(sample_tex_file), "-o", str(sortie)])

        assert code_retour == 0
        assert sortie.exists()
        assert "[cite 1]" not in sortie.read_text(encoding="utf-8")
        assert "[cite 1]" in sample_tex_file.read_text(encoding="utf-8")

    def test_main_fichier_inexistant(self, tmp_path: Path, capsys: pytest.CaptureFixture):
        fichier_inexistant = tmp_path / "introuvable.tex"
        code_retour = main([str(fichier_inexistant)])
        captured = capsys.readouterr()

        assert code_retour == 1
        assert "Erreur : Le fichier" in captured.err

    def test_main_fichier_dry_run(self, sample_tex_file: Path, capsys: pytest.CaptureFixture):
        code_retour = main([str(sample_tex_file), "--dry-run"])
        captured = capsys.readouterr()

        assert code_retour == 0
        assert "[Simulation]" in captured.out
        # Le fichier ne doit pas avoir changé
        assert "[cite 1]" in sample_tex_file.read_text(encoding="utf-8")

    def test_main_fichier_avec_remplacement(self, sample_tex_file: Path, capsys: pytest.CaptureFixture):
        code_retour = main([str(sample_tex_file), "--replace", "[REF]"])
        captured = capsys.readouterr()

        assert code_retour == 0
        contenu = sample_tex_file.read_text(encoding="utf-8")
        assert "[cite 1]" not in contenu
        assert "[REF]" in contenu

    def test_main_fichier_quiet(self, sample_tex_file: Path, capsys: pytest.CaptureFixture):
        code_retour = main([str(sample_tex_file), "-q"])
        captured = capsys.readouterr()

        assert code_retour == 0
        assert captured.out == ""


class TestCLIDirectory:
    """Tests du point d'entrée CLI pour des dossiers récursifs."""

    def test_main_dossier_sur_place(self, sample_cli_directory: Path, capsys: pytest.CaptureFixture):
        code_retour = main([str(sample_cli_directory)])
        captured = capsys.readouterr()

        assert code_retour == 0
        assert "Traitement terminé" in captured.out
        assert "2 modifié(s)" in captured.out
        assert "3 citation(s) supprimée(s)" in captured.out

        # Vérification sur disque
        doc1 = (sample_cli_directory / "doc1.tex").read_text(encoding="utf-8")
        assert "[cite 1]" not in doc1

        partie1 = (sample_cli_directory / "chapitre" / "partie1.md").read_text(encoding="utf-8")
        assert "[cite 2]" not in partie1
        assert "[cite:3]" not in partie1

    def test_main_dossier_avec_destination(
        self, sample_cli_directory: Path, tmp_path: Path, capsys: pytest.CaptureFixture
    ):
        dossier_sortie = tmp_path / "sortie_projet"
        code_retour = main([str(sample_cli_directory), "-o", str(dossier_sortie)])
        captured = capsys.readouterr()

        assert code_retour == 0
        assert "Dossier sauvegardé avec succès" in captured.out

        # Le dossier de sortie doit contenir l'arbre complet nettoyé
        assert (dossier_sortie / "doc1.tex").exists()
        assert (dossier_sortie / "chapitre" / "partie1.md").exists()
        assert (dossier_sortie / "propre.tex").exists()

        # Le dossier source ne doit pas être altéré
        source_doc1 = (sample_cli_directory / "doc1.tex").read_text(encoding="utf-8")
        assert "[cite 1]" in source_doc1

    def test_main_dossier_dry_run(self, sample_cli_directory: Path, capsys: pytest.CaptureFixture):
        code_retour = main([str(sample_cli_directory), "-n"])
        captured = capsys.readouterr()

        assert code_retour == 0
        assert "[Simulation]" in captured.out
        assert "3 citation(s) supprimée(s)" in captured.out

        # Rien n'a changé sur le disque
        source_doc1 = (sample_cli_directory / "doc1.tex").read_text(encoding="utf-8")
        assert "[cite 1]" in source_doc1

    def test_main_dossier_filtre_extension(
        self, sample_cli_directory: Path, capsys: pytest.CaptureFixture
    ):
        code_retour = main([str(sample_cli_directory), "-e", ".tex"])
        captured = capsys.readouterr()

        assert code_retour == 0
        assert "1 modifié(s)" in captured.out
        assert "1 citation(s) supprimée(s)" in captured.out

        # Le fichier markdown ne doit pas avoir été touché
        partie1 = (sample_cli_directory / "chapitre" / "partie1.md").read_text(encoding="utf-8")
        assert "[cite 2]" in partie1

    def test_main_dossier_no_recursive(
        self, sample_cli_directory: Path, capsys: pytest.CaptureFixture
    ):
        code_retour = main([str(sample_cli_directory), "--no-recursive"])
        captured = capsys.readouterr()

        assert code_retour == 0
        # Seul doc1.tex à la racine est scanné et modifié
        assert "1 modifié(s)" in captured.out
        assert "1 citation(s) supprimée(s)" in captured.out

        # Le sous-dossier chapitre n'a pas été exploré
        partie1 = (sample_cli_directory / "chapitre" / "partie1.md").read_text(encoding="utf-8")
        assert "[cite 2]" in partie1

    def test_main_dossier_verbose(
        self, sample_cli_directory: Path, capsys: pytest.CaptureFixture
    ):
        code_retour = main([str(sample_cli_directory), "-v"])
        captured = capsys.readouterr()

        assert code_retour == 0
        assert "[MODIFIÉ]" in captured.out
        assert "[INTACT]" in captured.out

    def test_main_dossier_avec_remplacement(
        self, sample_cli_directory: Path, capsys: pytest.CaptureFixture
    ):
        code_retour = main([str(sample_cli_directory), "--replace", "[CITE]"])
        captured = capsys.readouterr()

        assert code_retour == 0
        assert "3 citation(s) remplacée(s)" in captured.out
        doc1 = (sample_cli_directory / "doc1.tex").read_text(encoding="utf-8")
        assert "[CITE]" in doc1

    def test_main_dossier_all_files(
        self, sample_cli_directory: Path, capsys: pytest.CaptureFixture
    ):
        code_retour = main([str(sample_cli_directory), "-a"])
        captured = capsys.readouterr()

        assert code_retour == 0
        # Doit s'exécuter sans erreur même avec le binaire
        assert "Traitement terminé" in captured.out

    def test_main_dossier_quiet(
        self, sample_cli_directory: Path, capsys: pytest.CaptureFixture
    ):
        code_retour = main([str(sample_cli_directory), "-q"])
        captured = capsys.readouterr()

        assert code_retour == 0
        assert captured.out == ""

    def test_main_dossier_avec_erreur_affiche_avertissement(
        self, sample_cli_directory: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
    ):
        def lever_erreur(*args, **kwargs):
            raise OSError("Erreur IO simulée")

        monkeypatch.setattr(Path, "mkdir", lever_erreur)
        code_retour = main([str(sample_cli_directory), "-o", str(sample_cli_directory.parent / "echec")])
        captured = capsys.readouterr()

        assert code_retour == 0
        assert "Avertissement" in captured.err

    def test_main_dossier_verbose_avec_erreur(
        self, sample_cli_directory: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
    ):
        def lever_erreur(*args, **kwargs):
            raise OSError("Erreur IO simulée")

        monkeypatch.setattr(Path, "mkdir", lever_erreur)
        code_retour = main([str(sample_cli_directory), "-o", str(sample_cli_directory.parent / "echec_verb"), "-v"])
        captured = capsys.readouterr()

        assert code_retour == 0
        assert "[ERREUR]" in captured.out



class TestCLIOptions:
    """Vérifie le parsing des arguments."""

    def test_parse_args_defaut(self):
        args = parse_args(["mon_dossier"])
        assert args.chemin == "mon_dossier"
        assert args.recursive is True
        assert args.output is None
        assert args.dry_run is False
        assert args.replace == ""
        assert args.verbose is False
        assert args.all is False

    def test_execution_en_tant_que_module(self):
        import subprocess
        import sys

        result = subprocess.run(
            [sys.executable, "-m", "delete_citations.main", "--version"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "delete-citations 0.2.0" in result.stdout or "delete-citations 0.2.0" in result.stderr

