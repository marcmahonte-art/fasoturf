"""
Interface DataProvider (#4).

Le moteur ne connaît QUE cette interface. Ajouter un fournisseur = ajouter une
classe, jamais modifier le moteur.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from ..schema import Race, RaceResult, Runner


class DataProvider(ABC):
    """Contrat commun à tous les fournisseurs de données hippiques."""

    name: str = "abstract"

    # -- Découverte -------------------------------------------------

    @abstractmethod
    def get_meetings(self, date: str) -> list[dict]:
        """Réunions disponibles pour une date (YYYY-MM-DD)."""

    @abstractmethod
    def get_races(self, date: str) -> list[Race]:
        """Courses disponibles pour une date."""

    @abstractmethod
    def get_race(self, race_id: str) -> Race | None:
        """Une course complète avec ses partants."""

    @abstractmethod
    def get_runners(self, race_id: str) -> list[Runner]:
        """Partants d'une course."""

    # -- Historique -------------------------------------------------

    @abstractmethod
    def get_horse_history(self, horse_id: str) -> list[dict]:
        """Sorties passées d'un cheval."""

    @abstractmethod
    def get_jockey_history(self, jockey_id: str) -> list[dict]:
        """Montes passées d'un jockey."""

    @abstractmethod
    def get_trainer_history(self, trainer_id: str) -> list[dict]:
        """Sorties passées d'un entraîneur."""

    # -- Marché & résultats -----------------------------------------

    @abstractmethod
    def get_odds(self, race_id: str) -> dict[int, list[dict]]:
        """Historique de cote par numéro de partant."""

    @abstractmethod
    def get_results(self, race_id: str) -> RaceResult | None:
        """Résultat officiel d'une course, si connu."""

    # -- Divers -----------------------------------------------------

    def close(self) -> None:  # pragma: no cover - défaut no-op
        """Libère les ressources éventuelles."""
