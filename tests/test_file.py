"""Tests d'intégration et unitaires pour la classe `File`.

Ce fichier teste la manipulation des fichiers réels (lecture, modification et écriture).
Il utilise les fixtures définies dans `conftest.py` pour manipuler des fichiers temporaires
isolés sans altérer vos fichiers locaux.
"""
from pathlib import Path
import pytest

from delete_citations.file.file import File


class TestFileLecture:
    """Vérifie le chargement et la lecture de fichiers."""

    def test_lecture_fichier_existant(self, sample_tex_file: Path):
        mon_fichier = File(sample_tex_file)
        assert len(mon_fichier.lignes) > 0
        assert "documentclass" in mon_fichier.contenu

    def test_fichier_inexistant(self, tmp_path: Path):
        chemin_inexistant = tmp_path / "inexistant.tex"
        mon_fichier = File(chemin_inexistant)
        # Ne doit pas planter lors de l'instanciation si le fichier n'existe pas encore
        assert mon_fichier.lignes == []

    def test_propriete_contenu(self, sample_tex_file: Path, sample_tex_content: str):
        mon_fichier = File(sample_tex_file)
        assert mon_fichier.contenu == sample_tex_content


class TestFileOperations:
    """Vérifie la détection, modification et suppression des citations dans un objet File."""

    def test_detection_citations_dans_fichier(self, sample_tex_file: Path):
        mon_fichier = File(sample_tex_file)
        citations = mon_fichier.detection()
        assert citations == ["[cite 1]", "[cite 2]", "[cite 3]"]

    def test_detection_fichier_sans_citations(self, sample_clean_file: Path):
        mon_fichier = File(sample_clean_file)
        citations = mon_fichier.detection()
        assert citations == []

    def test_suppression_citations(self, sample_tex_file: Path):
        mon_fichier = File(sample_tex_file)
        assert len(mon_fichier.detection()) == 3

        mon_fichier.suppression()

        # Après suppression, plus aucune citation ne doit être détectée
        assert mon_fichier.detection() == []
        assert "[cite 1]" not in mon_fichier.contenu

    def test_alias_supression_fonctionne(self, sample_tex_file: Path):
        """Vérifie que la méthode 'supression' (avec un seul p) fonctionne à l'identique."""
        mon_fichier = File(sample_tex_file)
        mon_fichier.supression()
        assert mon_fichier.detection() == []

    def test_remplacer_citations(self, sample_tex_file: Path):
        mon_fichier = File(sample_tex_file)
        mon_fichier.remplacer("[REF]")
        assert "[REF]" in mon_fichier.contenu
        assert mon_fichier.detection() == []


class TestFileSauvegarde:
    """Vérifie l'enregistrement des fichiers sur le disque."""

    def test_sauvegarde_fichier_origine(self, sample_tex_file: Path):
        mon_fichier = File(sample_tex_file)
        mon_fichier.suppression()
        mon_fichier.sauvegarde()

        # Relire directement le fichier sur le disque pour vérifier que l'écriture est effective
        contenu_disque = sample_tex_file.read_text(encoding="utf-8")
        assert "[cite 1]" not in contenu_disque
        assert "[cite 2]" not in contenu_disque

    def test_sauvegarde_nouvelle_destination(self, sample_tex_file: Path, tmp_path: Path):
        mon_fichier = File(sample_tex_file)
        mon_fichier.suppression()

        fichier_sortie = tmp_path / "nouveau_dossier" / "resultat.tex"
        chemin_retour = mon_fichier.sauvegarde(destination=fichier_sortie)

        # Vérifier que le nouveau fichier a bien été créé avec le contenu nettoyé
        assert chemin_retour.exists()
        assert "[cite 1]" not in chemin_retour.read_text(encoding="utf-8")

        # Vérifier que le fichier d'origine n'a PAS été écrasé
        contenu_original = sample_tex_file.read_text(encoding="utf-8")
        assert "[cite 1]" in contenu_original
