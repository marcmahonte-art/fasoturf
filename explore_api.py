import requests
import socket
import dns.resolver

# Custom DNS resolver using Google DNS
resolver = dns.resolver.Resolver()
resolver.nameservers = ['8.8.8.8', '1.1.1.1']

original_getaddrinfo = socket.getaddrinfo

def custom_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
    if host in ['www.pmu.fr', 'online.turfinfo.api.pmu.fr', 'turfinfo.api.pmu.fr', 'api.pmu.fr', 'data.pmu.fr']:
        try:
            answers = resolver.resolve(host, 'A')
            ips = [r.to_text() for r in answers]
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, '', (ips[0], port))]
        except Exception as e:
            print('DNS resolve failed for ' + host + ': ' + str(e))
    return original_getaddrinfo(host, port, family, type, proto, flags)

socket.getaddrinfo = custom_getaddrinfo

import requests

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json',
    'Referer': 'https://www.pmu.fr/',
})

BASE = 'https://online.turfinfo.api.pmu.fr/rest/client/61'

# Test date: hier
date_test = '11092026'

print('=== EXPLORATION COMPLÈTE DES STRUCTURES ===')

# 1. Programme
print('\n=== PROGRAMME ===')
r = session.get(f'{BASE}/programme/11092026?specialisation=INTERNET', timeout=15)
prog = r.json()
print('Keys: ' + str(list(prog.keys())))
print('Programme keys: ' + str(list(prog.get('programme', {}).keys())))

prog_data = prog.get('programme', {})
reunions = prog_data.get('reunions', [])
print('Nb reunions: ' + str(len(reunions)))
for reun in reunions[:2]:
    print('  R' + str(reun.get('numeroReunion')) + ': ' + str(reun.get('hippodrome', {}).get('code')) + ' - ' + str(len(reun.get('courses', []))) + ' courses')
    for course in reun.get('courses', [])[:3]:
        print('    C' + str(course.get('numeroCourse')) + ': ' + str(course.get('libelleCourse')) + ' - ' + str(course.get('distance')) + 'm - ' + str(course.get('nombreDeclares')) + ' partants')

# 2. Participants détaillés
print('\n=== PARTICIPANTS R1C1 ===')
r = session.get('https://online.turfinfo.api.pmu.fr/rest/client/61/programme/11092026/R1/C1/participants?specialisation=INTERNET', timeout=15)
parts_data = r.json()
print('Keys: ' + str(list(parts_data.keys())))
participants = parts_data.get('participants', [])
print('Nb participants: ' + str(len(participants)))
if participants:
    p = participants[0]
    print('Champs participant: ' + str(list(p.keys())))
    print('Exemple: ' + str({k: p.get(k) for k in ['numero', 'nom', 'age', 'sexe', 'driver', 'entraineur', 'coteDirecte', 'musique', 'gainsCarriere', 'statut', 'corde', 'poids', 'idCheval'] if p.get(k) is not None}))

# 3. Rapports
print('\n=== RAPPORTS ===')
r = session.get('https://online.turfinfo.api.pmu.fr/rest/client/61/programme/11092026/R1/C1/rapports-definitifs?specialisation=INTERNET&combinaisonEnTableau=true', timeout=15)
rapports = r.json()
print('Type: ' + str(type(rapports)))
if isinstance(rapports, list):
    print('Liste de ' + str(len(rapports)) + ' rapports')
    for rap in rapports[:3]:
        print('  ' + str(rap.get('typePari')) + ': arrivee=' + str(rap.get('arrivee')) + ' gainsBase=' + str(rap.get('gainsBase')) + ' nbGagnants=' + str(rap.get('nbGagnants')))

# 4. Citations (cotes)
print('\n=== CITATIONS ===')
r = session.get('https://online.turfinfo.api.pmu.fr/rest/client/61/programme/11092026/R1/C1/citations?paris=&specialisation=INTERNET&combinaisonEnTableau=true', timeout=15)
citations = r.json()
print('Keys: ' + str(list(citations.keys())))
liste_cit = citations.get('listeCitations', [])
print('Nb citations: ' + str(len(liste_cit)))
if liste_cit:
    c = liste_cit[0]
    print('Champs citation: ' + str(list(c.keys())))
    print('Exemple: ' + str({k: c.get(k) for k in ['numero', 'coteDirecte', 'masseEnjeu', 'coteReference', 'evolutionCote'] if c.get(k) is not None}))

# 5. Météo
print('\n=== MÉTÉO ===')
r = session.get('https://online.turfinfo.api.pmu.fr/rest/client/61/programme/11092026/hippodrome/VIN/meteo', timeout=15)
meteo = r.json()
print('Keys: ' + str(list(meteo.keys())))
print('Exemple: ' + str({k: meteo.get(k) for k in ['temperature', 'vent', 'humidite', 'condition', 'terrain'] if meteo.get(k) is not None}))

# 6. Performances cheval (premier cheval)
print('\n=== PERFORMANCES CHEVAL ===')
r = session.get('https://online.turfinfo.api.pmu.fr/rest/client/61/programme/11092026/R1/C1/participants?specialisation=INTERNET', timeout=15)
parts = r.json().get('participants', [])
if parts:
    cheval_id = parts[0].get('idCheval')
    if cheval_id:
        r = session.get('https://online.turfinfo.api.pmu.fr/rest/client/61/programme/id_cheval/' + str(cheval_id) + '/light-performances', timeout=15)
        perf = r.json()
        print('Type: ' + str(type(perf)))
        if isinstance(perf, dict):
            print('Keys: ' + str(list(perf.keys())))
        elif isinstance(perf, list):
            print('Liste de ' + str(len(perf)) + ' performances')
            if perf:
                print('Premier: ' + str(list(perf[0].keys())))

# 7. Pronostics
print('\n=== PRONOSTICS ===')
r = session.get('https://online.turfinfo.api.pmu.fr/rest/client/61/programme/11092026/R1/C1/pronostics?commentaire=true', timeout=15)
prono = r.json()
print('Type: ' + str(type(prono)))
if isinstance(prono, dict):
    print('Keys: ' + str(list(prono.keys())))
elif isinstance(prono, list):
    print('Liste de ' + str(len(prono)))

# 8. Dernières courses
print('\n=== DERNIÈRES COURSES ===')
r = session.get('https://online.turfinfo.api.pmu.fr/rest/client/61/programme/dernieresCourses?specialisation=INTERNET&nb-courses=2', timeout=15)
der = r.json()
print('Type: ' + str(type(der)))
if isinstance(der, dict):
    print('Keys: ' + str(list(der.keys())))
elif isinstance(der, list):
    print('Liste de ' + str(len(der)))

print('\n=== EXPLORATION TERMINÉE ===')