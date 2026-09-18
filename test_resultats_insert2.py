import sqlite3
conn = sqlite3.connect(r'C:\Users\Lenovo\Desktop\PMU\pmu-lonab-scraper\data\processed\pmu_lonab.db')
c = conn.cursor()

# Minimal test with just 3 columns
try:
    c.execute('INSERT INTO resultats (document_id, course_id, date) VALUES (1, "test", "2024-01-01")')
    print('OK - 3 cols')
    conn.rollback()
except Exception as e:
    print(f'Error 3 cols: {e}')

# Test with 30 columns using named parameters
cols = ['document_id', 'course_id', 'date', 'type_pari', 'arrivee', 'arrivee_complete',
        'npo', 'np', 'disqualifies', 'non_partants',
        'gains_ordre_raw', 'gains_ordre_euros', 'gains_desordre_raw',
        'gains_desordre_euros', 'gains_bonus_raw', 'gains_bonus_euros',
        'nb_gagnants_ordre', 'nb_gagnants_desordre', 'nb_gagnants_bonus',
        'masse_partager_raw', 'masse_partager_euros',
        'rapport_gagnant_raw', 'rapport_gagnant_euros',
        'rapport_place_a_raw', 'rapport_place_a_euros',
        'rapport_place_b_raw', 'rapport_place_b_euros',
        'map_paris_raw', 'map_paris_euros', 'raw_text']

placeholders = ', '.join(['?'] * len(cols))
col_str = ', '.join(cols)
sql = f'INSERT INTO resultats ({col_str}) VALUES ({placeholders})'
print(f'SQL: {sql[:100]}...')
print(f'Columns: {len(cols)}, Placeholders: {placeholders.count("?")}')

values = tuple([None] * len(cols))
try:
    c.execute(sql, values)
    print('OK - dynamic insert works')
    conn.rollback()
except Exception as e:
    print(f'Error dynamic: {e}')