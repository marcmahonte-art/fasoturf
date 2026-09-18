import json
from app.parser.matcher import JournalResultMatcher
from app.models.parser_models import ParsedDocument, Course, Partant, MediaSelection, Classement, Commentaire, Resultat

# Load parsed documents
with open(r'C:\Users\Lenovo\Desktop\PMU\pmu-lonab-scraper\data\processed\all_parsed.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Reconstruct objects
def dict_to_course(cd):
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

def dict_to_partant(pd):
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

def dict_to_media(msd):
    return MediaSelection(course_id=msd.get('course_id', ''), source=msd.get('source', ''), selection=msd.get('selection', []), rang=msd.get('rang', []))

def dict_to_classement(cld):
    return Classement(course_id=cld.get('course_id', ''), forme=cld.get('forme', []), classe=cld.get('classe', []), progres=cld.get('progres', []), regularite=cld.get('regularite', []))

def dict_to_commentaire(cmd):
    return Commentaire(course_id=cmd.get('course_id', ''), numero_cheval=cmd.get('numero_cheval', 0), texte=cmd.get('texte', ''))

def dict_to_resultat(rd):
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

# Run matcher
matcher = JournalResultMatcher()
matches = matcher.match(
    [d for d in parsed_docs if d.doc_type == 'JOURNAL'],
    [d for d in parsed_docs if d.doc_type == 'RESULTAT']
)

print(f"Matches trouves: {len(matches)}")
for m in matches:
    print(f"\nMatch: {m.journal_doc.filename} <-> {m.resultat_doc.filename}")
    print(f"  Confidence: {m.confidence:.2f}")
    print(f"  Reasons: {m.reasons}")
    print(f"  Journal course: {m.course.course_id if m.course else 'N/A'}")
    print(f"  Resultat course: {m.resultat.course_id if m.resultat else 'N/A'}")
    print(f"  Arrivee: {m.resultat.arrivee if m.resultat else 'N/A'}")

# Unmatched
report = matcher.get_unmatched_report()
print(f"\nNon-matchés journaux: {len(report['unmatched_journals'])}")
for u in report['unmatched_journals']:
    print(f"  {u['filename']} - {u['date']} - {u['hippodrome']}")
print(f"Non-matchés résultats: {len(report['unmatched_results'])}")
for u in report['unmatched_results']:
    print(f"  {u['filename']} - {u['date']} - {u['type_pari']}")