"""Unit tests for the PMU'B LONAB parsers."""

import os
import unittest
from app.parser.resultat_parser import ResultatParser, parse_resultat_document
from app.parser.rep_parser import RepParser, parse_rep_document
from app.parser.document_classifier import DocumentClassifier, classify_document, DocumentType
from app.quality.validator import QualityValidator
from app.models.parser_models import ParsedDocument, ParsedRepDocument

SAMPLE_DIR = r"C:\Users\Lenovo\Desktop\PMU\echantillon\Nouveau dossier"


class TestResultatParser(unittest.TestCase):
    """Tests pour le parser de résultats (QUARTE, TIERCE)."""
    
    def setUp(self):
        self.parser = ResultatParser()
    
    def test_tierce_04_01_2025(self):
        """Test TIERCE DU SAMEDI 04/01/2025 - ARR :6-2-12"""
        pdf_path = os.path.join(SAMPLE_DIR, "Res_04_01_2025_TIERCE.pdf")
        result = self.parser.parse(pdf_path)
        
        self.assertEqual(result.doc_type, "RESULTAT")
        self.assertIsNotNone(result.resultat)
        
        r = result.resultat
        self.assertEqual(r.date, "2025-01-04")
        self.assertEqual(r.type_pari, "TIERCE")
        self.assertEqual(r.arrivee_raw, "6-2-12")
        self.assertEqual(r.arrivee, [6, 2, 12])
        self.assertEqual(len(r.arrivee), 3)  # TIERCE = 3 chevaux
        self.assertEqual(r.npo, 0)
        self.assertEqual(r.np, 0)
        
        # Gains
        self.assertEqual(r.gains_ordre_euros, 20000)
        self.assertEqual(r.gains_desordre_euros, 2000)
        self.assertEqual(r.nb_gagnants_ordre, 3612)
        self.assertEqual(r.nb_gagnants_desordre, 29520)
    
    def test_quarte_06_01_2025(self):
        """Test QUARTE DU LUNDI 06/01/2025 - ARR :14-5-4-3"""
        pdf_path = os.path.join(SAMPLE_DIR, "Res_06_01_2025_QUARTE.pdf")
        result = self.parser.parse(pdf_path)
        
        self.assertEqual(result.doc_type, "RESULTAT")
        self.assertIsNotNone(result.resultat)
        
        r = result.resultat
        self.assertEqual(r.date, "2025-01-06")
        self.assertEqual(r.type_pari, "QUARTE")
        self.assertEqual(r.arrivee_raw, "14-5-4-3")
        self.assertEqual(r.arrivee, [14, 5, 4, 3])
        self.assertEqual(len(r.arrivee), 4)  # QUARTE = 4 chevaux
        self.assertEqual(r.npo, 0)
        self.assertEqual(r.np, 0)
        
        # Gains
        self.assertEqual(r.gains_ordre_euros, 8799000)
        self.assertEqual(r.gains_desordre_euros, 556500)
        self.assertEqual(r.nb_gagnants_ordre, 7)
        self.assertEqual(r.nb_gagnants_desordre, 166)
    
    def test_tierce_11_01_2025(self):
        """Test TIERCE DU SAMEDI 11/01/2025 - ARR :15-1-4"""
        pdf_path = os.path.join(SAMPLE_DIR, "Res_11_01_2025_TIERCE_0.pdf")
        result = self.parser.parse(pdf_path)
        
        self.assertEqual(result.doc_type, "RESULTAT")
        self.assertIsNotNone(result.resultat)
        
        r = result.resultat
        self.assertEqual(r.date, "2025-01-11")
        self.assertEqual(r.type_pari, "TIERCE")
        self.assertEqual(r.arrivee_raw, "15-1-4")
        self.assertEqual(r.arrivee, [15, 1, 4])
        self.assertEqual(len(r.arrivee), 3)  # TIERCE = 3 chevaux
        
        # Gains
        self.assertEqual(r.gains_ordre_euros, 653500)
        self.assertEqual(r.gains_desordre_euros, 130500)
        self.assertEqual(r.nb_gagnants_ordre, 120)
        self.assertEqual(r.nb_gagnants_desordre, 472)
    
    def test_arrival_length_validation_tierce(self):
        """Test que la validation de longueur d'arrivée fonctionne pour TIERCE."""
        pdf_path = os.path.join(SAMPLE_DIR, "Res_04_01_2025_TIERCE.pdf")
        result = self.parser.parse(pdf_path)
        
        is_valid, error = self.parser.validate_arrival_length(result.resultat)
        self.assertTrue(is_valid)
        self.assertIsNone(error)
    
    def test_arrival_length_validation_quarte(self):
        """Test que la validation de longueur d'arrivée fonctionne pour QUARTE."""
        pdf_path = os.path.join(SAMPLE_DIR, "Res_06_01_2025_QUARTE.pdf")
        result = self.parser.parse(pdf_path)
        
        is_valid, error = self.parser.validate_arrival_length(result.resultat)
        self.assertTrue(is_valid)
        self.assertIsNone(error)


class TestRepParser(unittest.TestCase):
    """Tests pour le parser de rapports (REP)."""
    
    def setUp(self):
        self.parser = RepParser()
    
    def test_rep_41_15_01_2025(self):
        """Test REP41_15_01_2025.pdf"""
        pdf_path = os.path.join(SAMPLE_DIR, "Rep41_15_01_2025.pdf")
        result = self.parser.parse(pdf_path)
        
        self.assertEqual(result.doc_type, "REP")
        self.assertIsNotNone(result.rep_document)
        
        r = result.rep_document
        # Date du document
        self.assertEqual(r.date_document, "2025-01-15")
        self.assertEqual(r.date_document_raw, "15/01/2025")
        
        # Date de la course cible
        self.assertEqual(r.date_course_cible, "2025-01-17")
        self.assertEqual(r.date_course_cible_raw, "VENDREDI 17/01/2025")
        
        # Type de jeu
        self.assertEqual(r.game_type, "4+1")
        
        # Montant du rapport
        self.assertEqual(r.report_ordre_raw, "59 386 377")
        self.assertEqual(r.report_ordre, 59386377)
        
        # Pas d'arrivée pour un REP
        self.assertFalse(hasattr(r, 'arrivee') and r.arrivee)
    
    def test_rep_dates_are_different(self):
        """Test que la date du document et la date de course cible sont différentes."""
        pdf_path = os.path.join(SAMPLE_DIR, "Rep41_15_01_2025.pdf")
        result = self.parser.parse(pdf_path)
        
        r = result.rep_document
        self.assertNotEqual(r.date_document, r.date_course_cible)


class TestDocumentClassifier(unittest.TestCase):
    """Tests pour le classificateur de documents."""
    
    def setUp(self):
        self.classifier = DocumentClassifier()
    
    def test_classify_tierce(self):
        """Test classification d'un TIERCE."""
        text = "TIERCE DU SAMEDI 04/01/2025\nARR :6-2-12"
        result = self.classifier.classify("Res_04_01_2025_TIERCE.pdf", text)
        
        self.assertEqual(result.document_type, DocumentType.RESULTAT_TIERCE)
        self.assertEqual(result.game_type, "TIERCE")
        self.assertGreater(result.confidence, 0.8)
    
    def test_classify_quarte(self):
        """Test classification d'un QUARTE."""
        text = "QUARTE DU LUNDI 06/01/2025\nARR :14-5-4-3"
        result = self.classifier.classify("Res_06_01_2025_QUARTE.pdf", text)
        
        self.assertEqual(result.document_type, DocumentType.RESULTAT_QUARTE)
        self.assertEqual(result.game_type, "QUARTE")
        self.assertGreater(result.confidence, 0.8)
    
    def test_classify_rep(self):
        """Test classification d'un REP."""
        text = 'REPORT ORD. "4+1" DU VENDREDI 17/01/2025:\n59 386 377\n15/01/2025'
        result = self.classifier.classify("Rep41_15_01_2025.pdf", text)
        
        self.assertEqual(result.document_type, DocumentType.REP)
        self.assertGreater(result.confidence, 0.8)
    
    def test_classify_ecd(self):
        """Test classification d'un ECD."""
        text = "ESPACE COURSE EN DIRECT\nRECAPITULATIF DES ARRIVEES DES COURSES"
        result = self.classifier.classify("ECD_08-09-2026_R1_0.pdf", text)
        
        self.assertEqual(result.document_type, DocumentType.ECD)
        self.assertGreater(result.confidence, 0.8)
    
    def test_classify_programme(self):
        """Test classification d'un PROGRAMME (Journal)."""
        text = "JOURNAL HIPPIQUE PMU'B\n16 CONCURRENTS\nPRIX DE TEST"
        result = self.classifier.classify("JH_PMUB_DU_04-01-2025.pdf", text)
        
        self.assertEqual(result.document_type, DocumentType.PROGRAMME)
        self.assertGreater(result.confidence, 0.8)


class TestQualityValidator(unittest.TestCase):
    """Tests pour le validateur de qualité."""
    
    def setUp(self):
        self.validator = QualityValidator()
    
    def test_validate_tierce_success(self):
        """Test validation d'un TIERCE correct."""
        pdf_path = os.path.join(SAMPLE_DIR, "Res_04_01_2025_TIERCE.pdf")
        parser = ResultatParser()
        result = parser.parse(pdf_path)
        
        validated = self.validator.validate(result)
        
        self.assertEqual(validated.quality_status, "SUCCESS")
        self.assertGreaterEqual(validated.quality_score, 90)
    
    def test_validate_quarte_success(self):
        """Test validation d'un QUARTE correct."""
        pdf_path = os.path.join(SAMPLE_DIR, "Res_06_01_2025_QUARTE.pdf")
        parser = ResultatParser()
        result = parser.parse(pdf_path)
        
        validated = self.validator.validate(result)
        
        self.assertEqual(validated.quality_status, "SUCCESS")
        self.assertGreaterEqual(validated.quality_score, 90)
    
    def test_validate_rep_success(self):
        """Test validation d'un REP correct."""
        pdf_path = os.path.join(SAMPLE_DIR, "Rep41_15_01_2025.pdf")
        parser = RepParser()
        result = parser.parse(pdf_path)
        
        validated = self.validator.validate(result)
        
        self.assertEqual(validated.quality_status, "SUCCESS")
        self.assertGreaterEqual(validated.quality_score, 90)


class TestArriveeParsingEdgeCases(unittest.TestCase):
    """Tests pour les cas limites du parsing d'arrivée."""
    
    def test_arrivee_with_spaces(self):
        """Test ARR avec espaces: 'ARR : 14 - 5 - 4 - 3'"""
        from app.parser.normalizer import parse_arrivee
        result = parse_arrivee("14 - 5 - 4 - 3")
        self.assertEqual(result, [14, 5, 4, 3])
    
    def test_arrivee_without_spaces(self):
        """Test ARR sans espaces: 'ARR :14-5-4-3'"""
        from app.parser.normalizer import parse_arrivee
        result = parse_arrivee("14-5-4-3")
        self.assertEqual(result, [14, 5, 4, 3])
    
    def test_arrivee_tierce_3_numbers(self):
        """Test ARR TIERCE avec 3 numéros."""
        from app.parser.normalizer import parse_arrivee
        result = parse_arrivee("6-2-12")
        self.assertEqual(result, [6, 2, 12])


if __name__ == "__main__":
    unittest.main()