import sqlite3

conn = sqlite3.connect(r'C:\Users\Lenovo\Desktop\PMU\pmu-lonab-scraper\data\processed\pmu_lonab.db')
cursor = conn.cursor()

# Search more broadly - check all unique titles
cursor.execute("SELECT DISTINCT titre FROM courses WHERE titre IS NOT NULL ORDER BY titre")
titles = cursor.fetchall()
print("=== Tous les titres de courses ===")
for t in titles:
    print(f"  {t[0]}")

conn.close()