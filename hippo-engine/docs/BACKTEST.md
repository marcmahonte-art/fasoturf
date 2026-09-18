# Backtest — méthodologie (#30, #31)

## 1. Principe

Chaque prédiction est générée **avec les seules données connues avant la
course**, puis comparée à l'arrivée réelle. Aucun ajustement a posteriori.

## 2. Le piège des métriques trompeuses

Un taux brut n'est **pas** interprétable. Exemple mesuré :

> « top3_hit_rate = 55.9 % »

Avec 3 chevaux prédits sur 14 partants, un tirage **aléatoire** obtient déjà
~55 %. Ce chiffre ne mesure donc rien.

C'est exactement ce que la règle #31 interdit : publier un pourcentage sans
référence.

## 3. Les métriques retenues

| Métrique | Définition | Référence |
|---|---|---|
| `winner_hit_rate` | le n°1 du modèle a gagné | **favori du marché** |
| `top3_precision` | part de nos 3 premiers dans le vrai top 3 | **top 3 du marché** |
| `edge_vs_favorite` | écart de `winner_hit_rate` | — |
| `brier` / `log_loss` | qualité des probabilités | 0.25 / aléatoire |
| `roi` | mise 1 € sur les VALUE | — |

**Le favori du marché est la référence obligatoire.** Sans lui, aucun résultat
n'est interprétable.

## 4. Résultats actuels (2026, hors échantillon)

228 courses, du 2026-01-02 au 2026-09-08 :

| Métrique | Modèle | Favori marché | Écart |
|---|---|---|---|
| Gagnant trouvé | 18.0 % | 23.2 % | −5.3 pts |
| Précision Top 3 | 33.0 % | 36.0 % | −3.0 pts |
| Brier | 0.146 | — | — |
| Log loss | 0.456 | — | — |
| ROI (VALUE) | −8.3 % | — | — |

### Évolution

| Version | Gagnant trouvé |
|---|---|
| RANK seul (aucun entraînement) | 10.2 % |
| Modèles entraînés | 18.0 % |
| Favori du marché | 23.2 % |

**Conclusion honnête : +7.8 points grâce à l'entraînement, mais toujours
−5.3 points derrière le marché.** Le moteur n'est pas encore rentable.

## 5. Pistes identifiées

1. **Intégrer la cote dans le Fusion Engine** — le marché est aujourd'hui
   ignoré par la fusion, alors que c'est le meilleur prédicteur connu.
2. **Combler les données manquantes** — `api_meteo` est vide,
   `partitions_enrichies` à 185/13 163, `evolution_cote` vide.
3. **Modèle de ranking** (LambdaRank / YetiRank CatBoost) plutôt que
   classification binaire par cheval.
4. **Plus de données** — 708 courses est petit pour 34 features.

## 6. Ventilation

Le backtest produit automatiquement :

- `performance_by_month`
- `performance_by_hippodrome`
- `performance_by_race_type`
- `performance_by_odds_range`

```bash
python -m ml.scripts.backtest_cli --from 2026-01-01 --to 2026-09-30 --models
python -m ml.scripts.backtest_cli --all --models --json > backtest.json
```
