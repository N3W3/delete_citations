"""Tests unitaires pour le module `cleaner`.

Ce fichier teste la logique pure (expressions régulières, détection, suppression et remplacement).
C'est la base du TDD (Test-Driven Development) : tester des fonctions pures et isolées.
"""
import pytest

from delete_citations.cleaner import (
    detect_citations,
    remove_citations,
    replace_citations,
)


class TestDetectCitations:
    """Regroupe les tests liés à la fonction detect_citations."""

    def test_detection_single_citation(self):
        texte = "Voici une référence [cite 42] dans un paragraphe."
        resultat = detect_citations(texte)
        assert resultat == ["[cite 42]"]

    def test_detection_multiple_citations(self):
        texte = "Début [cite 1], milieu [cite 2] et fin [cite 3]."
        resultat = detect_citations(texte)
        assert resultat == ["[cite 1]", "[cite 2]", "[cite 3]"]

    def test_detection_no_citations(self):
        texte = "Un texte tout à fait ordinaire sans citation."
        resultat = detect_citations(texte)
        assert resultat == []

    @pytest.mark.parametrize(
        "texte, attendu",
        [
            ("Format classique [cite 1]", ["[cite 1]"]),
            ("Format sans espace [cite1]", ["[cite1]"]),
            ("Format avec deux-points [cite:1]", ["[cite:1]"]),
            ("Format deux-points avec espace [cite: 99]", ["[cite: 99]"]),
            ("Nombreux chiffres [cite 123456]", ["[cite 123456]"]),
        ],
    )
    def test_detection_formats_varies(self, texte, attendu):
        """Teste plusieurs variations du format de citation avec @pytest.mark.parametrize."""
        assert detect_citations(texte) == attendu

    @pytest.mark.parametrize(
        "texte_invalide",
        [
            "Crochets sans mot clef [12]",
            "Texte dans les crochets [cite article]",
            "Balise incomplète [cite ]",
            "Balise différente (cite 1)",
        ],
    )
    def test_non_detection_fausses_citations(self, texte_invalide):
        """Vérifie que des motifs incorrects ne sont pas pris pour des citations."""
        assert detect_citations(texte_invalide) == []


class TestRemoveCitations:
    """Regroupe les tests liés à la suppression de citations."""

    def test_suppression_simple(self):
        texte = "Texte avec [cite 1] citation."
        resultat = remove_citations(texte)
        assert resultat == "Texte avec  citation."

    def test_suppression_multiples(self):
        texte = "A [cite 1] B [cite 2] C [cite 3]"
        resultat = remove_citations(texte)
        assert resultat == "A  B  C "

    def test_suppression_aucun_effet_si_vide(self):
        texte = "Texte inchangé."
        assert remove_citations(texte) == texte

    def test_suppression_multiligne(self):
        texte = "Ligne 1 [cite 1]\nLigne 2 [cite 2]\nLigne 3"
        attendu = "Ligne 1 \nLigne 2 \nLigne 3"
        assert remove_citations(texte) == attendu


class TestReplaceCitations:
    """Regroupe les tests liés au remplacement de citations par un texte personnalisé."""

    def test_remplacement_par_placeholder(self):
        texte = "Résultat selon l'auteur [cite 4]."
        resultat = replace_citations(texte, replacement="[REF]")
        assert resultat == "Résultat selon l'auteur [REF]."

    def test_remplacement_par_chaine_vide_equivaut_a_suppression(self):
        texte = "Test [cite 99] fin."
        assert replace_citations(texte, "") == remove_citations(texte)
