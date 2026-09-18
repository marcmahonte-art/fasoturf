import sqlite3
from datetime import datetime

today = datetime.now().strftime('%Y-%m-%d')
print(f"Date aujourd'hui: {today}")

conn = sqlite3.connect(r'C:\Users\Lenovo\Desktop\PMU\pmu-lonab-scraper\data\processed\pmu_lonab.db')
cursor = conn.cursor()

# Check courses for today
cursor.execute("SELECT course_id, date, hippodrome, reunion, course_num, titre FROM courses WHERE date = ? ORDER BY reunion, course_num", (today,))
rows = cursor.fetchall()
print(f"\n=== Courses du {today} ===")
for row in rows:
    print(f"  {row[0]} | R{row[3]}C{row[4]} | {row[2]} | {row[5]}")

# Also check recent dates
for days_ago in range(1, 8):
    from datetime import timedelta
    d = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d')
    cursor.execute("SELECT COUNT(*) FROM courses WHERE date = ?", (d,))
    count = cursor.fetchone()[0]
    if count > 0:
        cursor.execute("SELECT course_id, hippodrome, reunion, course_num, titre FROM courses WHERE date = ? ORDER BY reunion, course_num", (d,))
        rows = cursor.fetchall()
        print(f"\n=== Courses du {d} ({count} courses) ===")
        for row in rows:
            print(f"  {row[0]} | R{row[2]}C{row[3]} | {row[1]} | {row[4]}")

conn.close()