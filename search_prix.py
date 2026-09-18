import sqlite3

conn = sqlite3.connect(r'C:\Users\Lenovo\Desktop\PMU\pmu-lonab-scraper\data\processed\pmu_lonab.db')
cursor = conn.cursor()

# Get date range
cursor.execute("SELECT MIN(date), MAX(date) FROM courses WHERE date IS NOT NULL")
dates = cursor.fetchone()
print(f"Plage de dates: {dates[0]} à {dates[1]}")

# Count courses by hippodrome
cursor.execute("SELECT hippodrome, COUNT(*) FROM courses GROUP BY hippodrome ORDER BY COUNT(*) DESC")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]} courses")

# Search for any PRIX in titre
cursor.execute("SELECT course_id, date, hippodrome, titre FROM courses WHERE LOWER(titre) LIKE '%prix%' ORDER BY date DESC LIMIT 20")
print("\n=== Courses avec 'PRIX' dans le titre ===")
for row in cursor.fetchall():
    print(f"  {row[0]} | {row[1]} | {row[2]} | {row[3][:80]}")

conn.close()