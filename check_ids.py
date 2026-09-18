import sqlite3

conn = sqlite3.connect(r'C:\Users\Lenovo\Desktop\PMU\pmu-lonab-scraper\data\processed\pmu_lonab.db')
cursor = conn.cursor()

# Check course_id formats
cursor.execute('SELECT DISTINCT course_id FROM courses WHERE discipline="ATTELE" LIMIT 10')
print('courses.course_id (ATTELE):')
for row in cursor.fetchall():
    print(' ', row[0])

cursor.execute('SELECT DISTINCT course_id FROM ecd_courses LIMIT 10')
print('\necd_courses.course_id:')
for row in cursor.fetchall():
    print(' ', row[0])

# Check if any overlap
cursor.execute('''
    SELECT COUNT(*) FROM courses c
    JOIN ecd_courses ec ON c.course_id = ec.course_id
    WHERE c.discipline = "ATTELE"
''')
print('\nOverlap courses <-> ecd_courses:', cursor.fetchone()[0])

# Check partants for attelé
cursor.execute('SELECT COUNT(*) FROM partants p JOIN courses c ON p.course_id = c.course_id WHERE c.discipline = "ATTELE"')
print('Partants attelé (JOURNAL):', cursor.fetchone()[0])

# Check discipline values
cursor.execute('SELECT DISTINCT discipline FROM courses')
print('\nDisciplines dans courses:', cursor.fetchall())

cursor.execute('SELECT DISTINCT discipline FROM ecd_documents')
print('Disciplines dans ecd_documents:', cursor.fetchall())

# Check ecd_documents discipline values
cursor.execute('SELECT DISTINCT discipline FROM ecd_documents')
rows = cursor.fetchall()
for r in rows:
    print('  ecd_documents discipline:', repr(r[0]))

conn.close()