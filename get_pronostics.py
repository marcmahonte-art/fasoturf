#!/usr/bin/env python3
import requests
import socket
import dns.resolver
from datetime import datetime, timedelta

# DNS fix
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
            pass
    return original_getaddrinfo(host, port, family, type, proto, flags)

socket.getaddrinfo = custom_getaddrinfo

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json',
    'Referer': 'https://www.pmu.fr/',
    'Accept-Language': 'fr-FR,fr;q=0.9',
})

BASE = 'https://online.turfinfo.api.pmu.fr/rest/client/61'

def get_pronostics_for_date(date_str, label):
    print('\n' + '='*60)
    print('PRONOSTICS ' + label.upper() + ' (' + date_str + ')')
    print('='*60)
    
    r = session.get(BASE + '/programme/' + date_str + '?specialisation=INTERNET', timeout=15)
    if r.status_code != 200:
        print('Pas de programme pour cette date')
        return
    
    data = r.json()
    prog = data.get('programme', {}) if isinstance(data, dict) else {}
    reunions = prog.get('reunions', [])
    
    if not reunions:
        print('Aucune reunion programmee')
        return
    
    for reun in reunions:
        reun_num = reun.get('numOfficiel')
        if not reun_num:
            continue
            
        hippo = reun.get('hippodrome', {}).get('libelle', reun.get('hippodrome', {}).get('code', ''))
        print('\n--- Reunion ' + str(reun_num) + ' - ' + hippo + ' ---')
        
        courses = reun.get('courses', [])
        for course in courses:
            course_num = course.get('numOrdre')
            libelle = course.get('libelle') or course.get('libelleCourt')
            
            # Get pronostics
            url_prono = BASE + '/programme/' + date_str + '/R' + str(reun_num) + '/C' + str(course_num) + '/pronostics?commentaire=true'
            rp = session.get(url_prono, timeout=10)
            
            if rp.status_code == 200:
                prono_data = rp.json()
                
                # Handle different structures
                pronostics_list = []
                if isinstance(prono_data, dict):
                    # Check for 'prono_pmu_fr' key
                    if 'prono_pmu_fr' in prono_data and isinstance(prono_data['prono_pmu_fr'], dict):
                        selection = prono_data['prono_pmu_fr'].get('selection', [])
                        if isinstance(selection, list):
                            pronostics_list = selection
                    # Or direct 'pronostics' key
                    elif 'pronostics' in prono_data:
                        pronostics = prono_data['pronostics']
                        if isinstance(pronostics, list):
                            pronostics_list = pronostics
                        elif isinstance(pronostics, dict):
                            # Sometimes it's a dict with source keys
                            for v in pronostics.values():
                                if isinstance(v, dict) and 'selection' in v:
                                    pronostics_list = v['selection']
                                    break
                
                if pronostics_list:
                    print('  C' + str(course_num) + ' - ' + (libelle if libelle else 'Course') + ':')
                    for i, p in enumerate(pronostics_list[:5]):
                        ordre = p.get('rang', i+1)
                        nom = p.get('nom', p.get('num_partant', p.get('id_nav_partant', 'N/A')))
                        # Get horse name from num_partant if needed
                        if nom == 'N/A' or (isinstance(nom, str) and nom.isdigit()):
                            nom = 'Partant ' + str(p.get('num_partant', p.get('rang', i+1)))
                        cote = p.get('cote_prob', p.get('cote', 'N/A'))
                        driver = ''
                        print('    ' + str(ordre) + '. ' + str(nom) + ' (cote: ' + str(cote) + ')')
                else:
                    print('  C' + str(course_num) + ' - ' + (libelle if libelle else 'Course') + ': Pas de pronostics dispo')
            else:
                print('  C' + str(course_num) + ': Erreur recuperation pronostics')

def main():
    today = datetime.now().strftime('%d%m%Y')
    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%d%m%Y')
    
    get_pronostics_for_date(today, "AUJOURD'HUI")
    get_pronostics_for_date((datetime.now() + timedelta(days=1)).strftime('%d%m%Y'), "DEMAIN")

if __name__ == '__main__':
    main()