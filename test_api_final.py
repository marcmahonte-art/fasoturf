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

# Test 1: Programme aujourd'hui
today = '12092026'
print('=== TEST PROGRAMME ===')
try:
    r = session.get('https://online.turfinfo.api.pmu.fr/rest/client/61/programme/12092026?specialisation=INTERNET', timeout=15)
    print('Status: ' + str(r.status_code))
    if r.status_code == 200:
        data = r.json()
        print('Keys: ' + str(list(data.keys())))
        reunions = data.get('reunions', [])
        print('Reunions: ' + str(len(reunions)))
        for reun in reunions[:2]:
            print('  R' + str(reun.get('numeroReunion')) + ': ' + str(reun.get('hippodrome', {}).get('code')) + ' - ' + str(len(reun.get('courses', []))) + ' courses')
except Exception as e:
    print('Error: ' + str(e))

# Test 2: Participants
print('\n=== TEST PARTICIPANTS ===')
try:
    r = session.get('https://online.turfinfo.api.pmu.fr/rest/client/61/programme/11092026/R1/C1/participants?specialisation=INTERNET', timeout=15)
    print('Status: ' + str(r.status_code))
    if r.status_code == 200:
        data = r.json()
        print('Keys: ' + str(list(data.keys())))
        parts = data.get('participants', [])
        print('Participants: ' + str(len(parts)))
        for p in parts[:3]:
            print('  ' + str(p.get('numero')) + ': ' + str(p.get('nom')) + ' - ' + str(p.get('driver')) + ' - cote: ' + str(p.get('coteDirecte')))
except Exception as e:
    print('Error: ' + str(e))

# Test 3: Rapports
print('\n=== TEST RAPPORTS ===')
try:
    r = session.get('https://online.turfinfo.api.pmu.fr/rest/client/61/programme/11092026/R1/C1/rapports-definitifs?specialisation=INTERNET&combinaisonEnTableau=true', timeout=15)
    print('Status: ' + str(r.status_code))
    if r.status_code == 200:
        data = r.json()
        print('Keys: ' + str(list(data.keys())))
        rapports = data.get('rapports', [])
        print('Rapports: ' + str(len(rapports)))
        for rep in rapports[:2]:
            print('  ' + str(rep.get('typePari')) + ': arrivee=' + str(rep.get('arrivee')) + ' gains=' + str(rep.get('gainsBase')))
except Exception as e:
    print('Error: ' + str(e))

# Test 4: Citations (cotes)
print('\n=== TEST COTES ===')
try:
    r = session.get('https://online.turfinfo.api.pmu.fr/rest/client/61/programme/11092026/R1/C1/citations?paris=&specialisation=INTERNET&combinaisonEnTableau=true', timeout=15)
    print('Status: ' + str(r.status_code))
    if r.status_code == 200:
        data = r.json()
        print('Keys: ' + str(list(data.keys())))
        parts = data.get('participants', [])
        print('Participants: ' + str(len(parts)))
        for p in parts[:3]:
            print('  ' + str(p.get('numero')) + ': cote=' + str(p.get('coteDirecte')) + ' masse=' + str(p.get('masseEnjeu')))
except Exception as e:
    print('Error: ' + str(e))