import sqlite3
conn = sqlite3.connect(r'C:\Users\Lenovo\Desktop\PMU\pmu-lonab-scraper\data\processed\pmu_lonab.db')
c = conn.cursor()
c.execute('PRAGMA table_info(courses)')
for row in c.fetchall():
    print(row)
c.execute('PRAGMA table_info(documents)')
for row in c.fetchall():
    print(row)