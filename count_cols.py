sql = '''INSERT INTO partants (document_id, course_id, numero, nom_cheval_raw, nom_cheval_normalized,
                                        sexe, age, poids, corde, distance_raw, distance_m,
                                        chrono_raw, chrono_normalized, performances_raw,
                                        performances_structured, gains_raw, gains_euros,
                                        driver_raw, driver_normalized, entraineur_raw,
                                        entraineur_normalized, proprietaire_raw,
                                        proprietaire_normalized, cote_raw, cote_decimale,
                                        commentaire, raw_data) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'''
print(f'Placeholders: {sql.count("?")}')

# Count columns
cols_part = sql.split("VALUES")[0]
cols = [c.strip() for c in cols_part.split("(")[1].split(")")[0].split(",")]
print(f'Columns: {len(cols)}')
for i, c in enumerate(cols):
    print(f'  {i+1}: {c}')