"""
PMU'B LONAB Scraper — Point d'entrée principal.

Usage:
    python main.py --dry-run                        # Analyse sans téléchargement
    python main.py --dry-run --source programmes     # Programmes uniquement
    python main.py --download                       # Télécharge tout
    python main.py --download --source programmes   # Programmes uniquement
    python main.py --download --source resultats    # Résultats uniquement
    python main.py --parse-sample                   # Parser l'échantillon
    python main.py --validate-sample                # Valider l'échantillon
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import List

from app.downloader.pdf_downloader import PDFDownloader
from app.models.document import DocumentMetadata, DocumentStatus
from app.models.parser_models import ParsedDocument, ParsedECDDocument, CourseDirect, ParsedRepDocument
from app.parser.journal_parser import JournalParser
from app.parser.resultat_parser import ResultatParser
from app.parser.course_direct_parser import ECDParser
from app.parser.rep_parser import RepParser
from app.parser.document_classifier import DocumentClassifier, classify_document
from app.parser.matcher import JournalResultMatcher
from app.quality.validator import QualityValidator
from app.scraper.programmes import ProgrammesScraper
from app.scraper.resultats import ResultatsScraper
from app.scraper.course_direct import CourseDirectScraper
from app.enrichment.enricher import PMUDataEnricher
from app.prediction.race_predictor import LonabPredictor
from app.utils.logging_config import setup_logging, get_logger

# Répertoires
PROJECT_DIR = Path(__file__).parent
DATA_DIR = PROJECT_DIR / "data"
METADATA_FILE = DATA_DIR / "metadata" / "documents.jsonl"
SAMPLE_DIR = Path(r"C:\Users\Lenovo\Desktop\PMU\echantillon")
PROCESSED_DIR = DATA_DIR / "processed"
QUALITY_DIR = DATA_DIR / "quality"

logger = get_logger("main")


def load_existing_metadata() -> dict[str, DocumentMetadata]:
    """
    Charge les métadonnées existantes depuis le fichier JSONL.

    Returns:
        Dictionnaire {pdf_url: DocumentMetadata} des documents déjà connus.
    """
    existing: dict[str, DocumentMetadata] = {}

    if not METADATA_FILE.exists():
        return existing

    try:
        with open(METADATA_FILE, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    doc = DocumentMetadata.from_jsonl(line)
                    existing[doc.pdf_url] = doc
                except Exception as e:
                    logger.warning("Erreur parsing ligne %d du fichier metadata: %s", line_num, e)

        logger.info("Métadonnées chargées: %d documents existants", len(existing))
    except OSError as e:
        logger.error("Erreur lecture du fichier metadata: %s", e)

    return existing


def save_metadata(documents: list[DocumentMetadata]) -> None:
    """
    Enregistre les métadonnées dans le fichier JSONL.

    Écrase le fichier existant avec l'ensemble complet des métadonnées.
    """
    METADATA_FILE.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(METADATA_FILE, "w", encoding="utf-8") as f:
            for doc in documents:
                f.write(doc.to_jsonl() + "\n")

        logger.info("Métadonnées enregistrées: %d documents dans %s", len(documents), METADATA_FILE)
    except OSError as e:
        logger.error("Erreur écriture du fichier metadata: %s", e)


def merge_documents(
    existing: dict[str, DocumentMetadata],
    new_docs: list[DocumentMetadata],
) -> list[DocumentMetadata]:
    """
    Fusionne les documents existants avec les nouveaux découverts.

    Les documents déjà téléchargés conservent leur statut.
    Les nouveaux documents sont ajoutés.

    Returns:
        Liste fusionnée.
    """
    merged = dict(existing)  # copie

    new_count = 0
    for doc in new_docs:
        if doc.pdf_url not in merged:
            merged[doc.pdf_url] = doc
            new_count += 1
        else:
            # Conserver le document existant (déjà téléchargé ou en erreur)
            pass

    logger.info("Fusion: %d existants + %d nouveaux = %d total", len(existing), new_count, len(merged))
    return list(merged.values())


def display_dry_run(title: str, documents: list[DocumentMetadata]) -> None:
    """Affiche les documents trouvés en mode dry-run."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"  Documents trouvés : {len(documents)}")
    print(f"{'='*60}")

    if not documents:
        print("  (aucun document trouvé)")
        return

    for i, doc in enumerate(documents, 1):
        date_str = str(doc.publication_date) if doc.publication_date else "date inconnue"
        type_str = doc.document_type.value.replace("_", " ").title()
        status_indicator = ""
        if doc.status == DocumentStatus.DOWNLOADED:
            status_indicator = " [déjà téléchargé]"
        elif doc.status == DocumentStatus.SKIPPED:
            status_indicator = " [skippé]"
        elif doc.status == DocumentStatus.FAILED:
            status_indicator = " [échec précédent]"

        print(f"  [{i:3d}] {date_str} — {type_str}{status_indicator}")
        print(f"        {doc.pdf_url}")

    print()


def parse_sample() -> List[ParsedDocument]:
    """Parse les PDFs de l'échantillon (JOURNAL, RESULTAT, REP)."""
    if not SAMPLE_DIR.exists():
        logger.error("Dossier d'échantillon introuvable: %s", SAMPLE_DIR)
        return []
    
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    
    journal_parser = JournalParser()
    resultat_parser = ResultatParser()
    ecd_parser = ECDParser()
    rep_parser = RepParser()
    classifier = DocumentClassifier()
    
    all_parsed: List[ParsedDocument] = []
    all_rep_parsed: List[ParsedRepDocument] = []
    
    # Scanner récursivement
    pdf_files = list(SAMPLE_DIR.rglob('*.pdf'))
    
    for f in sorted(pdf_files):
        logger.info("Parsing %s...", f.name)
        try:
            # Extraire le texte pour classification
            import fitz
            doc = fitz.open(str(f))
            full_text = ""
            for page in doc:
                full_text += page.get_text() + "\n"
            doc.close()
            
            # Classifier le document
            classification = classifier.classify(f.name, full_text)
            logger.info("  Classification: %s (confidence=%.2f, game_type=%s)", 
                       classification.document_type.value, classification.confidence, classification.game_type)
            
            parser_type = classifier.get_parser_type(classification)
            
            if parser_type == 'journal':
                parsed = journal_parser.parse(str(f))
                all_parsed.append(parsed)
            elif parser_type == 'resultat':
                parsed = resultat_parser.parse(str(f))
                all_parsed.append(parsed)
            elif parser_type == 'ecd':
                parsed = ecd_parser.parse(str(f))
                # ECD sont gérés séparément
                parsed.save_json(str(PROCESSED_DIR))
                logger.info("  -> OK (ECD)")
                continue
            elif parser_type == 'rep':
                parsed = rep_parser.parse(str(f))
                all_rep_parsed.append(parsed)
            else:
                logger.warning("  Type inconnu, tentative avec resultat_parser")
                parsed = resultat_parser.parse(str(f))
                all_parsed.append(parsed)
            
            if parser_type in ('journal', 'resultat', 'rep'):
                parsed.save_json(str(PROCESSED_DIR))
                logger.info("  -> OK (%s)", parsed.doc_type)
        except Exception as e:
            logger.error("  ERREUR: %s", e)
    
    # Sauvegarder le combiné (journaux + résultats)
    combined_file = PROCESSED_DIR / "all_parsed.json"
    with open(combined_file, 'w', encoding='utf-8') as out:
        json.dump([p.to_dict() for p in all_parsed], out, ensure_ascii=False, indent=2)
    
    # Sauvegarder les REP séparément
    if all_rep_parsed:
        rep_combined_file = PROCESSED_DIR / "rep_parsed.json"
        with open(rep_combined_file, 'w', encoding='utf-8') as out:
            json.dump([p.to_dict() for p in all_rep_parsed], out, ensure_ascii=False, indent=2)
        logger.info("REP parsés: %d fichiers -> %s", len(all_rep_parsed), rep_combined_file)
    
    logger.info("Parsing terminé: %d fichiers (JOURNAL/RESULTAT) -> %s", len(all_parsed), combined_file)
    return all_parsed


def parse_ecd_sample() -> List[ParsedECDDocument]:
    """Parse les PDFs ECD de l'échantillon."""
    if not SAMPLE_DIR.exists():
        logger.error("Dossier d'échantillon introuvable: %s", SAMPLE_DIR)
        return []
    
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    
    ecd_parser = ECDParser()
    
    all_parsed: List[ParsedECDDocument] = []
    
    for f in sorted(SAMPLE_DIR.iterdir()):
        if f.suffix.lower() == '.pdf' and f.name.upper().startswith('ECD'):
            logger.info("Parsing ECD %s...", f.name)
            try:
                parsed = ecd_parser.parse(str(f))
                
                # Sauvegarder individuellement
                parsed.save_json(str(PROCESSED_DIR))
                all_parsed.append(parsed)
                logger.info("  -> OK (ECD)")
            except Exception as e:
                logger.error("  ERREUR: %s", e)
    
    # Sauvegarder le combiné
    combined_file = PROCESSED_DIR / "ecd_parsed.json"
    with open(combined_file, 'w', encoding='utf-8') as out:
        json.dump([p.to_dict() for p in all_parsed], out, ensure_ascii=False, indent=2)
    
    logger.info("Parsing ECD terminé: %d fichiers -> %s", len(all_parsed), combined_file)
    return all_parsed


def validate_ecd_sample(parsed_docs: List[ParsedECDDocument] = None) -> List[ParsedECDDocument]:
    """Valide les documents ECD parsés et génère les rapports qualité."""
    if parsed_docs is None:
        # Charger depuis le fichier combiné
        combined_file = PROCESSED_DIR / "ecd_parsed.json"
        if not combined_file.exists():
            logger.error("Fichier combiné ECD introuvable. Lancez --parse-ecd-sample d'abord.")
            return []
        
        with open(combined_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Reconstruire les objets à partir des dicts JSON
        from app.models.parser_models import ParsedECDDocument, ECDDocument, CourseDirect, CourseDirectArrival, CourseDirectBet
        
        def dict_to_ecd_doc(edd: dict) -> ECDDocument:
            return ECDDocument(**edd)
        
        def dict_to_course_direct(cd: dict) -> CourseDirect:
            arrival = None
            if cd.get('arrivee'):
                arr_data = cd['arrivee']
                # Handle nested gains_total dict
                gains_total_raw = ""
                gains_total_euros = None
                if isinstance(arr_data.get('gains_total'), dict):
                    gains_total_raw = arr_data['gains_total'].get('raw', '')
                    gains_total_euros = arr_data['gains_total'].get('euros')
                elif arr_data.get('gains_total_raw'):
                    gains_total_raw = arr_data.get('gains_total_raw', '')
                    gains_total_euros = arr_data.get('gains_total_euros')
                
                arrival = CourseDirectArrival(
                    arrivee_raw=arr_data.get('arrivee_raw', ''),
                    positions=arr_data.get('positions', []),
                    gains_total_raw=gains_total_raw,
                    gains_total_euros=gains_total_euros
                )
            paris = []
            for p in cd.get('paris', []):
                # Handle nested combinaison and montant dicts
                comb_raw = ""
                comb_norm = []
                if isinstance(p.get('combinaison'), dict):
                    comb_raw = p['combinaison'].get('raw', '')
                    comb_norm = p['combinaison'].get('normalized', [])
                elif p.get('combinaison_raw'):
                    comb_raw = p.get('combinaison_raw', '')
                    comb_norm = p.get('combinaison_normalized', [])
                
                mont_raw = ""
                mont_euros = None
                if isinstance(p.get('montant'), dict):
                    mont_raw = p['montant'].get('raw', '')
                    mont_euros = p['montant'].get('euros')
                elif p.get('montant_raw'):
                    mont_raw = p.get('montant_raw', '')
                    mont_euros = p.get('montant_euros')
                
                paris.append(CourseDirectBet(
                    type_pari=p.get('type_pari', ''),
                    combinaison_raw=comb_raw,
                    combinaison_normalized=comb_norm,
                    montant_raw=mont_raw,
                    montant_euros=mont_euros,
                    nb_paris=p.get('nb_paris'),
                    position=p.get('position'),
                    uncertain=p.get('uncertain', False)
                ))
            return CourseDirect(
                course_id=cd.get('course_id', ''),
                document_id=cd.get('document_id', ''),
                numero_course=cd.get('numero_course', 0),
                arrivee=arrival,
                paris=paris,
                page_num=cd.get('page_num', 0),
                y_position=cd.get('y_position', 0.0),
                raw_text=cd.get('raw_text', '')
            )
        
        parsed_docs = []
        for d in data:
            ecd_doc = dict_to_ecd_doc(d['ecd_document']) if d.get('ecd_document') else None
            courses = [dict_to_course_direct(c) for c in d.get('courses', [])]
            
            pdoc = ParsedECDDocument(
                filename=d['filename'],
                doc_type=d['doc_type'],
                date_publication=d['date_publication'],
                pages=d['pages'],
                ecd_document=ecd_doc,
                courses=courses
            )
            parsed_docs.append(pdoc)
    
    QUALITY_DIR.mkdir(parents=True, exist_ok=True)
    
    # Validation basique pour ECD
    from app.quality.validator import QualityValidator
    validator = QualityValidator()
    
    validated = []
    for parsed in parsed_docs:
        # Validation ECD spécifique
        issues = []
        
        # Vérifications de base
        if not parsed.ecd_document or not parsed.ecd_document.date:
            issues.append(("date", "ERROR", "Date manquante"))
        if not parsed.ecd_document or not parsed.ecd_document.reunion:
            issues.append(("reunion", "WARNING", "Réunion manquante"))
        if not parsed.ecd_document or not parsed.ecd_document.hippodrome:
            issues.append(("hippodrome", "WARNING", "Hippodrome manquant"))
        if len(parsed.courses) == 0:
            issues.append(("courses", "ERROR", "Aucune course détectée"))
        
        # Vérifier chaque course
        for course in parsed.courses:
            if course.numero_course <= 0:
                issues.append((f"course_{course.numero_course}_num", "ERROR", "Numéro de course invalide"))
            if not course.arrivee or not course.arrivee.positions:
                issues.append((f"course_{course.numero_course}_arrivee", "WARNING", "Arrivée manquante"))
        
        # Calculer score
        errors = sum(1 for i in issues if i[1] == "ERROR")
        warnings = sum(1 for i in issues if i[1] == "WARNING")
        score = 100 - errors * 20 - warnings * 5
        score = max(0, score)
        
        if score >= 90:
            status = "SUCCESS"
        elif score >= 70:
            status = "PARTIAL"
        else:
            status = "FAILED"
        
        parsed.quality_score = score
        parsed.quality_status = status
        parsed.quality_details = {
            'total_issues': len(issues),
            'errors': errors,
            'warnings': warnings,
            'courses_parsed': len(parsed.courses),
            'arrivals_parsed': sum(1 for c in parsed.courses if c.arrivee and c.arrivee.positions),
            'bets_parsed': sum(len(c.paris) for c in parsed.courses)
        }
        parsed.parsing_errors = [f"{i[1]}: {i[0]} - {i[2]}" for i in issues]
        
        validated.append(parsed)
    
    # Exporter les issues
    import csv
    issues_file = QUALITY_DIR / "ecd_errors.csv"
    with open(issues_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['filename', 'course_id', 'field', 'severity', 'message'])
        for p in validated:
            for issue in p.parsing_errors:
                parts = issue.split(': ', 2)
                if len(parts) >= 3:
                    writer.writerow([p.filename, '', parts[0], parts[1], parts[2]])
    
    # Rapport qualité global
    report_file = QUALITY_DIR / "ecd_quality_report.csv"
    with open(report_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'filename', 'doc_type', 'date', 'reunion', 'hippodrome',
            'quality_score', 'quality_status',
            'courses_total', 'courses_parsed', 'arrivals_parsed', 'bets_parsed',
            'errors', 'warnings'
        ])
        
        for p in validated:
            ecd = p.ecd_document
            writer.writerow([
                p.filename, p.doc_type, 
                ecd.date if ecd else '',
                ecd.reunion if ecd else '',
                ecd.hippodrome if ecd else '',
                p.quality_score, p.quality_status,
                len(p.courses),
                p.quality_details.get('courses_parsed', 0),
                p.quality_details.get('arrivals_parsed', 0),
                p.quality_details.get('bets_parsed', 0),
                p.quality_details.get('errors', 0),
                p.quality_details.get('warnings', 0)
            ])
    
    # Cross-source validation (ECD vs Resultats)
    _cross_validate_ecd_results(validated)
    
    logger.info("Validation ECD terminée: %s, %s", issues_file, report_file)
    
    # Afficher résumé
    print_ecd_validation_summary(validated)
    
    return validated


def _cross_validate_ecd_results(ecd_docs: List[ParsedECDDocument]):
    """Compare les ECD avec les résultats existants."""
    # Charger les résultats parsés
    combined_file = PROCESSED_DIR / "all_parsed.json"
    if not combined_file.exists():
        return
    
    with open(combined_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Construire un index des résultats par date/réunion
    resultats = {}
    for d in data:
        if d['doc_type'] == 'RESULTAT' and d.get('resultat'):
            r = d['resultat']
            key = (r.get('date'), r.get('course_id'))
            resultats[key] = r
    
    # Comparer
    mismatches = []
    for ecd_doc in ecd_docs:
        ecd = ecd_doc.ecd_document
        if not ecd:
            continue
        
        for course in ecd_doc.courses:
            if not course.arrivee or not course.arrivee.positions:
                continue
            
            # Chercher résultat correspondant
            result_key = (ecd.date, f"{ecd.document_id}_C{course.numero_course}")
            if result_key in resultats:
                res = resultats[result_key]
                res_arrivee = res.get('arrivee', [])
                
                if res_arrivee != course.arrivee.positions:
                    mismatches.append({
                        'ecd_filename': ecd_doc.filename,
                        'resultat_filename': '',  # À retrouver
                        'date': ecd.date,
                        'reunion': ecd.reunion,
                        'course_num': course.numero_course,
                        'ecd_arrivee': course.arrivee.positions,
                        'resultat_arrivee': res_arrivee,
                        'match': 'ARRIVAL_MISMATCH'
                    })
    
    # Sauvegarder les mismatches
    if mismatches:
        mismatch_file = QUALITY_DIR / "ecd_mismatches.csv"
        with open(mismatch_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'ecd_filename', 'resultat_filename', 'date', 'reunion', 'course_num',
                'ecd_arrivee', 'resultat_arrivee', 'match'
            ])
            for m in mismatches:
                writer.writerow([
                    m['ecd_filename'], m['resultat_filename'], m['date'],
                    m['reunion'], m['course_num'],
                    '-'.join(map(str, m['ecd_arrivee'])),
                    '-'.join(map(str, m['resultat_arrivee'])),
                    m['match']
                ])
        logger.warning("%d conflits d'arrivée détectés (ECD vs Résultat)", len(mismatches))


def print_ecd_validation_summary(docs: List[ParsedECDDocument]):
    """Affiche un résumé de validation ECD lisible."""
    print(f"\n{'='*60}")
    print("  RAPPORT DE VALIDATION ECD ÉCHANTILLON")
    print(f"{'='*60}")
    
    total = len(docs)
    success = sum(1 for d in docs if d.quality_status == 'SUCCESS')
    partial = sum(1 for d in docs if d.quality_status == 'PARTIAL')
    failed = sum(1 for d in docs if d.quality_status == 'FAILED')
    avg_score = sum(d.quality_score for d in docs) / total if total > 0 else 0
    
    total_courses = sum(len(d.courses) for d in docs)
    total_arrivals = sum(
        sum(1 for c in d.courses if c.arrivee and c.arrivee.positions)
        for d in docs
    )
    total_bets = sum(len(c.paris) for d in docs for c in d.courses)
    
    print(f"\n  PDF ECD analysés  : {total}")
    print(f"  Courses totales   : {total_courses}")
    print(f"  Arrivées parsées  : {total_arrivals}")
    print(f"  Paris/Gains parsés: {total_bets}")
    print(f"\n  SUCCESS           : {success}")
    print(f"  PARTIAL           : {partial}")
    print(f"  FAILED            : {failed}")
    print(f"  Qualité moyenne   : {avg_score:.1f}/100")
    
    print(f"\n  Détail par document:")
    for d in docs:
        ecd = d.ecd_document
        print(f"    {d.filename}")
        print(f"      Date: {ecd.date if ecd else 'N/A'} | Réunion: {ecd.reunion if ecd else 'N/A'} | Hippodrome: {ecd.hippodrome if ecd else 'N/A'}")
        print(f"      Courses: {len(d.courses)} | Score: {d.quality_score} | Status: {d.quality_status}")
        if d.parsing_errors:
            for err in d.parsing_errors[:3]:
                print(f"      - {err}")
            if len(d.parsing_errors) > 3:
                print(f"      ... et {len(d.parsing_errors) - 3} autres")
    
    print(f"\n  Rapports générés:")
    print(f"    {QUALITY_DIR}/ecd_errors.csv")
    print(f"    {QUALITY_DIR}/ecd_quality_report.csv")
    print(f"    {QUALITY_DIR}/ecd_mismatches.csv (si conflits)")
    print(f"{'='*60}")


def validate_sample(parsed_docs: List[ParsedDocument] = None) -> List[ParsedDocument]:
    """Valide les documents parsés et génère les rapports qualité (JOURNAL, RESULTAT, REP)."""
    if parsed_docs is None:
        # Charger depuis les fichiers combinés
        combined_file = PROCESSED_DIR / "all_parsed.json"
        if not combined_file.exists():
            logger.error("Fichier combiné introuvable. Lancez --parse-sample d'abord.")
            return []
        
        with open(combined_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Aussi charger les REP
        rep_file = PROCESSED_DIR / "rep_parsed.json"
        rep_data = []
        if rep_file.exists():
            with open(rep_file, 'r', encoding='utf-8') as f:
                rep_data = json.load(f)
        
        # Reconstruire les objets à partir des dicts JSON
        from app.models.parser_models import ParsedDocument, Course, Partant, MediaSelection, Classement, Commentaire, Resultat, ParsedRepDocument, RepDocument
        
        def dict_to_course(cd: dict) -> Course:
            # Gérer les champs imbriqués (distance, montant)
            distance_raw = cd.get('distance', {}).get('raw', '') if isinstance(cd.get('distance'), dict) else cd.get('distance_raw', '')
            distance_m = cd.get('distance', {}).get('meters') if isinstance(cd.get('distance'), dict) else cd.get('distance_m')
            montant_raw = cd.get('montant', {}).get('raw', '') if isinstance(cd.get('montant'), dict) else cd.get('montant_raw', '')
            montant_euros = cd.get('montant', {}).get('euros') if isinstance(cd.get('montant'), dict) else cd.get('montant_euros')
            
            return Course(
                course_id=cd.get('course_id', ''),
                date=cd.get('date', ''),
                reunion=cd.get('reunion', ''),
                course_num=cd.get('course_num', 0),
                hippodrome=cd.get('hippodrome', ''),
                discipline=cd.get('discipline', ''),
                distance_raw=distance_raw,
                distance_m=distance_m,
                montant_raw=montant_raw,
                montant_euros=montant_euros,
                partants_declares=cd.get('partants_declares', 0),
                partants_effectifs=cd.get('partants_effectifs', 0),
                type_course=cd.get('type_course', ''),
                titre=cd.get('titre', ''),
                heure_depart=cd.get('heure_depart', ''),
                heure_arret_jeux=cd.get('heure_arret_jeux', ''),
                raw_text=cd.get('raw_text', '')
            )
        
        def dict_to_partant(pd: dict) -> Partant:
            # Gérer les champs imbriqués
            def get_nested(d, key, subkey, default=''):
                val = d.get(key, {})
                if isinstance(val, dict):
                    return val.get(subkey, default)
                return d.get(f"{key}_{subkey}", default)
            
            def get_nested_opt(d, key, subkey, default=None):
                val = d.get(key, {})
                if isinstance(val, dict):
                    return val.get(subkey, default)
                return d.get(f"{key}_{subkey}", default)
            
            return Partant(
                course_id=pd.get('course_id', ''),
                numero=pd.get('numero', 0),
                nom_cheval_raw=get_nested(pd, 'nom_cheval', 'raw', pd.get('nom_cheval_raw', '')),
                nom_cheval_normalized=get_nested(pd, 'nom_cheval', 'normalized', pd.get('nom_cheval_normalized', '')),
                sexe=pd.get('sexe', ''),
                age=pd.get('age', ''),
                poids=pd.get('poids', ''),
                corde=pd.get('corde', ''),
                distance_raw=get_nested(pd, 'distance', 'raw', pd.get('distance_raw', '')),
                distance_m=get_nested_opt(pd, 'distance', 'meters', pd.get('distance_m')),
                chrono_raw=get_nested(pd, 'chrono', 'raw', pd.get('chrono_raw', '')),
                chrono_normalized=get_nested(pd, 'chrono', 'normalized', pd.get('chrono_normalized', '')),
                performances_raw=get_nested(pd, 'performances', 'raw', pd.get('performances_raw', '')),
                performances_structured=get_nested(pd, 'performances', 'structured', pd.get('performances_structured', [])),
                gains_raw=get_nested(pd, 'gains', 'raw', pd.get('gains_raw', '')),
                gains_euros=get_nested_opt(pd, 'gains', 'euros', pd.get('gains_euros')),
                driver_raw=get_nested(pd, 'driver', 'raw', pd.get('driver_raw', '')),
                driver_normalized=get_nested(pd, 'driver', 'normalized', pd.get('driver_normalized', '')),
                entraineur_raw=get_nested(pd, 'entraineur', 'raw', pd.get('entraineur_raw', '')),
                entraineur_normalized=get_nested(pd, 'entraineur', 'normalized', pd.get('entraineur_normalized', '')),
                proprietaire_raw=get_nested(pd, 'proprietaire', 'raw', pd.get('proprietaire_raw', '')),
                proprietaire_normalized=get_nested(pd, 'proprietaire', 'normalized', pd.get('proprietaire_normalized', '')),
                cote_raw=get_nested(pd, 'cote', 'raw', pd.get('cote_raw', '')),
                cote_decimale=get_nested_opt(pd, 'cote', 'decimale', pd.get('cote_decimale')),
                commentaire=pd.get('commentaire', ''),
                raw_data=pd.get('raw_data', {})
            )
        
        def dict_to_media(msd: dict) -> MediaSelection:
            return MediaSelection(
                course_id=msd.get('course_id', ''),
                source=msd.get('source', ''),
                selection=msd.get('selection', []),
                rang=msd.get('rang', [])
            )
        
        def dict_to_classement(cld: dict) -> Classement:
            return Classement(
                course_id=cld.get('course_id', ''),
                forme=cld.get('forme', []),
                classe=cld.get('classe', []),
                progres=cld.get('progres', []),
                regularite=cld.get('regularite', [])
            )
        
        def dict_to_commentaire(cmd: dict) -> Commentaire:
            return Commentaire(
                course_id=cmd.get('course_id', ''),
                numero_cheval=cmd.get('numero_cheval', 0),
                texte=cmd.get('texte', '')
            )
        
        def dict_to_resultat(rd: dict) -> Resultat:
            def get_nested(d, key, subkey, default=''):
                val = d.get(key, {})
                if isinstance(val, dict):
                    return val.get(subkey, default)
                return d.get(f"{key}_{subkey}", default)
            
            def get_nested_opt(d, key, subkey, default=None):
                val = d.get(key, {})
                if isinstance(val, dict):
                    return val.get(subkey, default)
                return d.get(f"{key}_{subkey}", default)
            
            return Resultat(
                course_id=rd.get('course_id', ''),
                date=rd.get('date', ''),
                type_pari=rd.get('type_pari', ''),
                arrivee=rd.get('arrivee', []),
                arrivee_complete=rd.get('arrivee_complete', []),
                npo=rd.get('npo', 0),
                np=rd.get('np', 0),
                disqualifies=rd.get('disqualifies', []),
                non_partants=rd.get('non_partants', []),
                gains_ordre_raw=get_nested(rd, 'gains_ordre', 'raw', rd.get('gains_ordre_raw', '')),
                gains_ordre_euros=get_nested_opt(rd, 'gains_ordre', 'euros', rd.get('gains_ordre_euros')),
                gains_desordre_raw=get_nested(rd, 'gains_desordre', 'raw', rd.get('gains_desordre_raw', '')),
                gains_desordre_euros=get_nested_opt(rd, 'gains_desordre', 'euros', rd.get('gains_desordre_euros')),
                gains_bonus_raw=get_nested(rd, 'gains_bonus', 'raw', rd.get('gains_bonus_raw', '')),
                gains_bonus_euros=get_nested_opt(rd, 'gains_bonus', 'euros', rd.get('gains_bonus_euros')),
                nb_gagnants_ordre=rd.get('nb_gagnants', {}).get('ordre', rd.get('nb_gagnants_ordre')),
                nb_gagnants_desordre=rd.get('nb_gagnants', {}).get('desordre', rd.get('nb_gagnants_desordre')),
                nb_gagnants_bonus=rd.get('nb_gagnants', {}).get('bonus', rd.get('nb_gagnants_bonus')),
                masse_partager_raw=get_nested(rd, 'masse_partager', 'raw', rd.get('masse_partager_raw', '')),
                masse_partager_euros=get_nested_opt(rd, 'masse_partager', 'euros', rd.get('masse_partager_euros')),
                rapport_gagnant_raw=get_nested(rd, 'rapports', 'gagnant', {}).get('raw', rd.get('rapport_gagnant_raw', '')),
                rapport_gagnant_euros=get_nested(rd, 'rapports', 'gagnant', {}).get('euros', rd.get('rapport_gagnant_euros')),
                rapport_place_a_raw=get_nested(rd, 'rapports', 'place_a', {}).get('raw', rd.get('rapport_place_a_raw', '')),
                rapport_place_a_euros=get_nested(rd, 'rapports', 'place_a', {}).get('euros', rd.get('rapport_place_a_euros')),
                rapport_place_b_raw=get_nested(rd, 'rapports', 'place_b', {}).get('raw', rd.get('rapport_place_b_raw', '')),
                rapport_place_b_euros=get_nested(rd, 'rapports', 'place_b', {}).get('euros', rd.get('rapport_place_b_euros')),
                map_paris_raw=get_nested(rd, 'map_paris', 'raw', rd.get('map_paris_raw', '')),
                map_paris_euros=get_nested(rd, 'map_paris', 'euros', rd.get('map_paris_euros')),
                raw_text=rd.get('raw_text', '')
            )
        
        parsed_docs = []
        for d in data:
            courses = [dict_to_course(c) for c in d.get('courses', [])]
            partants = [dict_to_partant(p) for p in d.get('partants', [])]
            media = [dict_to_media(m) for m in d.get('media_selections', [])]
            classements = [dict_to_classement(c) for c in d.get('classements', [])]
            commentaires = [dict_to_commentaire(c) for c in d.get('commentaires', [])]
            resultat = dict_to_resultat(d['resultat']) if d.get('resultat') else None
            
            pdoc = ParsedDocument(
                filename=d['filename'],
                doc_type=d['doc_type'],
                date_publication=d['date_publication'],
                pages=d['pages'],
                courses=courses,
                partants=partants,
                media_selections=media,
                classements=classements,
                commentaires=commentaires,
                resultat=resultat
            )
            parsed_docs.append(pdoc)
        
        # Reconstruire les documents REP
        def dict_to_rep(rd: dict) -> RepDocument:
            def get_nested(d, key, subkey, default=''):
                val = d.get(key, {})
                if isinstance(val, dict):
                    return val.get(subkey, default)
                return d.get(f"{key}_{subkey}", default)
            
            def get_nested_opt(d, key, subkey, default=None):
                val = d.get(key, {})
                if isinstance(val, dict):
                    return val.get(subkey, default)
                return d.get(f"{key}_{subkey}", default)
            
            return RepDocument(
                document_type=rd.get('document_type', 'REP'),
                date_document=rd.get('date_document', ''),
                date_document_raw=rd.get('date_document_raw', ''),
                date_course_cible=rd.get('date_course_cible', ''),
                date_course_cible_raw=rd.get('date_course_cible_raw', ''),
                game_type=rd.get('game_type', ''),
                report_ordre_raw=rd.get('report_ordre', {}).get('raw', ''),
                report_ordre=rd.get('report_ordre', {}).get('euros'),
                tierce_v_raw=rd.get('tierce_v', {}).get('raw', ''),
                tierce_v_value=rd.get('tierce_v', {}).get('value'),
                raw_text=rd.get('raw_text', '')
            )
        
        for d in rep_data:
            rep_doc = dict_to_rep(d.get('rep_document', {}))
            pdoc = ParsedRepDocument(
                filename=d['filename'],
                doc_type=d['doc_type'],
                date_publication=d['date_publication'],
                pages=d['pages'],
                rep_document=rep_doc
            )
            parsed_docs.append(pdoc)
    
    QUALITY_DIR.mkdir(parents=True, exist_ok=True)
    validator = QualityValidator()
    
    validated = []
    for parsed in parsed_docs:
        validated_parsed = validator.validate(parsed)
        validated.append(validated_parsed)
    
    # Exporter les issues
    issues_file = QUALITY_DIR / "parsing_errors.csv"
    validator.export_issues_csv(str(issues_file))
    
    # Rapport qualité global
    report_file = QUALITY_DIR / "quality_report.csv"
    validator.generate_quality_report(validated, str(report_file))
    
    # Non-matched (si matcher utilisé)
    unmatched_file = QUALITY_DIR / "unmatched_results.csv"
    # (à implémenter si matcher utilisé)
    
    logger.info("Validation terminée: %s, %s", issues_file, report_file)
    
    # Afficher résumé
    print_validation_summary(validated)
    
    return validated


def print_validation_summary(docs: List):
    """Affiche un résumé de validation lisible."""
    print(f"\n{'='*60}")
    print("  RAPPORT DE VALIDATION ÉCHANTILLON")
    print(f"{'='*60}")
    
    total = len(docs)
    journals = sum(1 for d in docs if d.doc_type == 'JOURNAL')
    results = sum(1 for d in docs if d.doc_type == 'RESULTAT')
    reps = sum(1 for d in docs if d.doc_type == 'REP')
    courses = sum(len(getattr(d, 'courses', [])) for d in docs)
    partants = sum(len(getattr(d, 'partants', [])) for d in docs)
    
    success = sum(1 for d in docs if getattr(d, 'quality_status', '') == 'SUCCESS')
    partial = sum(1 for d in docs if getattr(d, 'quality_status', '') == 'PARTIAL')
    failed = sum(1 for d in docs if getattr(d, 'quality_status', '') == 'FAILED')
    avg_score = sum(getattr(d, 'quality_score', 0) for d in docs) / total if total > 0 else 0
    
    print(f"\n  PDF analysés      : {total}")
    print(f"  Journaux          : {journals}")
    print(f"  Résultats         : {results}")
    print(f"  Rapports (REP)    : {reps}")
    print(f"  Courses détectées : {courses}")
    print(f"  Partants          : {partants}")
    print(f"\n  SUCCESS           : {success}")
    print(f"  PARTIAL           : {partial}")
    print(f"  FAILED            : {failed}")
    print(f"  Qualité moyenne   : {avg_score:.1f}/100")
    
    print(f"\n  Détail par document:")
    for d in docs:
        course_id = "N/A"
        if hasattr(d, 'courses') and d.courses:
            course_id = d.courses[0].course_id
        elif hasattr(d, 'resultat') and d.resultat:
            course_id = d.resultat.course_id
        elif hasattr(d, 'rep_document') and d.rep_document:
            course_id = f"REP_{d.rep_document.date_course_cible}"
        
        print(f"    {d.filename}")
        print(f"      Type: {d.doc_type} | Course: {course_id} | Score: {getattr(d, 'quality_score', 'N/A')} | Status: {getattr(d, 'quality_status', 'N/A')}")
        if hasattr(d, 'parsing_errors') and d.parsing_errors:
            for err in d.parsing_errors[:3]:
                print(f"      - {err}")
            if len(d.parsing_errors) > 3:
                print(f"      ... et {len(d.parsing_errors) - 3} autres")
    
    print(f"\n  Rapports générés:")
    print(f"    {QUALITY_DIR}/parsing_errors.csv")
    print(f"    {QUALITY_DIR}/quality_report.csv")
    print(f"{'='*60}")


def run_scraping(source: str) -> tuple[list[DocumentMetadata], list[DocumentMetadata], list[DocumentMetadata]]:
    """
    Lance le scraping selon la source demandée.

    Returns:
        Tuple (programmes_docs, resultats_docs, ecd_docs).
    """
    programmes_docs: list[DocumentMetadata] = []
    resultats_docs: list[DocumentMetadata] = []
    ecd_docs: list[DocumentMetadata] = []

    if source in ("all", "programmes"):
        scraper = ProgrammesScraper()
        programmes_docs = scraper.scrape_all()

    if source in ("all", "resultats"):
        scraper = ResultatsScraper()
        resultats_docs = scraper.scrape_all()

    if source in ("all", "ecd"):
        scraper = CourseDirectScraper()
        ecd_docs = scraper.scrape_all()

    return programmes_docs, resultats_docs, ecd_docs


def main() -> int:
    """Point d'entrée principal."""
    parser = argparse.ArgumentParser(
        description="PMU'B LONAB Scraper — Collecte et parsing des journaux hippiques, résultats et courses en direct",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  python main.py --dry-run                     Analyse sans téléchargement
  python main.py --download                    Télécharge tout
  python main.py --download --source programmes  Programmes uniquement
  python main.py --download --source resultats   Résultats uniquement
  python main.py --download --source ecd         ECD uniquement
  python main.py --parse-sample                 Parser l'échantillon (JOURNAL + RESULTAT)
  python main.py --validate-sample              Valider l'échantillon parsé (JOURNAL + RESULTAT)
  python main.py --parse-ecd-sample             Parser l'échantillon ECD (Course En Direct)
  python main.py --validate-ecd-sample          Valider l'échantillon ECD parsé
        """,
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--dry-run",
        action="store_true",
        help="Analyser les pages et afficher les documents sans télécharger",
    )
    group.add_argument(
        "--download",
        action="store_true",
        help="Télécharger les documents PDF",
    )
    group.add_argument(
        "--parse-sample",
        action="store_true",
        help="Parser les PDFs JOURNAL et RESULTAT du dossier échantillon",
    )
    group.add_argument(
        "--validate-sample",
        action="store_true",
        help="Valider les PDFs JOURNAL/RESULTAT parsés de l'échantillon",
    )
    group.add_argument(
        "--parse-ecd-sample",
        action="store_true",
        help="Parser les PDFs ECD (Course En Direct) du dossier échantillon",
    )
    group.add_argument(
        "--validate-ecd-sample",
        action="store_true",
        help="Valider les PDFs ECD parsés de l'échantillon",
    )
    group.add_argument(
        "--enrich",
        action="store_true",
        help="Enrichir les données via l'API officielle PMU",
    )
    group.add_argument(
        "--predict",
        action="store_true",
        help="Analyse prédictive Tiercé, Quarté et 4+1 basée sur l'activité des jockeys et l'IA",
    )

    parser.add_argument(
        "--date",
        type=str,
        default=None,
        help="Date à enrichir (ex: 2024-02-11 ou 11022024)",
    )
    parser.add_argument(
        "--cheval",
        type=str,
        default=None,
        help="Nom du cheval dont l'historique doit être enrichi",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Limite du nombre de courses pour l'enrichissement par lot (défaut: 10)",
    )

    parser.add_argument(
        "--source",
        choices=["programmes", "resultats", "ecd", "all"],
        default="all",
        help="Source à traiter (défaut: all)",
    )

    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Niveau de logging (défaut: INFO)",
    )

    args = parser.parse_args()

    # Initialiser le logging
    setup_logging(level=args.log_level)

    logger.info("PMU'B LONAB Scraper V0.1 — Démarrage %s", datetime.now().isoformat())

    if args.parse_sample:
        logger.info("Mode: parse-sample")
        parse_sample()
        return 0

    if args.validate_sample:
        logger.info("Mode: validate-sample")
        validate_sample()
        return 0

    if args.parse_ecd_sample:
        logger.info("Mode: parse-ecd-sample")
        parse_ecd_sample()
        return 0

    if args.validate_ecd_sample:
        logger.info("Mode: validate-ecd-sample")
        validate_ecd_sample()
        return 0

    if args.enrich:
        logger.info("Mode: enrich (Enrichissement API PMU)")
        enricher = PMUDataEnricher(db_path=PROCESSED_DIR / "pmu_lonab.db")
        
        if args.date:
            print(f"\n--- Enrichissement pour la date : {args.date} ---")
            res = enricher.enrich_date(args.date)
            print(f"Statut : {res.get('status')}")
            if res.get("status") == "success":
                print(f"Course : R{res.get('reunion')}C{res.get('course')} - {res.get('course_nom')}")
                print(f"Chevaux enrichis : {res.get('enriched')}")
            else:
                print(f"Message : {res.get('message')}")
        elif args.cheval:
            print(f"\n--- Enrichissement de l'historique pour le cheval : {args.cheval} ---")
            res = enricher.enrich_horse(args.cheval)
            print(f"Statut : {res.get('status')}")
            print(f"Total dates trouvées : {res.get('total_dates', 0)}")
            success_dates = [d for d in res.get("details", []) if d.get("status") == "success"]
            print(f"Dates enrichies avec succès : {len(success_dates)}")
        else:
            print(f"\n--- Enrichissement par lot (limite: {args.limit} dates) ---")
            res = enricher.enrich_batch(limit=args.limit)
            print(f"Dates traitées : {res.get('total_pending_processed')}")
            print(f"Dates enrichies avec succès : {res.get('successful_dates')}")
            print(f"Total chevaux enrichis : {res.get('total_horses_enriched')}")
        return 0

    if args.predict:
        logger.info("Mode: predict (Analyse prédictive Tiercé/Quarté/4+1)")
        predictor = LonabPredictor(db_path=PROCESSED_DIR / "pmu_lonab.db")
        target_date = args.date or "2024-02-11"

        print(f"\n{'='*75}")
        print(f"  ANALYSE PRÉDICTIVE LONAB — TIERCE / QUARTE / 4+1")
        print(f"{'='*75}")
        
        analysis = predictor.predict_race(target_date)
        if analysis.get("status") == "error":
            print(f"Erreur : {analysis.get('message')}")
            return 1

        print(f"Course     : {analysis['titre']}")
        print(f"Date       : {analysis['date']} | Hippodrome : {analysis['hippodrome']} ({analysis['discipline']})")
        print(f"Partants   : {analysis['total_partants']} chevaux analysés\n")

        print(f"{'N°':<4} {'Cheval':<20} {'Driver':<16} {'Montes':<8} {'Profil':<14} {'Cote':<6} {'Déf.':<10} {'Score IA'}")
        print("-" * 88)
        for h in analysis["classement_ia"]:
            def_str = "D4" if "ANTERIEURS_POSTERIEURS" in h["deferre"] or "DES_4" in h["deferre"] else ("DP/DA" if "POSTERIEURS" in h["deferre"] or "ANTERIEURS" in h["deferre"] else "-")
            val_flag = " [VALUE]" if h["is_value_outsider"] else ""
            print(f"{h['numero']:<4} {h['nom'][:19]:<20} {h['driver'][:15]:<16} {h['montes_jour']:<8} {h['emoji_jockey']} {h['profil_jockey']:<12} {h['cote']:<6.1f} {def_str:<10} {h['score_total']:.2f}{val_flag}")

        print("\n" + "=" * 75)
        print("  STRATÉGIES DE PARIS PMU'B (RÈGLEMENTS LONAB)")
        print("=" * 75)
        
        if analysis.get("non_partants"):
            print(f"[NON-PARTANTS DÉTECTÉS] : {analysis['non_partants']} (exclus automatiquement)")

        print(f"\n1. FORMULES CLASSIQUES :")
        print(f"   * [BASES TIERCE]  (3 chevaux) : {analysis['bases_tierce']}")
        print(f"   * [SÉLECTION QUARTÉ] (4 ch.) : {analysis['selection_quarte']}")

        print(f"\n2. STRATÉGIES 4+1 (QUINTÉ+) :")
        print(f"   * [TICKET SÉCURITÉ]   : {analysis['ticket_securite_4plus1']}")
        print(f"     -> Objectif : Viser le Désordre (119 comb.) et la couverture Bonus (120 comb.)")
        print(f"     -> Cote moyenne : {analysis['analyse_trj']['moyenne_cote_securite']} ({analysis['analyse_trj']['ev_securite']})")
        
        print(f"   * [TICKET SPÉCULATIF] : {analysis['ticket_speculatif_4plus1']}")
        print(f"     -> Objectif : Viser l'Ordre ou gros Désordre pour battre les 35% de prélèvement LONAB")
        print(f"     -> Cote moyenne : {analysis['analyse_trj']['moyenne_cote_speculatif']} ({analysis['analyse_trj']['ev_speculatif']})")

        if analysis.get("cheval_complement"):
            print(f"\n3. RÈGLE NON-PARTANT LONAB :")
            print(f"   * [CHEVAL DE COMPLÉMENT] : N° {analysis['cheval_complement']}")
            print(f"     -> À cocher sur votre ticket pour éviter le déclassement en 'Quarté Venant'")

        cr_4plus1 = analysis.get("champ_reduit_4plus1")
        if cr_4plus1:
            print(f"\n4. FORMULE CHAMP RÉDUIT 4+1 (Bases + Associés) :")
            print(f"   * Bases incontournables : {cr_4plus1['bases']}")
            print(f"   * Chevaux Associés      : {cr_4plus1['associes']}")
            print(f"   * Combinaisons          : {cr_4plus1['nb_combinaisons']} tickets")
            print(f"   * Coût estimé           : {cr_4plus1['cout_300fcfa']} FCFA (mise à 300F) | {cr_4plus1['cout_500fcfa']} FCFA (mise à 500F)")

        if analysis.get("value_outsiders"):
            print(f"\n[OUTSIDERS VALUE RECOMMANDÉS] : {analysis['value_outsiders']}")
        if analysis.get("fake_favorites"):
            print(f"[FAUX FAVORIS À RISQUE]       : {analysis['fake_favorites']}")

        if analysis["arrivee_reelle"]:
            arr = analysis['arrivee_reelle']
            print(f"\n" + "=" * 75)
            print(f"  BILAN RÉTROSPECTIF vs ARRIVÉE OFFICIELLE")
            print("=" * 75)
            print(f"[ARRIVÉE RÉELLE DU 4+1] : {arr[:5]}")
            
            # Vérification des gains
            secu = analysis['ticket_securite_4plus1']
            spec = analysis['ticket_speculatif_4plus1']
            
            def check_gains(ticket, nom):
                t_set = set(ticket)
                top5_set = set(arr[:5])
                top4_set = set(arr[:4])
                top3_set = set(arr[:3])
                commun = len(t_set.intersection(top5_set))
                
                if ticket == arr[:5]:
                    return f"{nom} : GAGNÉ ORDRE 4+1 !!!"
                elif commun == 5:
                    return f"{nom} : GAGNÉ DÉSORDRE 4+1 (5/5) !"
                elif commun == 4:
                    return f"{nom} : GAGNÉ BONUS 4+1 (4/5) !"
                elif len(set(ticket[:4]).intersection(top4_set)) == 4:
                    return f"{nom} : Quarté touché en désordre !"
                elif len(set(ticket[:3]).intersection(top3_set)) == 3:
                    return f"{nom} : Tiercé touché en désordre !"
                else:
                    return f"{nom} : {commun}/5 chevaux dans le 4+1"

            print(f"   -> {check_gains(secu, 'Ticket Sécurité')}")
            print(f"   -> {check_gains(spec, 'Ticket Spéculatif')}")
            
            raps = analysis.get("rapports_officiels", {})
            if raps and any(raps.values()):
                print(f"   [Rapports LONAB enregistrés] :")
                if raps.get("ordre"): print(f"      - 4+1 Ordre    : {raps['ordre']:,} FCFA".replace(",", " "))
                if raps.get("desordre"): print(f"      - 4+1 Désordre : {raps['desordre']:,} FCFA".replace(",", " "))
                if raps.get("bonus"): print(f"      - 4+1 Bonus    : {raps['bonus']:,} FCFA".replace(",", " "))

        print("=" * 75)
        return 0

    logger.info("Mode: %s | Source: %s", "dry-run" if args.dry_run else "download", args.source)

    # Charger les métadonnées existantes
    existing = load_existing_metadata()

    # Scraper les pages
    programmes_docs, resultats_docs, ecd_docs = run_scraping(args.source)
    all_new_docs = programmes_docs + resultats_docs + ecd_docs

    if args.dry_run:
        # Marquer les documents déjà connus
        for doc in all_new_docs:
            if doc.pdf_url in existing:
                doc.status = existing[doc.pdf_url].status

        # Afficher les résultats
        if args.source in ("all", "programmes"):
            display_dry_run("PROGRAMMES PMU'B", programmes_docs)

        if args.source in ("all", "resultats"):
            display_dry_run("RÉSULTATS PMU'B", resultats_docs)

        if args.source in ("all", "ecd"):
            display_dry_run("ECD (COURSE EN DIRECT)", ecd_docs)

        # Résumé
        total = len(all_new_docs)
        already_known = sum(1 for d in all_new_docs if d.pdf_url in existing)
        print(f"\n--- Résumé ---")
        print(f"Total documents trouvés : {total}")
        print(f"Déjà connus            : {already_known}")
        print(f"Nouveaux               : {total - already_known}")

    elif args.download:
        # Fusionner avec les existants
        merged = merge_documents(existing, all_new_docs)

        # Identifier les documents à télécharger
        to_download = [
            d for d in merged
            if d.status in (DocumentStatus.DISCOVERED, DocumentStatus.FAILED)
        ]

        logger.info("%d document(s) à télécharger", len(to_download))

        if to_download:
            downloader = PDFDownloader(data_dir=DATA_DIR)
            downloaded = downloader.download_all(to_download)

            # Mettre à jour dans la liste fusionnée
            downloaded_map = {d.pdf_url: d for d in downloaded}
            for i, doc in enumerate(merged):
                if doc.pdf_url in downloaded_map:
                    merged[i] = downloaded_map[doc.pdf_url]

        # Sauvegarder les métadonnées
        save_metadata(merged)

        # Résumé final
        total = len(merged)
        downloaded_count = sum(1 for d in merged if d.status == DocumentStatus.DOWNLOADED)
        skipped_count = sum(1 for d in merged if d.status == DocumentStatus.SKIPPED)
        failed_count = sum(1 for d in merged if d.status == DocumentStatus.FAILED)

        print(f"\n{'='*60}")
        print(f"  RÉSUMÉ FINAL")
        print(f"{'='*60}")
        print(f"  Total documents       : {total}")
        print(f"  Téléchargés           : {downloaded_count}")
        print(f"  Skippés (déjà locaux) : {skipped_count}")
        print(f"  Échoués               : {failed_count}")
        print(f"  Métadonnées           : {METADATA_FILE}")
        print(f"{'='*60}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
