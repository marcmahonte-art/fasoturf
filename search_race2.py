import sqlite3

conn = sqlite3.connect(r'C:\Users\Lenovo\Desktop\PMU\pmu-lonab-scraper\data\processed\pmu_lonab.db')
cursor = conn.cursor()

# List tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("=== Tables dans pmu_lonab.db ===")
for t in tables:
    print(f"  {t[0]}")

# Search for the race
cursor.execute("""
    SELECT course_id, date_course, hippodrome, discipline, distance_m, montant, libelle 
    FROM courses 
    WHERE LOWER(libelle) LIKE '%boulangerie%' OR LOWER(libelle) LIKE '%fages%'
""")
rows = cursor.fetchall()
print("\n=== Courses trouvées ===")
for row in rows:
    print(f"course_id: {row[0]}")
    print(f"date: {row[1]}")
    print(f"hippodrome: {row[2]}")
    print(f"discipline: {row[3]}")
    print(f"distance: {row[4]}m")
    print(f"montant: {row[5]}")
    print(f"libelle: {row[6]}")
    print("---")

    # Get partants
    course_id = row[0]
    print(f"=== Partants pour {course_id} ===")
    cursor.execute("""
        SELECT numero, nom_cheval, sexe, age, gains_euros, cote_decimale, 
               driver_normalized, entraineur_normalized, performances_structured
        FROM partants 
        WHERE course_id = ?
        ORDER BY numero
    """, (course_id,))
    partants = cursor.fetchall()
    for p in partants:
        print(f"  {p[0]}: {p[1]} | {p[2]}/{p[3]}ans | gains:{p[4]}€ | cote:{p[5]} | drv:{p[6]} | ent:{p[7]} | perfs:{p[8]}")

    # Get results
    print(f"=== Résultats pour {course_id} ===")
    cursor.execute("""
        SELECT arrivee, rapport_tierce, rapport_quarte, rapport_quinte
        FROM resultats 
        WHERE course_id = ?
    """, (course_id,))
    resultats = cursor.fetchall()
    for r in resultats:
        print(f"  Arrivée: {r[0]} | Tiercé: {r[1]} | Quarté: {r[2]} | Quinté: {r[3]}")

conn.close()