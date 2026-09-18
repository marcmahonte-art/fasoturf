#!/usr/bin/env python3
"""
Parse TOUS les PDFs dans pmu-lonab-scraper/data/raw
avec classification, parsing, normalisation et rapport qualité.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'pmu-lonab-scraper'))

import json
import fitz
import traceback
from pathlib import Path
from datetime import datetime
from collections import defaultdict

from app.parser.document_classifier import DocumentClassifier
from app.parser.journal_parser import JournalParser
from app.parser.resultat_parser import ResultatParser
from app.parser.course_direct_parser import ECDParser
from app.parser.rep_parser import RepParser
from app.quality.validator import QualityValidator

# Chemins
RAW_DIR = Path(r"C:\Users\Lenovo\Desktop\PMU\pmu-lonab-scraper\data\raw")
PROCESSED_DIR = Path(r"C:\Users\Lenovo\Desktop\PMU\pmu-lonab-scraper\data\processed")
QUALITY_DIR = Path(r"C:\Users\Lenovo\Desktop\PMU\pmu-lonab-scraper\data\quality")

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
QUALITY_DIR.mkdir(parents=True, exist_ok=True)

classifier = DocumentClassifier()
journal_parser = JournalParser()
resultat_parser = ResultatParser()
ecd_parser = ECDParser()
rep_parser = RepParser()
validator = QualityValidator()

def extract_text(pdf_path: Path) -> str:
    """Extrait le texte complet d'un PDF."""
    doc = fitz.open(str(pdf_path))
    full_text = ""
    for page in doc:
        full_text += page.get_text() + "\n"
    doc.close()
    return full_text

def parse_all_raw():
    """Parse tous les PDFs du dossier raw."""
    pdf_files = list(RAW_DIR.rglob("*.pdf"))
    print(f"Trouvé {len(pdf_files)} fichiers PDF à parser")
    
    # Statistiques
    stats = defaultdict(int)
    errors = []
    all_parsed = []
    all_rep_parsed = []
    all_ecd_parsed = []
    
    # Fichiers déjà parsés (pour éviter de reparser)
    existing_parsed = set()
    for f in PROCESSED_DIR.glob("*.json"):
        if f.name not in ("all_parsed.json", "rep_parsed.json", "ecd_parsed.json", "all_parsed_merged.json"):
            existing_parsed.add(f.stem + ".pdf")
    
    print(f"Fichiers déjà parsés individuellement: {len(existing_parsed)}")
    
    for i, pdf_path in enumerate(sorted(pdf_files), 1):
        filename = pdf_path.name
        rel_path = pdf_path.relative_to(RAW_DIR)
        
        # Skip si déjà parsé (fichier JSON individuel existe)
        if filename in existing_parsed:
            stats["skipped"] += 1
            if i % 100 == 0:
                print(f"  [{i}/{len(pdf_files)}] Skip {filename} (déjà parsé)")
            continue
        
        if i % 50 == 0:
            print(f"  [{i}/{len(pdf_files)}] {rel_path}...")
        
        try:
            # Extraire texte pour classification
            text = extract_text(pdf_path)
            
            # Classifier
            classification = classifier.classify(filename, text)
            parser_type = classifier.get_parser_type(classification)
            
            # Parser selon le type
            if parser_type == 'journal':
                parsed = journal_parser.parse(str(pdf_path))
                all_parsed.append(parsed)
                stats["journal"] += 1
            elif parser_type == 'resultat':
                parsed = resultat_parser.parse(str(pdf_path))
                all_parsed.append(parsed)
                stats["resultat"] += 1
            elif parser_type == 'ecd':
                parsed = ecd_parser.parse(str(pdf_path))
                parsed.save_json(str(PROCESSED_DIR))
                all_ecd_parsed.append(parsed)
                stats["ecd"] += 1
                continue  # ECD sauvé séparément
            elif parser_type == 'rep':
                parsed = rep_parser.parse(str(pdf_path))
                all_rep_parsed.append(parsed)
                stats["rep"] += 1
            else:
                # Inconnu - essayer comme résultat
                stats["unknown"] += 1
                try:
                    parsed = resultat_parser.parse(str(pdf_path))
                    all_parsed.append(parsed)
                    stats["resultat"] += 1
                except:
                    stats["failed"] += 1
                    errors.append({"file": str(rel_path), "error": "Type inconnu, échec parsing"})
                    continue
            
            # Sauvegarder individuellement
            parsed.save_json(str(PROCESSED_DIR))
            
        except Exception as e:
            stats["failed"] += 1
            error_msg = f"{type(e).__name__}: {e}"
            errors.append({"file": str(rel_path), "error": error_msg})
            print(f"    ERREUR {filename}: {error_msg}")
    
    # Sauvegarder combinés
    print("\nSauvegarde des fichiers combinés...")
    
    # JOURNAL + RESULTAT combiné
    combined_file = PROCESSED_DIR / "all_parsed.json"
    with open(combined_file, 'w', encoding='utf-8') as f:
        json.dump([p.to_dict() for p in all_parsed], f, ensure_ascii=False, indent=2)
    print(f"  {combined_file}: {len(all_parsed)} documents")
    
    # REP combiné
    if all_rep_parsed:
        rep_file = PROCESSED_DIR / "rep_parsed.json"
        with open(rep_file, 'w', encoding='utf-8') as f:
            json.dump([p.to_dict() for p in all_rep_parsed], f, ensure_ascii=False, indent=2)
        print(f"  {rep_file}: {len(all_rep_parsed)} documents")
    
    # ECD combiné
    if all_ecd_parsed:
        ecd_file = PROCESSED_DIR / "ecd_parsed.json"
        with open(ecd_file, 'w', encoding='utf-8') as f:
            json.dump([p.to_dict() for p in all_ecd_parsed], f, ensure_ascii=False, indent=2)
        print(f"  {ecd_file}: {len(all_ecd_parsed)} documents")
    
    # Rapport d'erreurs
    if errors:
        err_file = QUALITY_DIR / "parse_errors.json"
        with open(err_file, 'w', encoding='utf-8') as f:
            json.dump(errors, f, ensure_ascii=False, indent=2)
        print(f"  {err_file}: {len(errors)} erreurs")
    
    # Statistiques finales
    print(f"\n{'='*60}")
    print("  RÉSUMÉ PARSING")
    print(f"{'='*60}")
    print(f"  Total fichiers     : {len(pdf_files)}")
    print(f"  Journaux parsés    : {stats['journal']}")
    print(f"  Résultats parsés   : {stats['resultat']}")
    print(f"  ECD parsés         : {stats['ecd']}")
    print(f"  REP parsés         : {stats['rep']}")
    print(f"  Inconnus/échecs    : {stats['failed']}")
    print(f"  Skippés (existants): {stats['skipped']}")
    print(f"  Nouveaux parsés    : {sum(stats[k] for k in ['journal', 'resultat', 'ecd', 'rep'])}")
    print(f"{'='*60}")
    
    return all_parsed, all_rep_parsed, all_ecd_parsed, errors

def validate_all(parsed_docs, rep_docs, ecd_docs):
    """Valide tous les documents parsés."""
    print("\nValidation qualité en cours...")
    
    # Combiner pour validation
    all_for_validation = parsed_docs + rep_docs
    
    validated = []
    for parsed in all_for_validation:
        try:
            validated_parsed = validator.validate(parsed)
            validated.append(validated_parsed)
        except Exception as e:
            print(f"  Erreur validation {parsed.filename}: {e}")
            validated.append(parsed)
    
    # Exporter issues
    issues_file = QUALITY_DIR / "parsing_errors.csv"
    validator.export_issues_csv(str(issues_file))
    
    # Rapport qualité
    report_file = QUALITY_DIR / "quality_report.csv"
    validator.generate_quality_report(validated, str(report_file))
    
    # Résumé
    total = len(validated)
    success = sum(1 for d in validated if getattr(d, 'quality_status', '') == 'SUCCESS')
    partial = sum(1 for d in validated if getattr(d, 'quality_status', '') == 'PARTIAL')
    failed = sum(1 for d in validated if getattr(d, 'quality_status', '') == 'FAILED')
    avg_score = sum(getattr(d, 'quality_score', 0) for d in validated) / total if total > 0 else 0
    
    print(f"\n{'='*60}")
    print("  RAPPORT QUALITÉ GLOBAL")
    print(f"{'='*60}")
    print(f"  Documents validés  : {total}")
    print(f"  SUCCESS            : {success}")
    print(f"  PARTIAL            : {partial}")
    print(f"  FAILED             : {failed}")
    print(f"  Qualité moyenne    : {avg_score:.1f}/100")
    print(f"  Rapports           : {issues_file}, {report_file}")
    print(f"{'='*60}")
    
    # Validation ECD séparée
    if ecd_docs:
        print("\nValidation ECD...")
        from app.models.parser_models import ParsedECDDocument, ECDDocument, CourseDirect, CourseDirectArrival, CourseDirectBet
        
        QUALITY_DIR.mkdir(parents=True, exist_ok=True)
        validated_ecd = []
        
        for parsed in ecd_docs:
            issues = []
            
            if not parsed.ecd_document or not parsed.ecd_document.date:
                issues.append(("date", "ERROR", "Date manquante"))
            if not parsed.ecd_document or not parsed.ecd_document.reunion:
                issues.append(("reunion", "WARNING", "Réunion manquante"))
            if not parsed.ecd_document or not parsed.ecd_document.hippodrome:
                issues.append(("hippodrome", "WARNING", "Hippodrome manquant"))
            if len(parsed.courses) == 0:
                issues.append(("courses", "ERROR", "Aucune course détectée"))
            
            for course in parsed.courses:
                if course.numero_course <= 0:
                    issues.append((f"course_{course.numero_course}_num", "ERROR", "Numéro de course invalide"))
                if not course.arrivee or not course.arrivee.positions:
                    issues.append((f"course_{course.numero_course}_arrivee", "WARNING", "Arrivée manquante"))
            
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
            
            validated_ecd.append(parsed)
        
        # Exporter ECD
        import csv
        ecd_issues_file = QUALITY_DIR / "ecd_errors.csv"
        with open(ecd_issues_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['filename', 'course_id', 'field', 'severity', 'message'])
            for p in validated_ecd:
                for issue in p.parsing_errors:
                    parts = issue.split(': ', 2)
                    if len(parts) >= 3:
                        writer.writerow([p.filename, '', parts[0], parts[1], parts[2]])
        
        ecd_report_file = QUALITY_DIR / "ecd_quality_report.csv"
        with open(ecd_report_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'filename', 'doc_type', 'date', 'reunion', 'hippodrome',
                'quality_score', 'quality_status',
                'courses_total', 'courses_parsed', 'arrivals_parsed', 'bets_parsed',
                'errors', 'warnings'
            ])
            for p in validated_ecd:
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
        
        print(f"  ECD validés: {len(validated_ecd)}")
        print(f"  Rapports ECD: {ecd_issues_file}, {ecd_report_file}")
    
    return validated

def print_detailed_issues(errors):
    """Affiche les problèmes détaillés."""
    if not errors:
        print("\n✅ Aucune erreur de parsing")
        return
    
    print(f"\n{'='*60}")
    print(f"  PROBLÈMES DÉTECTÉS ({len(errors)})")
    print(f"{'='*60}")
    
    by_type = defaultdict(list)
    for e in errors:
        err_type = e['error'].split(':')[0] if ':' in e['error'] else 'OTHER'
        by_type[err_type].append(e)
    
    for err_type, items in sorted(by_type.items(), key=lambda x: -len(x[1])):
        print(f"\n  {err_type} ({len(items)}):")
        for e in items[:5]:
            print(f"    - {e['file']}: {e['error'][:100]}")
        if len(items) > 5:
            print(f"    ... et {len(items) - 5} autres")

def generate_summary_report(parsed_docs, rep_docs, ecd_docs, errors):
    """Génère un rapport de synthèse."""
    report_file = QUALITY_DIR / "parsing_summary.txt"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("RAPPORT DE PARSING COMPLET - PMU LONAB\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Date: {datetime.now().isoformat()}\n")
        f.write(f"Dossier source: {RAW_DIR}\n")
        f.write(f"Dossier destination: {PROCESSED_DIR}\n\n")
        
        # Stats par type
        f.write("STATISTIQUES PAR TYPE:\n")
        f.write(f"  Journaux (JH):     {len([d for d in parsed_docs if d.doc_type == 'JOURNAL'])}\n")
        f.write(f"  Résultats:         {len([d for d in parsed_docs if d.doc_type == 'RESULTAT'])}\n")
        f.write(f"  ECD (Course Direct): {len(ecd_docs)}\n")
        f.write(f"  REP (Rapports):    {len(rep_docs)}\n")
        f.write(f"  Erreurs:           {len(errors)}\n\n")
        
        # Détail par document
        f.write("DÉTAIL PAR DOCUMENT:\n")
        all_docs = parsed_docs + rep_docs + ecd_docs
        
        for d in sorted(all_docs, key=lambda x: x.filename):
            f.write(f"\n  {d.filename}\n")
            f.write(f"    Type: {d.doc_type}\n")
            f.write(f"    Date: {d.date_publication}\n")
            f.write(f"    Pages: {d.pages}\n")
            
            if hasattr(d, 'courses') and d.courses:
                f.write(f"    Courses: {len(d.courses)}\n")
                for c in d.courses:
                    if hasattr(c, 'hippodrome'):
                        f.write(f"      - {c.course_id}: {c.hippodrome} {c.discipline} {c.distance_raw} {c.montant_raw}\n")
                    else:
                        # CourseDirect
                        f.write(f"      - {c.course_id}: Course {c.numero_course} - Arrivée: {c.arrivee.positions if c.arrivee else 'N/A'}\n")
            
            if hasattr(d, 'partants'):
                f.write(f"    Partants: {len(d.partants)}\n")
            
            if hasattr(d, 'resultat') and d.resultat:
                f.write(f"    Résultat: {d.resultat.type_pari} - Arrivée: {d.resultat.arrivee}\n")
            
            if hasattr(d, 'ecd_document') and d.ecd_document:
                ecd = d.ecd_document
                f.write(f"    ECD: Réunion {ecd.reunion} - Hippodrome: {ecd.hippodrome}\n")
                f.write(f"    Courses ECD: {len(d.courses)}\n")
            
            if hasattr(d, 'quality_score'):
                f.write(f"    Qualité: {d.quality_score}/100 ({d.quality_status})\n")
        
        # Erreurs
        if errors:
            f.write(f"\n\nERREURS ({len(errors)}):\n")
            for e in errors:
                f.write(f"  {e['file']}: {e['error']}\n")
    
    print(f"\nRapport de synthèse: {report_file}")

if __name__ == "__main__":
    print("=" * 60)
    print("  PARSING COMPLET - PMU LONAB RAW DATA")
    print("=" * 60)
    
    # Parser
    parsed, rep_parsed, ecd_parsed, errors = parse_all_raw()
    
    # Afficher problèmes
    print_detailed_issues(errors)
    
    # Valider
    validate_all(parsed, rep_parsed, ecd_parsed)
    
    # Rapport synthèse
    generate_summary_report(parsed, rep_parsed, ecd_parsed, errors)
    
    print("\n✅ TERMINÉ")