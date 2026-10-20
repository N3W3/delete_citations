"""Tests d'intégration pour le point d'entrée CLI (main.py).

Ce fichier montre comment tester une interface en ligne de commande (CLI)
en capturant la sortie console (`capsys`) et en simulant les arguments passés.
"""
from pathlib import Path
import pytest

from delete_citations.main import main


class TestCLI:
    """Tests du point d'entrée CLI."""

    def test_main_fichier_existant(self, sample_tex_file: Path, capsys: pytest.CaptureFixture):
        code_retour = main([str(sample_tex_file)])
        captured = capsys.readouterr()

        assert code_retour == 0
        assert "3 citation(s) détectée(s)" in captured.out
        assert "sauvegardé avec succès" in captured.out

        # Vérifier que le fichier sur disque a bien été modifié
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
        # Le fichier d'origine n'a pas été écrasé
        assert "[cite 1]" in sample_tex_file.read_text(encoding="utf-8")

    def test_main_fichier_inexistant(self, tmp_path: Path, capsys: pytest.CaptureFixture):
        fichier_inexistant = tmp_path / "introuvable.tex"
        code_retour = main([str(fichier_inexistant)])
        captured = capsys.readouterr()

        assert code_retour == 1
        assert "Erreur : Le fichier" in captured.err
