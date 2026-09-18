"""
Construction du dataset d'entraînement (#8, #14).

Deux garanties anti-fuite :

1. **Temporelle** — les statistiques jockey/entraîneur utilisées pour une
   course proviennent uniquement des courses de dates STRICTEMENT antérieures.
2. **Cible** — les labels (win / top3 / top5) sont extraits des résultats et
   ne sont jamais injectés dans les features.

Le découpage train / validation / test est chronologique, jamais aléatoire.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from ..config import Config, load_config
from ..data.schema import Race, RaceResult
from ..features.engineering import Features, build_factors, compute_features
from ..models.rank import compute_rank


@dataclass(slots=True)
class DatasetRow:
    race_id: str
    date: str
    number: int
    features: Features
    label_win: int
    label_top3: int
    label_top5: int
    top5_known: bool = True


@dataclass(slots=True)
class Dataset:
    rows: list[DatasetRow] = field(default_factory=list)
    feature_names: list[str] = field(default_factory=list)

    def split_xy(self) -> tuple[list[list[float]], dict[str, list[int]]]:
        X = [[row.features.to_vector().get(name, 0.0) for name in self.feature_names]
             for row in self.rows]
        labels = {
            "win": [row.label_win for row in self.rows],
            "top3": [row.label_top3 for row in self.rows],
            # -1 = inconnu (arrivée tronquée à moins de 5 chevaux) : exclu de l'entraînement
            "top5": [row.label_top5 if row.top5_known else -1 for row in self.rows],
        }
        return X, labels

    def split_chronological(self, train_until: str, valid_until: str) -> tuple["Dataset", "Dataset", "Dataset"]:
        train = Dataset(feature_names=self.feature_names)
        valid = Dataset(feature_names=self.feature_names)
        test = Dataset(feature_names=self.feature_names)
        for row in self.rows:
            if row.date <= train_until:
                train.rows.append(row)
            elif row.date <= valid_until:
                valid.rows.append(row)
            else:
                test.rows.append(row)
        return train, valid, test

    def __len__(self) -> int:
        return len(self.rows)


def _position_of(number: int, result: RaceResult | None) -> int | None:
    if not result or not result.finish_order:
        return None
    try:
        return result.finish_order.index(number) + 1
    except ValueError:
        return None


def build_dataset(
    provider,
    race_ids: list[str],
    *,
    config: Config | None = None,
    verbose: bool = False,
) -> Dataset:
    """
    Construit le dataset à partir d'une liste de courses ordonnées par date.

    ``provider`` doit exposer ``get_race`` et ``get_results``.
    """
    cfg = config or load_config()
    dataset = Dataset()

    # Statistiques cumulatives (mises à jour APRÈS chaque date).
    jockey_stats: dict[str, dict] = {}
    trainer_stats: dict[str, dict] = {}
    current_date: str | None = None

    races: list[tuple[str, Race, RaceResult | None]] = []
    for race_id in race_ids:
        race = provider.get_race(race_id)
        if race is None or len(race.active_runners) < 4:
            continue
        races.append((race_id, race, provider.get_results(race_id)))

    races.sort(key=lambda item: item[1].date)

    for race_id, race, result in races:
        # Changement de date -> on intègre les résultats de la date précédente.
        if current_date is not None and race.date != current_date:
            _update_person_stats(races, current_date, jockey_stats, trainer_stats)
        current_date = race.date

        features = compute_features(race, jockey_stats=jockey_stats, trainer_stats=trainer_stats)
        build_factors(features)

        if not result or not result.finish_order:
            continue

        arrival_len = len(result.finish_order)
        # La cible Top5 n'est exploitable que si l'arrivée liste au moins
        # 5 chevaux. Sinon on ne sait pas si un non-arrivé était 5e.
        race_top5_known = arrival_len >= 5
        for number, feat in features.items():
            pos = _position_of(number, result)
            if pos is not None:
                label_top5 = 1 if pos <= 5 else 0
            else:
                label_top5 = 0
            dataset.rows.append(DatasetRow(
                race_id=race_id,
                date=race.date,
                number=number,
                features=feat,
                label_win=1 if pos == 1 else 0,
                label_top3=1 if (pos is not None and pos <= 3) else 0,
                label_top5=label_top5,
                top5_known=race_top5_known,
            ))

        if verbose:
            print(f"  {race.date}  {race.hippodrome:<22} {len(features):>3} partants")

    if dataset.rows:
        dataset.feature_names = sorted(dataset.rows[0].features.to_vector().keys())
    return dataset


def _update_person_stats(
    races: list[tuple[str, Race, RaceResult | None]],
    date: str,
    jockey_stats: dict[str, dict],
    trainer_stats: dict[str, dict],
) -> None:
    """Intègre les résultats d'une date dans les stats cumulatives."""
    for _race_id, race, result in races:
        if race.date != date or not result:
            continue
        for runner in race.active_runners:
            pos = _position_of(runner.number, result)
            if pos is None:
                continue
            if runner.jockey:
                _accumulate(jockey_stats, runner.jockey.name, pos)
            if runner.trainer:
                _accumulate(trainer_stats, runner.trainer.name, pos)


def _accumulate(stats: dict[str, dict], key: str, position: int) -> None:
    entry = stats.setdefault(key, {"starts": 0, "wins": 0, "places": 0})
    entry["starts"] += 1
    if position == 1:
        entry["wins"] += 1
    if position <= 3:
        entry["places"] += 1
    entry["win_rate"] = round(entry["wins"] / entry["starts"], 4)
    entry["place_rate"] = round(entry["places"] / entry["starts"], 4)


def rank_dataset(dataset: Dataset) -> dict[str, int]:
    """Statistiques descriptives du dataset."""
    races = {row.race_id for row in dataset.rows}
    return {
        "rows": len(dataset.rows),
        "races": len(races),
        "positive_win": sum(r.label_win for r in dataset.rows),
        "positive_top3": sum(r.label_top3 for r in dataset.rows),
        "positive_top5": sum(r.label_top5 for r in dataset.rows),
    }
