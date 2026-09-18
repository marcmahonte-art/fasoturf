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

print(f'SQL length: {len(sql)}')
print(f'Placeholders: {sql.count("?")}')

# Count columns
import re
cols_match = re.search(r'INSERT INTO partants\s*\((.*?)\)', sql, re.DOTALL)
if cols_match:
    cols_str = cols_match.group(1)
    cols = [c.strip() for c in cols_str.split(',')]
    print(f'Columns: {len(cols)}')
    for i, c in enumerate(cols):
        print(f'  {i+1}: {c}')

# Count values in tuple
vals = (
    1, "test", 1, "test", "test", "H", "5", "50", "1", "1000", 1000,
    "1:10", "1:10", "1,2,3", "[]", "1000", 1000,
    "driver", "driver", "trainer", "trainer", "owner", "owner",
    "10.0", 10.0, "comment", "{}"
)
print(f'Values in tuple: {len(vals)}')