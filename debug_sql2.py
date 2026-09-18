sql = '''
        INSERT INTO partants (document_id, course_id, numero, nom_cheval_raw, nom_cheval_normalized,
                            sexe, age, poids, corde, distance_raw, distance_m,
                            chrono_raw, chrono_normalized, performances_raw,
                            performances_structured, gains_raw, gains_euros,
                            driver_raw, driver_normalized, entraineur_raw,
                            entraineur_normalized, proprietaire_raw,
                            proprietaire_normalized, cote_raw, cote_decimale,
                            commentaire, raw_data)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
'''

# Find all ? positions
for i, ch in enumerate(sql):
    if ch == '?':
        print(f'Position {i}: ...{sql[max(0,i-10):i+10]}...')

print(f'\nTotal ?: {sql.count("?")}')