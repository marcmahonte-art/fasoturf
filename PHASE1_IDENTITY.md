# IDENTITY_READINESS

> **Aucun identifiant n'est créé en Phase 1.** Mesure de l'état actuel uniquement.

| Identifiant | Existe | Présent dans | Remplissage | Statut |
|---|---|---|---|---|
| `horse_id` | **NON** | — | — | NOT_IMPLEMENTED |
| `jockey_id` | **NON** | — | — | NOT_IMPLEMENTED |
| `trainer_id` | **NON** | — | — | NOT_IMPLEMENTED |
| `hippodrome_id` | **NON** | — | — | NOT_IMPLEMENTED |
| `race_id` | **NON** | — | — | NOT_IMPLEMENTED |
| `external_entity_mapping` | **NON** | — | — | à créer en Phase 4 |

## `course_id` — état réel (mesuré)

| Mesure | Valeur |
|---|---|
| Lignes `courses` | 929 |
| `courses.course_id` rempli | 610 |
| `courses.course_id` distinct | 604 |
| **Collisions** (rempli − distinct) | **6** |
| `partants.course_id` rempli | 8 642 |
| `resultats.course_id` rempli | 934 |

> ⚠️ `course_id` n'est **pas vide** (contrairement à l'hypothèse initiale de l'audit §2.2), mais il est **non unique** : plusieurs `document_id` peuvent partager la même valeur (ex. `1995-07-18_DEAUVILLELATOUQUES_C8` → 4 documents). Le format est hétérogène (`JH_<date>` et `<date>_<HIPPODROME>_C<n>`). Il reste donc **inutilisable comme identifiant de course**.

## Conclusion

**IDENTITY_READINESS = PARTIAL**

Les noms textuels (`nom_cheval_normalized`, `driver_normalized`, `entraineur_normalized`) sont aujourd'hui les seuls identifiants disponibles. Leur usage comme clé est **proscrit** (spec §9) : à traiter en Phase 2.
