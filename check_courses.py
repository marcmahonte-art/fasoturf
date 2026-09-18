import sqlite3
conn = sqlite3.connect(r'C:\Users\Lenovo\Desktop\PMU\pmu-lonab-scraper\data\processed\pmu_lonab.db')
c = conn.cursor()
c.execute('SELECT course_id, date, reunion, course_num, hippodrome FROM courses LIMIT 5')
for row in c.fetchall():
    print(row)