# PHASE1_REP_ECD

## REP (`rep_documents`)

| Champ requis | Présent |
|---|---|
| `date_document` | ✅ |
| `date_course_cible` | ✅ |
| `game_type` | ✅ |
| `report_ordre_euros` | ✅ |
| `tierce_v_value` | ✅ |

| Mesure | Valeur |
|---|---|
| Documents REP | 45 |
| date_document min | 2024-04-30 |
| date_document max | 2026-09-06 |
| `date_document` ≠ `date_course_cible` | 41 |
| `date_course_cible` vide | 0 |

| game_type | Documents |
|---|---|
| (null) | 1 |
| 4+1 | 44 |

> ✅ Le parseur REP distingue correctement la date du document de la date cible (conforme spec §5).
> ⚠️ **Aucun REP n'a été converti en résultat.**

## ECD

| Mesure | Valeur |
|---|---|
| ecd_documents | 800 |
| ecd_courses | 6 509 |
| ecd_paris | 11 879 |
| Période | 2025-07-26 → 2026-09-06 |
| Courses ECD sans document | 6 509 |
| Courses ECD avec arrivée | 6 509 |

**Colonnes `ecd_documents` :** `id`, `document_id`, `date`, `reunion`, `hippodrome`, `discipline`, `date_heure_extraction`, `raw_text`

> ECD n'est **pas fusionné** avec `courses` en Phase 1.
