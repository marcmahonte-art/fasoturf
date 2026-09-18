# Logique de pronostic (#21-24)

Ce document décrit **comment** le moteur passe des scores à une sélection
publiée. Tout est explicable : chaque catégorie a un critère énonçable.

## 1. Du score au classement

Pour chaque partant actif :

```
RANK_SCORE  = 25 % forme + 20 % rating + 10 % distance + 10 % terrain
            + 10 % jockey + 10 % entraîneur + 5 % poids + 5 % corde
            + 5 % régularité                    (sous-scores 0..100)

FINAL_SCORE = 30 % CatBoost + 25 % Top3 + 20 % RANK + 15 % Forme + 10 % Value
```

Les deux jeux de pondérations sont configurables (`ml/config.py`, surchargeables
par l'administration). Ils doivent sommer à 1.0 — la configuration est validée
au démarrage.

Les chevaux sont classés par `FINAL_SCORE` décroissant.

## 2. Catégories de sélection

### BASE
Critère : `top3_probability >= 0.25` **et** incertitude `<= 0.35`.

L'incertitude est l'écart entre les signaux du modèle :
`|top3_probability − catboost_probability|`. Un faible écart = les modèles
sont d'accord = base solide.

Si moins de 2 candidats, repli explicite sur les 2-3 meilleurs scores.

### CHANCE
Critère : `top5_probability >= 0.35`, hors base. Complétée par régularité.

### OUTSIDER
Critère : `is_value` **et** `final_score >= 35`. Si aucun, repli explicable
sur les mieux classés à cote `>= 10`.

### VALUE
Critère strict : `model_probability > implied_probability` avec
`edge >= VALUE_THRESHOLD` et `ratio >= VALUE_RATIO_THRESHOLD`.

## 3. Construction du Quinté

```
QUINTÉ      = bases (2) + chances (3)        -> 5 chevaux
QUINTÉ ÉL.  = quinté + 1er outsider + ...    -> 7 chevaux
TIERCÉ      = 3 meilleurs scores
QUARTÉ+     = 4 meilleurs scores
```

Le moteur produit quatre formules de jeu :

| Formule | Champ | Combinaisons |
|---|---|---|
| Quinté ordre | quinté | 1 |
| Quinté désordre | quinté trié | 1 |
| Champ réduit | bases + chances | n·(n−1)·(n−2)·(n−3)·(n−4) |
| Champ total | sélection élargie | idem sur 7 |

## 4. Score de confiance (#19)

La confiance n'est **jamais** « gagnant assuré ». Elle est calculée :

| Signal | Effet |
|---|---|
| Qualité des données complète | +2 |
| Bon accord entre modèles (écart ≤ 0.15) | +2 |
| Peloton bien séparé (top1−top3 ≥ 15 pts) | +2 |
| Cotes volatiles sur certains partants | −1 |

`HIGH` si score ≥ 5, `MEDIUM` si ≥ 3, sinon `LOW`.

Chaque décision est renvoyée dans `confidence_reasons` — affichable tel quel.

## 5. Diversification (#25)

Le champ élargi ajoute un outsider à value positive même s'il n'est pas dans
les 5 meilleurs scores. Objectif : éviter une sélection trop corrélée aux
mêmes profils. Ce choix est tracé dans `selection.rationale["outsider"]`.

## 6. Données insuffisantes (#32)

Si la qualité est `DATA_INSUFFICIENT`, **aucune prédiction normale n'est
produite**. Le moteur renvoie :

> « Données insuffisantes pour une prédiction fiable. »

Critères : moins de 80 % des partants avec cote, ou moins de 60 % avec un
historique d'au moins 3 sorties.
