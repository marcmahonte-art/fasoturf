#!/usr/bin/env python3
"""
Test rapide des endpoints API PMU Turfinfo
"""

import requests
import json
from datetime import datetime, timedelta

BASE = "https://online.turfinfo.api.pmu.fr/rest/client/61"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
    "Referer": "https://www.pmu.fr/",
    "Origin": "https://www.pmu.fr",
    "Connection": "keep-alive",
}

SESSION = requests.Session()
SESSION.headers.update(HEADERS)

def test_endpoint(name, url, params=None):
    """Test un endpoint et affiche le résultat"""
    print(f"\n{'='*60}")
    print(f"TEST: {name}")
    print(f"URL: {url}")
    print(f"{'='*60}")
    
    try:
        r = SESSION.get(url, params=params, timeout=15)
        print(f"Status: {r.status_code}")
        print(f"Content-Type: {r.headers.get('Content-Type', 'N/A')}")
        print(f"Taille: {len(r.content)} bytes")
        
        if r.status_code == 200:
            try:
                data = r.json()
                # Afficher structure
                if isinstance(data, dict):
                    print(f"Clés racine: {list(data.keys())}")
                    # Échantillon
                    for k, v in list(data.items())[:5]:
                        if isinstance(v, (list, dict)):
                            print(f"  {k}: {type(v).__name__} (len={len(v) if hasattr(v, '__len__') else 'N/A'})")
                        else:
                            print(f"  {k}: {v}")
                elif isinstance(data, list):
                    print(f"Liste de {len(data)} éléments")
                    if data:
                        print(f"  Premier: {json.dumps(data[0], ensure_ascii=False)[:200]}")
                return data
            except json.JSONDecodeError:
                print(f"Réponse non-JSON: {r.text[:200]}")
                return r.text
        elif r.status_code == 403:
            print("❌ 403 Forbidden - Authentification requise")
        elif r.status_code == 429:
            print("❌ 429 Too Many Requests - Rate limited")
        elif r.status_code == 404:
            print("❌ 404 Not Found - Endpoint ou date invalide")
        else:
            print(f"❌ Erreur {r.status_code}: {r.text[:200]}")
    except requests.exceptions.Timeout:
        print("❌ Timeout")
    except requests.exceptions.ConnectionError:
        print("❌ Erreur de connexion")
    except Exception as e:
        print(f"❌ Exception: {e}")
    return None

def main():
    # Date d'hier (format DDMMYYYY) - plus sûr car course terminée
    today = datetime.now()
    yesterday = (today - timedelta(days=1)).strftime("%d%m%Y")
    today_str = today.strftime("%d%m%Y")
    
    print(f"Date test: {yesterday} (hier) et {today_str} (aujourd'hui)")
    print(f"Base URL: {BASE}")
    
    # 1. Programme du jour (aujourd'hui)
    print("\n" + "="*60)
    print("1. PROGRAMME DU JOUR")
    test_endpoint(
        "Programme aujourd'hui",
        f"{BASE}/programme/{today_str}?specialisation=INTERNET"
    )
    
    # 2. Programme d'hier (courses terminées)
    test_endpoint(
        "Programme hier",
        f"{BASE}/programme/{yesterday}?specialisation=INTERNET"
    )
    
    # 3. Participants d'une course spécifique (R1C1 hier)
    print("\n" + "="*60)
    print("2. PARTANTS COURSE SPÉCIFIQUE")
    test_endpoint(
        "Participants R1C1 hier",
        f"{BASE}/programme/{yesterday}/R1/C1/participants?specialisation=INTERNET"
    )
    
    # 4. Rapports définitifs hier
    print("\n" + "="*60)
    print("3. RAPPORTS DÉFINITIFS")
    test_endpoint(
        "Rapports R1C1 hier",
        f"{BASE}/programme/{yesterday}/R1/C1/rapports-definitifs?specialisation=INTERNET&combinaisonEnTableau=true"
    )
    
    # 5. Cotes temps réel (hier - pour voir structure)
    print("\n" + "="*60)
    print("4. COTES / CITATIONS")
    test_endpoint(
        "Citations R1C1 hier",
        f"{BASE}/programme/{yesterday}/R1/C1/citations?paris=&specialisation=INTERNET&combinaisonEnTableau=true"
    )
    
    # 5. Météo hippodrome
    print("\n" + "="*60)
    print("5. MÉTÉO")
    test_endpoint(
        "Météo Vincennes hier",
        f"{BASE}/programme/{yesterday}/hippodrome/VIN/meteo"
    )
    
    # 6. Replays
    print("\n" + "="*60)
    print("6. REPLAYS")
    test_endpoint(
        "Replay R1C2 hier",
        f"{BASE}/replays/{yesterday}/R1/C2?specialisation=ONLINE"
    )

if __name__ == "__main__":
    main()