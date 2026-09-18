import sqlite3
conn = sqlite3.connect(r'C:\Users\Lenovo\Desktop\PMU\pmu-lonab-scraper\data\processed\pmu_lonab.db')
c = conn.cursor()
# Test insert with minimal columns
try:
    c.execute('INSERT INTO partants (document_id, course_id, numero) VALUES (1, "test", 1)')
    print('OK')
    conn.rollback()
except Exception as e:
    print(f'Error: {e}')

# Count columns in INSERT
sql = '''INSERT INTO partants (document_id, course_id, numero, nom_cheval_raw, nom_cheval_normalized,
                                        sexe, age, poids, corde, distance_raw, distance_m,
                                        chrono_raw, chrono_normalized, performances_raw,
                                        performances_structured, gains_raw, gains_euros,
                                        driver_raw, driver_normalized, entraineur_raw,
                                        entraineur_normalized, proprietaire_raw,
                                        proprietaire_normalized, cote_raw, cote_decimale,
                                        commentaire, raw_data) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'''
placeholders = sql.count('?')
print(f'Placeholders: {placeholders}')