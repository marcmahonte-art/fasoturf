import sqlite3

conn = sqlite3.connect(r'C:\Users\Lenovo\Desktop\PMU\pmu-lonab-scraper\data\processed\pmu_lonab.db')
cursor = conn.cursor()

# Get all courses on the most recent date
cursor.execute("SELECT course_id, date, hippodrome, reunion, course_num, titre FROM courses WHERE date = '2026-09-10' ORDER BY reunion, course_num")
rows = cursor.fetchall()
print("=== Courses du 2026-09-10 ===")
for row in rows:
    print(f"  {row[0]} | R{row[3]}C{row[4]} | {row[2]} | {row[5]}")

# Also check 2026-09-09
cursor.execute("SELECT course_id, date, hippodrome, reunion, course_num, titre FROM courses WHERE date = '2026-09-09' ORDER BY reunion, course_num")
rows = cursor.fetchall()
print("\n=== Courses du 2026-09-09 ===")
for row in rows:
    print(f"  {row[0]} | R{row[3]}C{row[4]} | {row[2]} | {row[5]}")

conn.close()