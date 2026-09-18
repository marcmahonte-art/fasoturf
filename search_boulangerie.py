import sqlite3

conn = sqlite3.connect(r'C:\Users\Lenovo\Desktop\PMU\pmu-lonab-scraper\data\processed\pmu_lonab.db')
cursor = conn.cursor()

# Search in documents filename
cursor.execute("SELECT id, filename, doc_type, date_publication FROM documents WHERE LOWER(filename) LIKE '%boulangerie%' OR LOWER(filename) LIKE '%fages%'")
found = cursor.fetchall()
print("=== Dans documents.filename ===")
for f in found:
    print(f"  ID:{f[0]} | Type:{f[2]} | Date:{f[3]} | {f[1]}")

# Search in courses.titre
cursor.execute("SELECT course_id, date, hippodrome, titre FROM courses WHERE LOWER(titre) LIKE '%boulangerie%' OR LOWER(titre) LIKE '%fages%'")
found = cursor.fetchall()
print("\n=== Dans courses.titre ===")
for f in found:
    print(f"  course_id:{f[0]} | Date:{f[1]} | Hippo:{f[2]} | {f[3]}")

# Search in partants commentaire
cursor.execute("SELECT course_id, numero, nom_cheval_normalized, commentaire FROM partants WHERE LOWER(commentaire) LIKE '%boulangerie%' OR LOWER(commentaire) LIKE '%fages%'")
found = cursor.fetchall()
print("\n=== Dans partants.commentaire ===")
for f in found:
    print(f"  course_id:{f[0]} | #{f[1]} | {f[2]} | {f[3][:100]}")

conn.close()