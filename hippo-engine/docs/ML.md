# Modèles et entraînement (#7-15)

## 1. Backends

Trois backends, choisis automatiquement par ordre de préférence :

| Priorité | Backend | Condition | Classe |
|---|---|---|---|
| 1 | CatBoost | `catboost` installé | `CatBoostClassifier` |
| 2 | scikit-learn | `sklearn` installé | `HistGradientBoostingClassifier` |
| 3 | **Python pur** | toujours | `PureLogisticRegression` |

Le backend utilisé est **enregistré dans le modèle sérialisé**. Aucune métrique
ne peut donc être confondue avec celle d'un autre backend.

Le backend pur (`PureLogisticRegression`) inclut une **standardisation des
features** — sans elle, la descente de gradient ne converge pas.

## 2. Cibles

| Modèle | Cible | Positifs |
|---|---|---|
| `catboost_win_v1` | `finish_position == 1` | 657 |
| `catboost_top3_v1` | `finish_position <= 3` | 1 932 |
| `catboost_top5_v1` | `finish_position <= 5` | 2 775 |

**Cas particulier du Top5** : les arrivées de la base source ne listent que
3 à 5 chevaux. Si l'arrivée compte moins de 5 chevaux, on **ne peut pas**
savoir si un non-arrivé était 5e. Ces lignes sont donc marquées `-1` et
exclues de l'entraînement — d'où `n = 1 115` (contre 2 408 pour win/top3).

## 3. Découpage temporel (#14)

**Jamais de split aléatoire.** Les données sont temporelles.

```
2024-02 → 2025-06   TRAIN        4 393 lignes
2025-07 → 2025-12   VALIDATION   2 408 lignes
2026-01 → 2026-09   TEST         3 243 lignes
```

Surchargeable : `--train-until`, `--valid-until`.

## 4. Statistiques jockey / entraîneur sans fuite

Le constructeur de dataset (`ml/models/dataset.py`) maintient des statistiques
**cumulatives** :

1. Les courses sont triées par date.
2. Pour une course du jour J, les stats utilisées proviennent uniquement des
   dates **strictement antérieures** à J.
3. Après traitement de la date J, les résultats de J sont intégrés.

Un cheval ne peut donc jamais « voir » sa propre performance.

## 5. Anti-leakage

Test bloquant : `ml/tests/test_no_leakage.py`

- aucun nom de feature interdit (`finish_position`, `arrivee`, `result`…)
- `compute_features()` ne doit jamais appeler `get_results()`
- l'historique d'un partant est strictement antérieur à la course
- le module de features ne contient aucun accès aux résultats

## 6. Métriques (#15)

Classification : accuracy, precision, recall, F1, ROC-AUC
Probabilités : log loss, Brier score, courbe de calibration
Pronostics : hit rates Top1 / Top3 / Top5 / Quinté

Toutes implémentées en Python pur (`ml/evaluation/metrics.py`).

## 7. Reproduction

```bash
python -m ml.scripts.train --train-until 2025-06-30 --valid-until 2025-12-31
```

Sortie : `ml/models/artifacts/catboost_{win,top3,top5}_v1.json`
+ `training_report.json`
