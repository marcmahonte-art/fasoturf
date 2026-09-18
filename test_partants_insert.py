import sqlite3
conn = sqlite3.connect(r'C:\Users\Lenovo\Desktop\PMU\pmu-lonab-scraper\data\processed\pmu_lonab.db')
c = conn.cursor()

# Test minimal insert
try:
    c.execute('''
        INSERT INTO partants (document_id, course_id, numero, nom_cheval_raw, nom_cheval_normalized,
                            sexe, age, poids, corde, distance_raw, distance_m,
                            chrono_raw, chrono_normalized, performances_raw,
                            performances_structured, gains_raw, gains_euros,
                            driver_raw, driver_normalized, entraineur_raw,
                            entraineur_normalized, proprietaire_raw,
                            proprietaire_normalized, cote_raw, cote_decimale,
                            commentaire, raw_data)
        VALUES (1, "test", 1, "test", "test", "H", "5", "50", "1", "1000", 1000,
                "1:10", "1:10", "1,2,3", "[]", "1000", 1000,
                "driver", "driver", "trainer", "trainer", "owner", "owner",
                "10.0", 10.0, "comment", "{}")
    ''')
    print('OK - minimal insert works')
    conn.rollback()
except Exception as e:
    print(f'Error: {e}')

# Test with the exact columns from the script
try:
    c.execute('''
        INSERT INTO partants (document_id, course_id, numero, nom_cheval_raw, nom_cheval_normalized,
                            sexe, age, poids, corde, distance_raw, distance_m,
                            chrono_raw, chrono_normalized, performances_raw,
                            performances_structured, gains_raw, gains_euros,
                            driver_raw, driver_normalized, entraineur_raw,
                            entraineur_normalized, proprietaire_raw,
                            proprietaire_normalized, cote_raw, cote_decimale,
                            commentaire, raw_data)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        1, "test", 1, "test", "test", "H", "5", "50", "1", "1000", 1000,
        "1:10", "1:10", "1,2,3", "[]", "1000", 1000,
        "driver", "driver", "trainer", "trainer", "owner", "owner",
        "10.0", 10.0, "comment", "{}"
    ))
    print('OK - parameterized insert works')
    conn.rollback()
except Exception as e:
    print(f'Error parameterized: {e}')