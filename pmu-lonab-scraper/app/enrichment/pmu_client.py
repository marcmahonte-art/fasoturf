"""
Client HTTP pour l'API publique PMU France avec résolveur DNS robuste.
"""
import socket
import logging
import time
import requests
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Fallback CloudFront IPs for online.turfinfo.api.pmu.fr if local ISP blocks or fails DNS
PMU_FALLBACK_IPS = [
    "99.86.159.69",
    "99.86.159.128",
    "99.86.159.19",
    "99.86.159.57"
]

_orig_getaddrinfo = socket.getaddrinfo

def _setup_dns_fallback():
    """Installe un résolveur de secours pour les domaines PMU si le DNS local échoue."""
    def custom_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
        try:
            return _orig_getaddrinfo(host, port, family, type, proto, flags)
        except (socket.gaierror, OSError):
            if "pmu.fr" in host or "pmutech.fr" in host:
                logger.debug("Utilisation de l'IP de secours PMU pour %s", host)
                return _orig_getaddrinfo(PMU_FALLBACK_IPS[0], port, family, type, proto, flags)
            raise

    socket.getaddrinfo = custom_getaddrinfo

_setup_dns_fallback()


class PMUApiClient:
    """Client pour interroger l'API publique PMU."""
    
    BASE_URL = "https://online.turfinfo.api.pmu.fr/rest/client/61"

    def __init__(self, timeout: int = 12, delay: float = 0.2):
        self.timeout = timeout
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json"
        })

    def _get(self, endpoint: str) -> Optional[Dict[str, Any]]:
        """Effectue une requête GET sur l'API PMU avec gestion d'erreur."""
        url = f"{self.BASE_URL}/{endpoint.lstrip('/')}"
        time.sleep(self.delay)
        try:
            response = self.session.get(url, timeout=self.timeout)
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                logger.debug("Ressource non trouvée (404) : %s", url)
                return None
            else:
                logger.warning("Erreur HTTP %s pour %s : %s", response.status_code, url, response.text[:150])
                return None
        except Exception as e:
            logger.warning("Exception réseau lors de la requête %s : %s", url, e)
            return None

    def get_programme(self, date_str: str) -> Optional[Dict[str, Any]]:
        """
        Récupère le programme complet pour une date.
        date_str doit être au format JJMMAAAA (ex: '11022024') ou AAAA-MM-JJ (ex: '2024-02-11').
        """
        formatted_date = self._format_date(date_str)
        return self._get(f"programme/{formatted_date}")

    def get_participants(self, date_str: str, reunion_num: int, course_num: int) -> Optional[Dict[str, Any]]:
        """
        Récupère les partants détaillés d'une course.
        Ex: date_str='11022024', reunion_num=1, course_num=3.
        """
        formatted_date = self._format_date(date_str)
        return self._get(f"programme/{formatted_date}/R{reunion_num}/C{course_num}/participants")

    def get_rapports(self, date_str: str, reunion_num: int, course_num: int) -> Optional[Dict[str, Any]]:
        """Récupère les rapports officiels et l'ordre d'arrivée."""
        formatted_date = self._format_date(date_str)
        return self._get(f"programme/{formatted_date}/R{reunion_num}/C{course_num}/rapports-definitifs")

    @staticmethod
    def _format_date(date_str: str) -> str:
        """Convertit '2024-02-11' ou '11/02/2024' en '11022024'."""
        clean = date_str.replace("-", "").replace("/", "").strip()
        if len(clean) == 8:
            # Si c'est AAAA MM JJ (ex: 20240211)
            if clean.startswith("20") or clean.startswith("19"):
                return f"{clean[6:8]}{clean[4:6]}{clean[0:4]}"
            # Si c'est déjà JJ MM AAAA (ex: 11022024)
            return clean
        raise ValueError(f"Format de date invalide : {date_str}")
