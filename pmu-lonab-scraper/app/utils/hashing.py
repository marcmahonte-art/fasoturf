"""
Utilitaire de hashing SHA-256 pour les fichiers PDF.
"""

import hashlib
from pathlib import Path


def compute_sha256(file_path: Path, chunk_size: int = 8192) -> str:
    """
    Calcule le hash SHA-256 d'un fichier.

    Args:
        file_path: Chemin vers le fichier.
        chunk_size: Taille des blocs de lecture (défaut 8 Ko).

    Returns:
        Le hash SHA-256 en hexadécimal.

    Raises:
        FileNotFoundError: Si le fichier n'existe pas.
    """
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            sha256.update(chunk)
    return sha256.hexdigest()
