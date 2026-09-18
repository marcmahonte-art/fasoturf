import sqlite3
conn = sqlite3.connect(r'C:\Users\Lenovo\Desktop\PMU\pmu-lonab-scraper\data\processed\pmu_lonab.db')
c = conn.cursor()
c.execute('SELECT name FROM sqlite_master WHERE type="table"')
print([r[0] for r in c.fetchall()])