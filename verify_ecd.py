import sqlite3

conn = sqlite3.connect(r'C:\Users\Lenovo\Desktop\PMU\pmu-lonab-scraper\data\processed\pmu_lonab.db')
cursor = conn.cursor()

# 1. Verifier ECD documents
cursor.execute('SELECT COUNT(*) FROM ecd_documents')
print('ECD documents:', cursor.fetchone()[0])

cursor.execute('SELECT COUNT(*) FROM ecd_courses')
print('ECD courses:', cursor.fetchone()[0])

cursor.execute('SELECT COUNT(*) FROM ecd_paris')
print('ECD paris:', cursor.fetchone()[0])

# 2. Dates couvertes
cursor.execute('SELECT MIN(date), MAX(date) FROM ecd_documents WHERE date IS NOT NULL')
print('Periode ECD:', cursor.fetchone())

# 3. Reunions par date
cursor.execute('''
    SELECT date, reunion, COUNT(*) as nb_courses
    FROM ecd_documents
    WHERE date IS NOT NULL
    GROUP BY date, reunion
    ORDER BY date DESC, reunion
    LIMIT 20
''')
print('\nDernieres reunions ECD:')
for row in cursor.fetchall():
    print('  {} R{}: {} courses'.format(row[0], row[1], row[2]))

# 4. Jockeys uniques dans ECD (attelé) - via partants + courses
cursor.execute('''
    SELECT COUNT(DISTINCT p.driver_normalized) 
    FROM partants p
    JOIN courses c ON p.course_id = c.course_id
    JOIN ecd_courses ec ON c.course_id = ec.course_id
    WHERE c.discipline = "ATTELE" AND p.driver_normalized IS NOT NULL
''')
print('\nJockeys uniques (attelé) dans ECD:', cursor.fetchone()[0])

# 5. Top activité jockey/jour
cursor.execute('''
    SELECT 
        p.driver_normalized as jockey,
        c.date,
        c.reunion,
        COUNT(DISTINCT p.course_id) as montes_du_jour
    FROM partants p
    JOIN courses c ON p.course_id = c.course_id
    JOIN ecd_courses ec ON c.course_id = ec.course_id
    WHERE c.discipline = "ATTELE" AND p.driver_normalized IS NOT NULL
    GROUP BY p.driver_normalized, c.date, c.reunion
    ORDER BY montes_du_jour DESC
    LIMIT 20
''')
print('\nTop activite jockey/jour:')
for row in cursor.fetchall():
    print('  {:30s} | {} R{} | {} courses'.format(row[0], row[1], row[2], row[3]))

# 6. Distribution activité
cursor.execute('''
    SELECT 
        COUNT(DISTINCT p.course_id) as montes_du_jour,
        COUNT(*) as nb_occurrences
    FROM partants p
    JOIN courses c ON p.course_id = c.course_id
    JOIN ecd_courses ec ON c.course_id = ec.course_id
    WHERE c.discipline = "ATTELE" AND p.driver_normalized IS NOT NULL
    GROUP BY p.driver_normalized, c.date, c.reunion
''')
rows = cursor.fetchall()
dist = {}
for montes, count in rows:
    dist[montes] = dist.get(montes, 0) + count

print('\nDistribution activité jockey/jour:')
for montes in sorted(dist.keys()):
    print('  {} courses/jour: {} jockeys-jour'.format(montes, dist[montes]))

# 7. Taux de réussite par activité
cursor.execute('''
    SELECT 
        COUNT(DISTINCT p.course_id) as montes_du_jour,
        COUNT(*) as total_montes,
        SUM(CASE WHEN p.numero = json_extract(ec.arrivee_positions, '$[0]') THEN 1 ELSE 0 END) as victoires,
        ROUND(SUM(CASE WHEN p.numero = json_extract(ec.arrivee_positions, '$[0]') THEN 1.0 ELSE 0.0 END) * 100.0 / COUNT(*), 2) as taux_reussite
    FROM partants p
    JOIN courses c ON p.course_id = c.course_id
    JOIN ecd_courses ec ON c.course_id = ec.course_id
    WHERE c.discipline = "ATTELE" AND p.driver_normalized IS NOT NULL
    GROUP BY p.driver_normalized, c.date, c.reunion
''')
rows = cursor.fetchall()
by_activity = {}
for montes, total, vic, taux in rows:
    if montes not in by_activity:
        by_activity[montes] = {'total': 0, 'victoires': 0}
    by_activity[montes]['total'] += total
    by_activity[montes]['victoires'] += vic

print('\nTaux de reussite par niveau d\'activite:')
for montes in sorted(by_activity.keys()):
    d = by_activity[montes]
    taux = round(d['victoires'] * 100.0 / d['total'], 2) if d['total'] > 0 else 0
    print('  {} courses/jour: {}/{} = {}%'.format(montes, d['victoires'], d['total'], taux))

# 8. Réunions dans courses (attelé)
cursor.execute('''
    SELECT c.reunion, COUNT(*) 
    FROM courses c
    JOIN ecd_courses ec ON c.course_id = ec.course_id
    WHERE c.discipline = "ATTELE"
    GROUP BY c.reunion
    ORDER BY c.reunion
''')
print('\nRéunions dans courses (attelé):')
for row in cursor.fetchall():
    print('  R{}: {} courses'.format(row[0], row[1]))

# 9. Échantillon de données ECD pour vérifier structure
cursor.execute('''
    SELECT ed.date, ed.reunion, ed.hippodrome, ec.numero_course, ec.arrivee_positions
    FROM ecd_courses ec
    JOIN ecd_documents ed ON ec.document_id = ed.id
    WHERE ed.date IS NOT NULL
    ORDER BY ed.date DESC, ed.reunion, ec.numero_course
    LIMIT 10
''')
print('\nEchantillon ECD (derniers):')
for row in cursor.fetchall():
    print('  {} R{} {} C{} -> {}'.format(row[0], row[1], row[2], row[3], row[4]))

conn.close()