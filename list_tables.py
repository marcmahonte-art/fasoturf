import sqlite3

conn = sqlite3.connect(r'C:\Users\Lenovo\Desktop\PMU\pmu_master.db')
cursor = conn.cursor()

# List tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("=== Tables dans pmu_master.db ===")
for t in tables:
    print(f"  {t[0]}")

conn.close()