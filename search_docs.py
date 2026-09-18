import sqlite3

conn = sqlite3.connect(r'C:\Users\Lenovo\Desktop\PMU\pmu-lonab-scraper\data\processed\pmu_lonab.db')
cursor = conn.cursor()

# Check documents table for race names
cursor.execute("SELECT document_id, document_type, title, date_document FROM documents WHERE title IS NOT NULL ORDER BY date_document DESC LIMIT 50")
docs = cursor.fetchall()
print("=== Documents récents ===")
for d in docs:
    print(f"  ID:{d[0]} | Type:{d[1]} | Date:{d[3]} | {d[2]}")

# Also search for boulangerie/fages in documents
cursor.execute("SELECT document_id, document_type, title, date_document FROM documents WHERE LOWER(title) LIKE '%boulangerie%' OR LOWER(title) LIKE '%fages%'")
found = cursor.fetchall()
print("\n=== Documents trouvés ===")
for f in found:
    print(f"  ID:{f[0]} | Type:{f[1]} | Date:{f[3]} | {f[2]}")

conn.close()