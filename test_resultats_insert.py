import sqlite3
conn = sqlite3.connect(r'C:\Users\Lenovo\Desktop\PMU\pmu-lonab-scraper\data\processed\pmu_lonab.db')
c = conn.cursor()

# Simulate the resultats insert with test data
r = {
    'course_id': '',
    'date': '2024-01-19',
    'type_pari': 'TIERCE',
    'arrivee': [1, 2, 3],
    'arrivee_complete': [1, 2, 3, 4, 5],
    'npo': 0,
    'np': 0,
    'disqualifies': [],
    'non_partants': [],
    'gains_ordre_raw': '1000',
    'gains_ordre_euros': 1000,
    'gains_desordre_raw': '500',
    'gains_desordre_euros': 500,
    'gains_bonus_raw': '200',
    'gains_bonus_euros': 200,
    'nb_gagnants_ordre': 10,
    'nb_gagnants_desordre': 20,
    'nb_gagnants_bonus': 30,
    'masse_partager_raw': '10000',
    'masse_partager_euros': 10000,
    'rapports': {
        'gagnant': {'raw': '10.0', 'euros': 10.0},
        'place_a': {'raw': '3.0', 'euros': 3.0},
        'place_b': {'raw': '2.0', 'euros': 2.0}
    },
    'rapport_gagnant_raw': '10.0',
    'rapport_place_a_raw': '3.0',
    'rapport_place_b_raw': '2.0',
    'map_paris_raw': '5000',
    'map_paris_euros': 5000,
    'raw_text': 'test'
}

import json
def get_nested(obj, key, subkey, default=''):
    val = obj.get(key, {})
    if isinstance(val, dict):
        return val.get(subkey, default)
    return obj.get(f"{key}_{subkey}", default)

def get_nested_opt(obj, key, subkey, default=None):
    val = obj.get(key, {})
    if isinstance(val, dict):
        return val.get(subkey, default)
    return obj.get(f"{key}_{subkey}", default)

values = (
    1, r.get('course_id', ''), r.get('date'), r.get('type_pari'),
    json.dumps(r.get('arrivee', []), ensure_ascii=False),
    json.dumps(r.get('arrivee_complete', []), ensure_ascii=False),
    r.get('npo'), r.get('np'),
    json.dumps(r.get('disqualifies', []), ensure_ascii=False),
    json.dumps(r.get('non_partants', []), ensure_ascii=False),
    get_nested(r, 'gains_ordre', 'raw', r.get('gains_ordre_raw', '')),
    get_nested_opt(r, 'gains_ordre', 'euros', r.get('gains_ordre_euros')),
    get_nested(r, 'gains_desordre', 'raw', r.get('gains_desordre_raw', '')),
    get_nested_opt(r, 'gains_desordre', 'euros', r.get('gains_desordre_euros')),
    get_nested(r, 'gains_bonus', 'raw', r.get('gains_bonus_raw', '')),
    get_nested_opt(r, 'gains_bonus', 'euros', r.get('gains_bonus_euros')),
    r.get('nb_gagnants_ordre'), r.get('nb_gagnants_desordre'), r.get('nb_gagnants_bonus'),
    get_nested(r, 'masse_partager', 'raw', r.get('masse_partager_raw', '')),
    get_nested_opt(r, 'masse_partager', 'euros', r.get('masse_partager_euros')),
    get_nested(r, 'rapports', 'gagnant', {}).get('raw', r.get('rapport_gagnant_raw', '')) if isinstance(r.get('rapports'), dict) else r.get('rapport_gagnant_raw', ''),
    get_nested(r, 'rapports', 'gagnant', {}).get('euros', r.get('gains_ordre_euros')) if isinstance(r.get('rapports'), dict) else r.get('gains_ordre_euros'),
    get_nested(r, 'rapports', 'place_a', {}).get('raw', r.get('rapport_place_a_raw', '')) if isinstance(r.get('rapports'), dict) else r.get('rapport_place_a_raw', ''),
    get_nested(r, 'rapports', 'place_a', {}).get('euros', r.get('gains_ordre_euros')) if isinstance(r.get('rapports'), dict) else r.get('gains_ordre_euros'),
    get_nested(r, 'rapports', 'place_b', {}).get('raw', r.get('rapport_place_b_raw', '')) if isinstance(r.get('rapports'), dict) else r.get('rapport_place_b_raw', ''),
    get_nested(r, 'rapports', 'place_b', {}).get('euros', r.get('gains_ordre_euros')) if isinstance(r.get('rapports'), dict) else r.get('gains_ordre_euros'),
    get_nested(r, 'map_paris', 'raw', r.get('map_paris_raw', '')),
    get_nested_opt(r, 'map_paris', 'euros', r.get('map_paris_euros')),
    r.get('raw_text', '')[:10000] if r.get('raw_text') else None
)

print(f'Values count: {len(values)}')
for i, v in enumerate(values):
    print(f'  {i+1}: {repr(v)[:80]}')

# Test insert
try:
    c.execute('''
        INSERT INTO resultats (document_id, course_id, date, type_pari, arrivee, arrivee_complete,
                             npo, np, disqualifies, non_partants,
                             gains_ordre_raw, gains_ordre_euros, gains_desordre_raw,
                             gains_desordre_euros, gains_bonus_raw, gains_bonus_euros,
                             nb_gagnants_ordre, nb_gagnants_desordre, nb_gagnants_bonus,
                             masse_partager_raw, masse_partager_euros,
                             rapport_gagnant_raw, rapport_gagnant_euros,
                             rapport_place_a_raw, rapport_place_a_euros,
                             rapport_place_b_raw, rapport_place_b_euros,
                             map_paris_raw, map_paris_euros, raw_text)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', values)
    print('OK - insert works')
    conn.rollback()
except Exception as e:
    print(f'Error: {e}')