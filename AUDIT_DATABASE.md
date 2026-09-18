# AUDIT — BASES DE DONNÉES DU PROJET

- Racine analysée : `C:\Users\Lenovo\Desktop\PMU`
- Bases détectées : **15**
- Date de l'audit : 2026-09-16 18:11:11

> Audit **en lecture seule** (`mode=ro`). Aucune écriture, aucune migration.

## 1. Synthèse

| Base | Taille | Tables | SHA-256 (12) |
|---|---:|---:|---|
| `pmu-lonab-scraper/data/master/pmu_master.db` | 40.3 Mo | 19 | `dd886c3051f3` |
| `pmu-lonab-scraper/data/backups/pmu_master_before_lonab_20260916_0358.db` | 39.1 Mo | 19 | `af8de3f09745` |
| `pmu-lonab-scraper/data/processed/pmu_lonab.db` | 36.1 Mo | 19 | `d71f6a013ff7` |
| `pmu-lonab-scraper/data/backups/phase1/pmu_lonab_phase1_backup_20260913_142930.db` | 36.1 Mo | 19 | `d71f6a013ff7` |
| `debug.db` | 20.0 Ko | 2 | `86d4b5d2bb66` |
| `debug2.db` | 20.0 Ko | 2 | `d06ba9a60077` |
| `test.db` | 12.0 Ko | 1 | `2153925f2905` |
| `test2.db` | 12.0 Ko | 1 | `2153925f2905` |
| `test3.db` | 12.0 Ko | 1 | `2153925f2905` |
| `test4.db` | 12.0 Ko | 1 | `bbaf7b71880e` |
| `test5.db` | 12.0 Ko | 1 | `3c7dbbf00631` |
| `test6.db` | 12.0 Ko | 1 | `0c961e24ae34` |
| `test7.db` | 12.0 Ko | 1 | `07c3fde5174c` |
| `test8.db` | 12.0 Ko | 1 | `4ea4c0ab4758` |
| `test9.db` | 12.0 Ko | 1 | `be62e808343a` |

## 2. Base `pmu-lonab-scraper/data/master/pmu_master.db`

- Taille : **40.3 Mo**
- SHA-256 : `dd886c3051f3a7dad5dfc6ec596546c436fedd83f1362a0118d8396f3986f6e6`
- Vues : aucune

### 2.1 Tables et volumes

| Table | Lignes | Clé primaire | Index |
|---|---:|---|---|
| `comment_features` | 10 116 | `runner_id` | `idx_cf_race` |
| `data_version` | 2 | `version_id` | — |
| `external_entity_mapping` | 0 | `internal_id`, `provider` | — |
| `external_fetch_log` | 1 516 | `id` | — |
| `external_pmu_citations` | 65 654 | `id` | `idx_ext_cit_upd`, `idx_ext_cit_race` |
| `external_pmu_results` | 5 424 | `date_race`, `reunion`, `course`, `type_pari` | — |
| `feature_version` | 0 | `version_id` | — |
| `market_race_meta` | 712 | `race_id` | — |
| `market_runner_features` | 15 847 | `runner_id` | `idx_mrf_split`, `idx_mrf_race` |
| `master_hippodrome` | 104 | `hippodrome_id` | — |
| `master_horse` | 10 372 | `horse_id` | `idx_horse_namekey` |
| `master_person` | 13 068 | `person_id` | `idx_person_role_key` |
| `master_race` | 1 424 | `race_id` | `idx_race_hippo`, `idx_race_date` |
| `master_runner` | 18 879 | `runner_id` | `idx_runner_trainer`, `idx_runner_jockey`, `idx_runner_horse`, `idx_runner_race` |
| `model_version` | 0 | `version_id` | — |
| `phase3_leakage_audit` | 5 | `check_name` | — |
| `prediction_snapshot` | 0 | `snapshot_id` | — |
| `ref_discipline` | 4 | `discipline_raw` | — |
| `ref_hippodrome` | 86 | `label_variant` | — |

### 2.2 Colonnes

**`comment_features`** — 10 116 lignes

| Colonne | Type | NOT NULL | PK | Taux de nullité | Distinct | Exemples |
|---|---|---|---|---:|---:|---|
| `runner_id` | TEXT | non | oui | 0.0 % | 10 116 | `0000634f-26be-5643-a4d4-6d1620ff6909`, `0000d280-19bd-5bed-9bc7-fdf1257ae616`, `00025f98-188c-5a4e-8c97-acaf61ef6749` |
| `race_id` | TEXT | oui | non | 0.0 % | 712 | `0105467f-fd91-517f-87c9-58e4b3bb4256`, `01837dc5-645d-57bc-a5b3-df2fd807793e`, `01aa2782-79c0-530e-b751-dc7c5cdc539b` |
| `has_comment` | INTEGER | oui | non | 0.0 % | 2 | `1`, `0` |
| `cm_len` | INTEGER | non | non | 3.8 % | 554 | `360`, `265`, `303` |
| `cm_len_log` | REAL | non | non | 3.8 % | 554 | `5.8888779583328805`, `5.583496308781699`, `5.717027701406222` |
| `cm_pos` | INTEGER | non | non | 3.8 % | 9 | `0`, `2`, `1` |
| `cm_neg` | INTEGER | non | non | 3.8 % | 5 | `2`, `0`, `1` |
| `cm_sentiment` | REAL | non | non | 3.8 % | 25 | `-0.6666666666666666`, `0.6666666666666666`, `0.0` |
| `cm_has_favori` | INTEGER | non | non | 3.8 % | 2 | `0`, `1` |

**`data_version`** — 2 lignes

| Colonne | Type | NOT NULL | PK | Taux de nullité | Distinct | Exemples |
|---|---|---|---|---:|---:|---|
| `version_id` | INTEGER | non | oui | 0.0 % | 2 | `1`, `2` |
| `scope` | TEXT | oui | non | 0.0 % | 2 | `socle_lonab`, `master_db` |
| `version` | TEXT | oui | non | 0.0 % | 2 | `phase2-derived`, `v1` |
| `source_sha256` | TEXT | non | non | 50.0 % | 1 | `d71f6a013ff7fc5720ffd5824d0c71077cba1602c883073b` |
| `created_at` | TEXT | oui | non | 0.0 % | 1 | `2026-09-13T19:25:57.744581+00:00` |
| `notes` | TEXT | non | non | 0.0 % | 2 | `Master DB dérivée du socle LONAB en lecture seul`, `fichier: pmu_master.db` |

**`external_entity_mapping`** — 0 lignes

| Colonne | Type | NOT NULL | PK | Taux de nullité | Distinct | Exemples |
|---|---|---|---|---:|---:|---|
| `internal_id` | TEXT | oui | oui | — | 0 | — |
| `internal_type` | TEXT | oui | non | — | 0 | — |
| `provider` | TEXT | oui | oui | — | 0 | — |
| `external_id` | TEXT | non | non | — | 0 | — |
| `confidence` | REAL | non | non | — | 0 | — |
| `verified` | INTEGER | oui | non | — | 0 | — |
| `created_at` | TEXT | non | non | — | 0 | — |

**`external_fetch_log`** — 1 516 lignes

| Colonne | Type | NOT NULL | PK | Taux de nullité | Distinct | Exemples |
|---|---|---|---|---:|---:|---|
| `id` | INTEGER | non | oui | 0.0 % | 1 516 | `1`, `2`, `3` |
| `ts` | TEXT | non | non | 0.0 % | 1 359 | `2026-09-14 07:33:47`, `2026-09-14 07:33:51`, `2026-09-14 07:33:55` |
| `endpoint` | TEXT | non | non | 0.0 % | 2 | `citations`, `rapports-definitifs` |
| `date_race` | TEXT | non | non | 0.0 % | 32 | `2024-02-09`, `2024-01-19`, `2024-04-30` |
| `reunion` | INTEGER | non | non | 0.5 % | 4 | `1`, `2`, `3` |
| `course` | INTEGER | non | non | 0.5 % | 10 | `1`, `2`, `3` |
| `status` | TEXT | non | non | 0.0 % | 2 | `ERREUR`, `OK` |
| `detail` | TEXT | non | non | 0.0 % | 33 | `HTTP 400`, `91 lignes`, `7 types` |

**`external_pmu_citations`** — 65 654 lignes

| Colonne | Type | NOT NULL | PK | Taux de nullité | Distinct | Exemples |
|---|---|---|---|---:|---:|---|
| `id` | INTEGER | non | oui | 0.0 % | 65 654 | `1130`, `1131`, `1132` |
| `fetched_at` | TEXT | oui | non | 0.0 % | 761 | `2026-09-14 07:35:30`, `2026-09-14 07:35:32`, `2026-09-14 07:35:34` |
| `date_race` | TEXT | oui | non | 0.0 % | 32 | `2024-01-19`, `2024-02-09`, `2024-03-08` |
| `reunion` | INTEGER | oui | non | 0.0 % | 4 | `1`, `2`, `3` |
| `course` | INTEGER | oui | non | 0.0 % | 10 | `1`, `2`, `3` |
| `type_pari` | TEXT | oui | non | 0.0 % | 15 | `E_COUPLE_GAGNANT`, `E_COUPLE_PLACE`, `E_DEUX_SUR_QUATRE` |
| `api_updatetime` | INTEGER | non | non | 0.0 % | 1 939 | `1705660796000`, `1705661876000`, `1705663051000` |
| `numero` | INTEGER | oui | non | 0.0 % | 18 | `1`, `2`, `3` |
| `nom` | TEXT | non | non | 0.0 % | 7 547 | `KUMBI DE PHYT'S`, `KRONOS DU GITE`, `JIPSY ROYALE` |
| `statut` | TEXT | non | non | 0.0 % | 2 | `PARTANT`, `NON_PARTANT` |
| `enjeu` | REAL | non | non | 0.0 % | 23 052 | `16500.0`, `81900.0`, `40100.0` |
| `ratio` | REAL | non | non | 0.0 % | 3 906 | `0.74`, `3.68`, `1.8` |

**`external_pmu_results`** — 5 424 lignes

| Colonne | Type | NOT NULL | PK | Taux de nullité | Distinct | Exemples |
|---|---|---|---|---:|---:|---|
| `date_race` | TEXT | oui | oui | 0.0 % | 32 | `2024-01-19`, `2024-02-09`, `2024-03-08` |
| `reunion` | INTEGER | oui | oui | 0.0 % | 7 | `1`, `2`, `3` |
| `course` | INTEGER | oui | oui | 0.0 % | 11 | `1`, `2`, `3` |
| `fetched_at` | TEXT | non | non | 0.0 % | 794 | `2026-09-14 07:35:30`, `2026-09-14 07:35:32`, `2026-09-14 07:35:34` |
| `arrivee` | TEXT | non | non | 0.0 % | 1 | `null` |
| `type_pari` | TEXT | non | oui | 0.0 % | 15 | `E_COUPLE_GAGNANT`, `E_COUPLE_PLACE`, `E_DEUX_SUR_QUATRE` |
| `nb_gagnants` | REAL | non | non | 100.0 % | 0 | — |
| `masse_partager` | REAL | non | non | 100.0 % | 0 | — |
| `data_json` | TEXT | non | non | 0.0 % | 5 382 | `{"typePari": "E_SIMPLE_GAGNANT", "miseBase": 100`, `{"typePari": "E_SIMPLE_PLACE", "miseBase": 100, `, `{"typePari": "E_COUPLE_GAGNANT", "miseBase": 100` |

**`feature_version`** — 0 lignes

| Colonne | Type | NOT NULL | PK | Taux de nullité | Distinct | Exemples |
|---|---|---|---|---:|---:|---|
| `version_id` | INTEGER | non | oui | — | 0 | — |
| `scope` | TEXT | oui | non | — | 0 | — |
| `version` | TEXT | oui | non | — | 0 | — |
| `created_at` | TEXT | oui | non | — | 0 | — |
| `notes` | TEXT | non | non | — | 0 | — |

**`market_race_meta`** — 712 lignes

| Colonne | Type | NOT NULL | PK | Taux de nullité | Distinct | Exemples |
|---|---|---|---|---:|---:|---|
| `race_id` | TEXT | non | oui | 0.0 % | 712 | `0105467f-fd91-517f-87c9-58e4b3bb4256`, `01837dc5-645d-57bc-a5b3-df2fd807793e`, `01aa2782-79c0-530e-b751-dc7c5cdc539b` |
| `date` | TEXT | non | non | 0.0 % | 705 | `2024-02-09`, `2024-02-10`, `2024-02-11` |
| `split` | TEXT | oui | non | 0.0 % | 3 | `train`, `val`, `test` |
| `n_runners` | INTEGER | oui | non | 0.0 % | 7 | `13`, `15`, `14` |
| `n_with_odds` | INTEGER | oui | non | 0.0 % | 7 | `13`, `15`, `14` |

**`market_runner_features`** — 15 847 lignes

| Colonne | Type | NOT NULL | PK | Taux de nullité | Distinct | Exemples |
|---|---|---|---|---:|---:|---|
| `runner_id` | TEXT | non | oui | 0.0 % | 15 847 | `0000634f-26be-5643-a4d4-6d1620ff6909`, `0000d280-19bd-5bed-9bc7-fdf1257ae616`, `00025f98-188c-5a4e-8c97-acaf61ef6749` |
| `race_id` | TEXT | oui | non | 0.0 % | 1 208 | `003816d4-6e3f-5731-b02c-7c0c0578a73d`, `0057ea67-00a0-5136-82a4-0c9c565e101a`, `0105467f-fd91-517f-87c9-58e4b3bb4256` |
| `date` | TEXT | non | non | 0.2 % | 713 | `2024-02-09`, `2024-02-10`, `2024-02-11` |
| `split` | TEXT | oui | non | 0.0 % | 5 | `api_pmu`, `inference`, `test` |
| `m_implied` | REAL | non | non | 1.3 % | 399 | `0.0625`, `0.3333333333333333`, `0.058823529411764705` |
| `m_prob_norm` | REAL | non | non | 1.1 % | 13 058 | `0.04498039347446274`, `0.23989543186380127`, `0.04233448797596493` |
| `m_rank` | INTEGER | non | non | 1.1 % | 26 | `7`, `1`, `8` |
| `m_log_odds` | REAL | non | non | 1.3 % | 415 | `2.772588722239781`, `1.0986122886681098`, `2.833213344056216` |
| `m_rel_median` | REAL | non | non | 1.3 % | 3 069 | `1.0`, `0.1875`, `1.0625` |
| `m_is_fav` | INTEGER | non | non | 0.2 % | 2 | `0`, `1` |
| `f_musique_n` | INTEGER | non | non | 0.2 % | 11 | `4`, `5`, `3` |
| `f_musique_avg` | REAL | non | non | 3.4 % | 225 | `3.0`, `4.0`, `6.0` |
| `f_musique_best` | REAL | non | non | 3.4 % | 10 | `1.0`, `4.0`, `2.0` |
| `f_musique_winrate` | REAL | non | non | 0.2 % | 30 | `0.5`, `0.6`, `0.0` |
| `f_musique_top3rate` | REAL | non | non | 0.2 % | 35 | `0.75`, `0.6`, `0.0` |
| `f_gains_log` | REAL | non | non | 0.2 % | 12 513 | `12.231004253949012`, `12.483651350419267`, `12.498454904777747` |
| `f_age` | INTEGER | non | non | 0.0 % | 14 | `7`, `9`, `8` |
| `f_sex` | INTEGER | non | non | 0.2 % | 4 | `1`, `-1`, `0` |
| `f_field_size` | INTEGER | non | non | 0.2 % | 19 | `13`, `15`, `14` |
| `c_horse_starts` | INTEGER | non | non | 0.2 % | 25 | `0`, `1`, `2` |
| `c_horse_winrate` | REAL | non | non | 0.2 % | 31 | `0.0`, `1.0`, `0.5` |
| `c_horse_top3rate` | REAL | non | non | 0.2 % | 49 | `0.0`, `1.0`, `0.5` |
| `c_jockey_winrate` | REAL | non | non | 0.2 % | 1 299 | `0.0`, `0.3333333333333333`, `0.2` |
| `c_trainer_winrate` | REAL | non | non | 0.2 % | 501 | `0.0`, `1.0`, `0.25` |
| `label_win` | INTEGER | non | non | 0.2 % | 2 | `0`, `1` |
| `label_top3` | INTEGER | non | non | 0.2 % | 2 | `1`, `0` |

**`master_hippodrome`** — 104 lignes

| Colonne | Type | NOT NULL | PK | Taux de nullité | Distinct | Exemples |
|---|---|---|---|---:|---:|---|
| `hippodrome_id` | TEXT | non | oui | 0.0 % | 104 | `00aef98f-8ea0-47ef-9bb0-e563ef9ea8d2`, `02475693-5203-54eb-9c96-68ad47dfe505`, `05411480-7a57-4334-af95-b6ab0412ed11` |
| `label_canonical` | TEXT | oui | non | 0.0 % | 104 | `AGEN LA GARENNE`, `ANGERS`, `ANGERS EVENTARD` |
| `label_variants` | TEXT | non | non | 0.0 % | 103 | `AGEN LA GARENNE`, `ANGERS`, `ANGERS EVENTARD` |
| `country` | TEXT | non | non | 0.0 % | 1 | `FR` |
| `is_valid` | INTEGER | oui | non | 0.0 % | 1 | `1` |
| `quality_flag` | TEXT | oui | non | 0.0 % | 1 | `ok` |
| `n_courses` | INTEGER | oui | non | 0.0 % | 25 | `3`, `6`, `2` |

**`master_horse`** — 10 372 lignes

| Colonne | Type | NOT NULL | PK | Taux de nullité | Distinct | Exemples |
|---|---|---|---|---:|---:|---|
| `horse_id` | TEXT | non | oui | 0.0 % | 10 372 | `000b903b-4cb8-467e-a920-f118bd23228b`, `000bbb95-1b36-5ec3-aaef-9c5f00335b13`, `003478e9-f522-4a51-be98-c1f73382d0f8` |
| `name_normalized` | TEXT | oui | non | 0.0 % | 10 027 | `1 - C. ESCUDER`, `1 - M. SEROR`, `1 – R. DERIEUX` |
| `name_key` | TEXT | oui | non | 0.0 % | 10 372 | `1 C ESCUDER`, `1 M SEROR`, `1 R DERIEUX` |
| `resolution_method` | TEXT | oui | non | 0.0 % | 5 | `exact_name+sex_age`, `exact_name`, `name+pedigree` |
| `resolution_confidence` | REAL | oui | non | 0.0 % | 4 | `0.9`, `0.7`, `0.6` |
| `homonym_risk` | TEXT | oui | non | 0.0 % | 6 | `consistent_signal`, `no_signal`, `suspected_homonym` |
| `n_sex_birthyear_variants` | INTEGER | non | non | 0.1 % | 5 | `1`, `0`, `2` |
| `sex_birthyear_variants` | TEXT | non | non | 0.1 % | 197 | `H~2016`, ``, `F~2018 | H~2016` |
| `n_starts` | INTEGER | oui | non | 0.0 % | 24 | `1`, `2`, `5` |
| `first_seen_date` | TEXT | non | non | 0.1 % | 666 | `2026-01-30`, `2026-04-02`, `2026-02-03` |
| `last_seen_date` | TEXT | non | non | 0.1 % | 730 | `2026-01-30`, `2026-04-06`, `2026-03-18` |
| `pedigree_pere` | TEXT | non | non | 44.6 % | 1 459 | `RIO DE LA PLATA`, `BOLD EAGLE`, `RECOLETOS` |
| `pedigree_mere` | TEXT | non | non | 44.6 % | 5 452 | `ANCIENT EAST`, `WILL OF A WOMAN`, `TIA KIA` |
| `robe` | TEXT | non | non | 44.6 % | 21 | `BAI F.`, `BAI`, `ALEZAN` |
| `race` | TEXT | non | non | 44.6 % | 7 | `PUR-SANG`, `TROTTEUR ETRANGER`, `TROTTEUR FRANCAIS` |

**`master_person`** — 13 068 lignes

| Colonne | Type | NOT NULL | PK | Taux de nullité | Distinct | Exemples |
|---|---|---|---|---:|---:|---|
| `person_id` | TEXT | non | oui | 0.0 % | 13 068 | `000382ca-816e-42c0-bbf6-69abc357e027`, `000c8a52-09ef-40a9-8721-c462d687eec7`, `000ca919-b098-4c1c-a479-cb38d00d584b` |
| `name_normalized` | TEXT | oui | non | 0.0 % | 11 596 | `7 - N. GEORGE & A. ZETTERHOLM`, `A.A. CHAVATTE`, `A. ABRIVARD` |
| `name_key` | TEXT | oui | non | 0.0 % | 11 656 | `7 N GEORGE A ZETTERHOLM`, `A A CHAVATTE`, `A ABRIVARD` |
| `role` | TEXT | oui | non | 0.0 % | 6 | `JOCKEY`, `OWNER`, `TRAINER` |
| `resolution_method` | TEXT | oui | non | 0.0 % | 3 | `exact_name`, `EXACT`, `api_pmu` |
| `resolution_confidence` | REAL | oui | non | 0.0 % | 1 | `1.0` |
| `n_appearances` | INTEGER | oui | non | 0.0 % | 159 | `3`, `8`, `205` |

**`master_race`** — 1 424 lignes

| Colonne | Type | NOT NULL | PK | Taux de nullité | Distinct | Exemples |
|---|---|---|---|---:|---:|---|
| `race_id` | TEXT | non | oui | 0.0 % | 1 424 | `001ab63d-80ca-52e8-8140-4e558d197284`, `003816d4-6e3f-5731-b02c-7c0c0578a73d`, `0057ea67-00a0-5136-82a4-0c9c565e101a` |
| `source_document_id` | INTEGER | oui | non | 0.0 % | 931 | `1`, `2`, `3` |
| `date` | TEXT | non | non | 0.0 % | 742 | `1995-07-18`, `2024-01-19`, `2024-01-20` |
| `date_is_sentinel` | INTEGER | oui | non | 0.0 % | 2 | `0`, `1` |
| `hippodrome_id` | TEXT | non | non | 21.0 % | 104 | `00aef98f-8ea0-47ef-9bb0-e563ef9ea8d2`, `02475693-5203-54eb-9c96-68ad47dfe505`, `05411480-7a57-4334-af95-b6ab0412ed11` |
| `hippodrome_label_raw` | TEXT | non | non | 0.0 % | 132 | `DEAUVILLE NOCTURNE`, `PARIS-VINCENNES`, `11` |
| `discipline` | TEXT | non | non | 50.4 % | 8 | `PLAT`, `ATTELE`, `OBSTACLE` |
| `discipline_status` | TEXT | oui | non | 0.0 % | 4 | `present`, `missing`, `OK` |
| `distance_m` | INTEGER | non | non | 0.1 % | 100 | `1300`, `25`, `3400` |
| `montant_euros` | INTEGER | non | non | 0.4 % | 296 | `53000`, `4500`, `58000` |
| `partants_declares` | INTEGER | non | non | 0.1 % | 21 | `16`, `15`, `18` |
| `partants_effectifs` | INTEGER | non | non | 0.1 % | 20 | `15`, `14`, `13` |
| `type_course` | TEXT | non | non | 0.1 % | 7 | `HANDICAP`, ``, `AUTOSTART` |
| `titre` | TEXT | non | non | 0.0 % | 1 230 | `DEAUVILLE NOCTURNE - PRIX DU VOLCAN - PLAT`, `PARIS-VINCENNES - PRIX DE BREST - ATTELE`, `11 - FIFTY FIVE BOND : Excellent troisième du Pr` |
| `n_partants_source` | INTEGER | oui | non | 0.0 % | 20 | `15`, `14`, `13` |
| `n_runners_linked` | INTEGER | oui | non | 0.0 % | 20 | `15`, `14`, `13` |
| `result_status` | TEXT | oui | non | 0.0 % | 5 | `no_arrival_for_date`, `sentinel_date`, `arrival_available` |
| `is_lonab` | INTEGER | non | non | 0.0 % | 2 | `0`, `1` |
| `lonab_bet` | TEXT | non | non | 98.7 % | 2 | `Quinté+ / Quarté+ / Tiercé`, `Quarté+` |
| `arrivee_officielle` | TEXT | non | non | 98.9 % | 16 | `14-3-5-6-12`, `7-5-8-14`, `3-9-13-2-5` |
| `reunion_num` | INTEGER | non | non | 65.3 % | 13 | `1`, `2`, `3` |
| `course_num` | INTEGER | non | non | 65.3 % | 11 | `1`, `2`, `3` |
| `heure_depart` | TEXT | non | non | 65.3 % | 273 | `13:55`, `14:36`, `15:09` |
| `quinte_dividende` | REAL | non | non | 99.5 % | 7 | `814760.0`, `1777840.0`, `118700.0` |
| `nb_gagnants_quinte` | REAL | non | non | 99.5 % | 7 | `7.84`, `8.0`, `139.6` |
| `lonab_journal_bet` | TEXT | non | non | 99.4 % | 3 | `4+1`, `QUARTE`, `TIERCE` |
| `lonab_journal_venue` | TEXT | non | non | 99.4 % | 8 | `ANGERS - GRAND NATIONAL DU TROT (9ème Etape du G`, `PARISLONGCHAMP - PRIX CARRUS`, `PARIS-VINCENNES NOCTURNE - PRIX ALGORAH` |
| `lonab_source_url` | TEXT | non | non | 99.4 % | 8 | `https://lonab.bf/sites/default/files/2026-09/JH_`, `https://lonab.bf/sites/default/files/2026-09/JH_`, `https://lonab.bf/sites/default/files/2026-09/JH_` |
| `meteo_temperature` | INTEGER | non | non | 65.3 % | 25 | `21`, `18`, `19` |
| `meteo_nebulosite` | TEXT | non | non | 65.3 % | 15 | `Peu nuageux`, `Très nuageux`, `Nuages et soleil` |
| `meteo_vent_force` | INTEGER | non | non | 65.3 % | 22 | `11`, `18`, `14` |
| `meteo_vent_direction` | TEXT | non | non | 65.3 % | 8 | `NO`, `SO`, `O` |

**`master_runner`** — 18 879 lignes

| Colonne | Type | NOT NULL | PK | Taux de nullité | Distinct | Exemples |
|---|---|---|---|---:|---:|---|
| `runner_id` | TEXT | non | oui | 0.0 % | 18 879 | `0000634f-26be-5643-a4d4-6d1620ff6909`, `0000d280-19bd-5bed-9bc7-fdf1257ae616`, `00025f98-188c-5a4e-8c97-acaf61ef6749` |
| `race_id` | TEXT | oui | non | 0.0 % | 1 419 | `001ab63d-80ca-52e8-8140-4e558d197284`, `003816d4-6e3f-5731-b02c-7c0c0578a73d`, `0057ea67-00a0-5136-82a4-0c9c565e101a` |
| `source_document_id` | INTEGER | oui | non | 0.0 % | 926 | `1`, `2`, `3` |
| `source_partant_id` | INTEGER | oui | non | 0.0 % | 13 179 | `1`, `2`, `3` |
| `numero` | INTEGER | non | non | 0.0 % | 26 | `1`, `2`, `3` |
| `horse_id` | TEXT | non | non | 0.0 % | 10 372 | `000b903b-4cb8-467e-a920-f118bd23228b`, `000bbb95-1b36-5ec3-aaef-9c5f00335b13`, `003478e9-f522-4a51-be98-c1f73382d0f8` |
| `jockey_id` | TEXT | non | non | 0.2 % | 2 385 | `00185bb9-eb82-52e2-8020-af1e414144c1`, `004d1393-b5ba-59d2-b4ed-74a618b438c8`, `0052f53c-4a5a-4b60-a85b-64298b46dd82` |
| `trainer_id` | TEXT | non | non | 0.5 % | 3 233 | `000ca919-b098-4c1c-a479-cb38d00d584b`, `00276e53-18fb-553b-b58f-d28b99bb64e0`, `003e55a4-9196-5a95-8360-07ffac68d9c3` |
| `owner_id` | TEXT | non | non | 4.5 % | 7 452 | `0496f548-cb12-5206-99cd-354ae23fe4c7`, `22776201-a47d-53be-921f-93c42b7c113e`, `2ed87667-9979-54ba-b0ae-de67ab83b195` |
| `cote_decimale` | REAL | non | non | 12.9 % | 290 | `35.0`, `39.0`, `26.0` |
| `gains_euros` | INTEGER | non | non | 4.8 % | 14 075 | `146785`, `115245`, `153110` |
| `performances_structured` | TEXT | non | non | 1.1 % | 16 365 | `[2, 2, 9, 5, 4]`, `[0, 0, 1, 7, 1]`, `[5, 9, 1, 3, 6]` |
| `sexe_raw` | TEXT | non | non | 0.1 % | 228 | `M.7`, `F.7`, `H.5` |
| `age_raw` | TEXT | non | non | 0.0 % | 14 | `7`, `5`, `4` |
| `poids_raw` | TEXT | non | non | 30.3 % | 1 | `` |
| `corde_raw` | TEXT | non | non | 30.3 % | 1 | `` |
| `result_position` | INTEGER | non | non | 59.7 % | 24 | `3`, `2`, `4` |
| `result_status` | TEXT | oui | non | 0.0 % | 7 | `no_arrival_for_date`, `sentinel_date`, `arrived` |

**`model_version`** — 0 lignes

| Colonne | Type | NOT NULL | PK | Taux de nullité | Distinct | Exemples |
|---|---|---|---|---:|---:|---|
| `version_id` | INTEGER | non | oui | — | 0 | — |
| `scope` | TEXT | oui | non | — | 0 | — |
| `version` | TEXT | oui | non | — | 0 | — |
| `created_at` | TEXT | oui | non | — | 0 | — |
| `notes` | TEXT | non | non | — | 0 | — |

**`phase3_leakage_audit`** — 5 lignes

| Colonne | Type | NOT NULL | PK | Taux de nullité | Distinct | Exemples |
|---|---|---|---|---:|---:|---|
| `check_name` | TEXT | non | oui | 0.0 % | 5 | `aucune_colonne_cible`, `cumul_strictement_anterieur`, `marche_coherent` |
| `result` | TEXT | oui | non | 0.0 % | 1 | `PASS` |
| `detail` | TEXT | non | non | 0.0 % | 5 | `train≤2025-11-05 < val≤2026-04-01 < test≤2026-09`, `0 lignes avec cote mais sans probabilité`, `0 courses dont la somme ≠ 1` |

**`prediction_snapshot`** — 0 lignes

| Colonne | Type | NOT NULL | PK | Taux de nullité | Distinct | Exemples |
|---|---|---|---|---:|---:|---|
| `snapshot_id` | INTEGER | non | oui | — | 0 | — |
| `race_id` | TEXT | non | non | — | 0 | — |
| `model_version` | TEXT | non | non | — | 0 | — |
| `cutoff_ts` | TEXT | non | non | — | 0 | — |
| `payload_json` | TEXT | non | non | — | 0 | — |
| `created_at` | TEXT | oui | non | — | 0 | — |

**`ref_discipline`** — 4 lignes

| Colonne | Type | NOT NULL | PK | Taux de nullité | Distinct | Exemples |
|---|---|---|---|---:|---:|---|
| `discipline_raw` | TEXT | non | oui | 0.0 % | 4 | ``, `ATTELE`, `OBSTACLE` |
| `discipline_norm` | TEXT | non | non | 25.0 % | 3 | `ATTELE`, `OBSTACLE`, `PLAT` |
| `status` | TEXT | oui | non | 0.0 % | 2 | `missing`, `present` |

**`ref_hippodrome`** — 86 lignes

| Colonne | Type | NOT NULL | PK | Taux de nullité | Distinct | Exemples |
|---|---|---|---|---:|---:|---|
| `label_variant` | TEXT | non | oui | 0.0 % | 86 | ``, `1`, `10` |
| `hippodrome_id` | TEXT | non | non | 23.3 % | 59 | `3f919aab-8053-5cb3-9337-fa0148065e9c`, `64f06856-9821-5c2e-869b-dec83dd089d6`, `ff09562f-4cdf-5561-a8d3-2ff7d5c3980f` |
| `quality_flag` | TEXT | oui | non | 0.0 % | 3 | `missing`, `numeric_parse_error`, `ok` |

### 2.3 Relations

| Source | Colonne | Cible | Origine |
|---|---|---|---|
| `comment_features` | `race_id` | `master_race` | inférée (nommage) |
| `comment_features` | `runner_id` | `master_runner` | déclarée (FOREIGN KEY) |
| `market_race_meta` | `race_id` | `master_race` | inférée (nommage) |
| `market_runner_features` | `race_id` | `master_race` | inférée (nommage) |
| `market_runner_features` | `runner_id` | `master_runner` | déclarée (FOREIGN KEY) |
| `master_race` | `hippodrome_id` | `master_hippodrome` | déclarée (FOREIGN KEY) |
| `master_runner` | `horse_id` | `master_horse` | déclarée (FOREIGN KEY) |
| `master_runner` | `race_id` | `master_race` | déclarée (FOREIGN KEY) |
| `prediction_snapshot` | `race_id` | `master_race` | inférée (nommage) |
| `ref_hippodrome` | `hippodrome_id` | `master_hippodrome` | inférée (nommage) |

## 2. Base `pmu-lonab-scraper/data/backups/pmu_master_before_lonab_20260916_0358.db`

- Taille : **39.1 Mo**
- SHA-256 : `af8de3f0974564284a0cdd146286df3bc15924d8e9a524036b9c8352eeedf7b1`
- Vues : aucune

### 2.1 Tables et volumes

| Table | Lignes | Clé primaire | Index |
|---|---:|---|---|
| `comment_features` | 10 116 | `runner_id` | `idx_cf_race` |
| `data_version` | 2 | `version_id` | — |
| `external_entity_mapping` | 0 | `internal_id`, `provider` | — |
| `external_fetch_log` | 1 516 | `id` | — |
| `external_pmu_citations` | 65 654 | `id` | `idx_ext_cit_upd`, `idx_ext_cit_race` |
| `external_pmu_results` | 5 424 | `date_race`, `reunion`, `course`, `type_pari` | — |
| `feature_version` | 0 | `version_id` | — |
| `market_race_meta` | 712 | `race_id` | — |
| `market_runner_features` | 15 143 | `runner_id` | `idx_mrf_split`, `idx_mrf_race` |
| `master_hippodrome` | 98 | `hippodrome_id` | — |
| `master_horse` | 9 700 | `horse_id` | `idx_horse_namekey` |
| `master_person` | 12 266 | `person_id` | `idx_person_role_key` |
| `master_race` | 1 369 | `race_id` | `idx_race_hippo`, `idx_race_date` |
| `master_runner` | 18 282 | `runner_id` | `idx_runner_trainer`, `idx_runner_jockey`, `idx_runner_horse`, `idx_runner_race` |
| `model_version` | 0 | `version_id` | — |
| `phase3_leakage_audit` | 5 | `check_name` | — |
| `prediction_snapshot` | 0 | `snapshot_id` | — |
| `ref_discipline` | 4 | `discipline_raw` | — |
| `ref_hippodrome` | 86 | `label_variant` | — |

### 2.2 Colonnes

**`comment_features`** — 10 116 lignes

| Colonne | Type | NOT NULL | PK | Taux de nullité | Distinct | Exemples |
|---|---|---|---|---:|---:|---|
| `runner_id` | TEXT | non | oui | 0.0 % | 10 116 | `0000634f-26be-5643-a4d4-6d1620ff6909`, `0000d280-19bd-5bed-9bc7-fdf1257ae616`, `00025f98-188c-5a4e-8c97-acaf61ef6749` |
| `race_id` | TEXT | oui | non | 0.0 % | 712 | `0105467f-fd91-517f-87c9-58e4b3bb4256`, `01837dc5-645d-57bc-a5b3-df2fd807793e`, `01aa2782-79c0-530e-b751-dc7c5cdc539b` |
| `has_comment` | INTEGER | oui | non | 0.0 % | 2 | `1`, `0` |
| `cm_len` | INTEGER | non | non | 3.8 % | 554 | `360`, `265`, `303` |
| `cm_len_log` | REAL | non | non | 3.8 % | 554 | `5.8888779583328805`, `5.583496308781699`, `5.717027701406222` |
| `cm_pos` | INTEGER | non | non | 3.8 % | 9 | `0`, `2`, `1` |
| `cm_neg` | INTEGER | non | non | 3.8 % | 5 | `2`, `0`, `1` |
| `cm_sentiment` | REAL | non | non | 3.8 % | 25 | `-0.6666666666666666`, `0.6666666666666666`, `0.0` |
| `cm_has_favori` | INTEGER | non | non | 3.8 % | 2 | `0`, `1` |

**`data_version`** — 2 lignes

| Colonne | Type | NOT NULL | PK | Taux de nullité | Distinct | Exemples |
|---|---|---|---|---:|---:|---|
| `version_id` | INTEGER | non | oui | 0.0 % | 2 | `1`, `2` |
| `scope` | TEXT | oui | non | 0.0 % | 2 | `socle_lonab`, `master_db` |
| `version` | TEXT | oui | non | 0.0 % | 2 | `phase2-derived`, `v1` |
| `source_sha256` | TEXT | non | non | 50.0 % | 1 | `d71f6a013ff7fc5720ffd5824d0c71077cba1602c883073b` |
| `created_at` | TEXT | oui | non | 0.0 % | 1 | `2026-09-13T19:25:57.744581+00:00` |
| `notes` | TEXT | non | non | 0.0 % | 2 | `Master DB dérivée du socle LONAB en lecture seul`, `fichier: pmu_master.db` |

**`external_entity_mapping`** — 0 lignes

| Colonne | Type | NOT NULL | PK | Taux de nullité | Distinct | Exemples |
|---|---|---|---|---:|---:|---|
| `internal_id` | TEXT | oui | oui | — | 0 | — |
| `internal_type` | TEXT | oui | non | — | 0 | — |
| `provider` | TEXT | oui | oui | — | 0 | — |
| `external_id` | TEXT | non | non | — | 0 | — |
| `confidence` | REAL | non | non | — | 0 | — |
| `verified` | INTEGER | oui | non | — | 0 | — |
| `created_at` | TEXT | non | non | — | 0 | — |

**`external_fetch_log`** — 1 516 lignes

| Colonne | Type | NOT NULL | PK | Taux de nullité | Distinct | Exemples |
|---|---|---|---|---:|---:|---|
| `id` | INTEGER | non | oui | 0.0 % | 1 516 | `1`, `2`, `3` |
| `ts` | TEXT | non | non | 0.0 % | 1 359 | `2026-09-14 07:33:47`, `2026-09-14 07:33:51`, `2026-09-14 07:33:55` |
| `endpoint` | TEXT | non | non | 0.0 % | 2 | `citations`, `rapports-definitifs` |
| `date_race` | TEXT | non | non | 0.0 % | 32 | `2024-02-09`, `2024-01-19`, `2024-04-30` |
| `reunion` | INTEGER | non | non | 0.5 % | 4 | `1`, `2`, `3` |
| `course` | INTEGER | non | non | 0.5 % | 10 | `1`, `2`, `3` |
| `status` | TEXT | non | non | 0.0 % | 2 | `ERREUR`, `OK` |
| `detail` | TEXT | non | non | 0.0 % | 33 | `HTTP 400`, `91 lignes`, `7 types` |

**`external_pmu_citations`** — 65 654 lignes

| Colonne | Type | NOT NULL | PK | Taux de nullité | Distinct | Exemples |
|---|---|---|---|---:|---:|---|
| `id` | INTEGER | non | oui | 0.0 % | 65 654 | `1130`, `1131`, `1132` |
| `fetched_at` | TEXT | oui | non | 0.0 % | 761 | `2026-09-14 07:35:30`, `2026-09-14 07:35:32`, `2026-09-14 07:35:34` |
| `date_race` | TEXT | oui | non | 0.0 % | 32 | `2024-01-19`, `2024-02-09`, `2024-03-08` |
| `reunion` | INTEGER | oui | non | 0.0 % | 4 | `1`, `2`, `3` |
| `course` | INTEGER | oui | non | 0.0 % | 10 | `1`, `2`, `3` |
| `type_pari` | TEXT | oui | non | 0.0 % | 15 | `E_COUPLE_GAGNANT`, `E_COUPLE_PLACE`, `E_DEUX_SUR_QUATRE` |
| `api_updatetime` | INTEGER | non | non | 0.0 % | 1 939 | `1705660796000`, `1705661876000`, `1705663051000` |
| `numero` | INTEGER | oui | non | 0.0 % | 18 | `1`, `2`, `3` |
| `nom` | TEXT | non | non | 0.0 % | 7 547 | `KUMBI DE PHYT'S`, `KRONOS DU GITE`, `JIPSY ROYALE` |
| `statut` | TEXT | non | non | 0.0 % | 2 | `PARTANT`, `NON_PARTANT` |
| `enjeu` | REAL | non | non | 0.0 % | 23 052 | `16500.0`, `81900.0`, `40100.0` |
| `ratio` | REAL | non | non | 0.0 % | 3 906 | `0.74`, `3.68`, `1.8` |

**`external_pmu_results`** — 5 424 lignes

| Colonne | Type | NOT NULL | PK | Taux de nullité | Distinct | Exemples |
|---|---|---|---|---:|---:|---|
| `date_race` | TEXT | oui | oui | 0.0 % | 32 | `2024-01-19`, `2024-02-09`, `2024-03-08` |
| `reunion` | INTEGER | oui | oui | 0.0 % | 7 | `1`, `2`, `3` |
| `course` | INTEGER | oui | oui | 0.0 % | 11 | `1`, `2`, `3` |
| `fetched_at` | TEXT | non | non | 0.0 % | 794 | `2026-09-14 07:35:30`, `2026-09-14 07:35:32`, `2026-09-14 07:35:34` |
| `arrivee` | TEXT | non | non | 0.0 % | 1 | `null` |
| `type_pari` | TEXT | non | oui | 0.0 % | 15 | `E_COUPLE_GAGNANT`, `E_COUPLE_PLACE`, `E_DEUX_SUR_QUATRE` |
| `nb_gagnants` | REAL | non | non | 100.0 % | 0 | — |
| `masse_partager` | REAL | non | non | 100.0 % | 0 | — |
| `data_json` | TEXT | non | non | 0.0 % | 5 382 | `{"typePari": "E_SIMPLE_GAGNANT", "miseBase": 100`, `{"typePari": "E_SIMPLE_PLACE", "miseBase": 100, `, `{"typePari": "E_COUPLE_GAGNANT", "miseBase": 100` |

**`feature_version`** — 0 lignes

| Colonne | Type | NOT NULL | PK | Taux de nullité | Distinct | Exemples |
|---|---|---|---|---:|---:|---|
| `version_id` | INTEGER | non | oui | — | 0 | — |
| `scope` | TEXT | oui | non | — | 0 | — |
| `version` | TEXT | oui | non | — | 0 | — |
| `created_at` | TEXT | oui | non | — | 0 | — |
| `notes` | TEXT | non | non | — | 0 | — |

**`market_race_meta`** — 712 lignes

| Colonne | Type | NOT NULL | PK | Taux de nullité | Distinct | Exemples |
|---|---|---|---|---:|---:|---|
| `race_id` | TEXT | non | oui | 0.0 % | 712 | `0105467f-fd91-517f-87c9-58e4b3bb4256`, `01837dc5-645d-57bc-a5b3-df2fd807793e`, `01aa2782-79c0-530e-b751-dc7c5cdc539b` |
| `date` | TEXT | non | non | 0.0 % | 705 | `2024-02-09`, `2024-02-10`, `2024-02-11` |
| `split` | TEXT | oui | non | 0.0 % | 3 | `train`, `val`, `test` |
| `n_runners` | INTEGER | oui | non | 0.0 % | 7 | `13`, `15`, `14` |
| `n_with_odds` | INTEGER | oui | non | 0.0 % | 7 | `13`, `15`, `14` |

**`market_runner_features`** — 15 143 lignes

| Colonne | Type | NOT NULL | PK | Taux de nullité | Distinct | Exemples |
|---|---|---|---|---:|---:|---|
| `runner_id` | TEXT | non | oui | 0.0 % | 15 143 | `0000634f-26be-5643-a4d4-6d1620ff6909`, `0000d280-19bd-5bed-9bc7-fdf1257ae616`, `00025f98-188c-5a4e-8c97-acaf61ef6749` |
| `race_id` | TEXT | oui | non | 0.0 % | 1 145 | `0057ea67-00a0-5136-82a4-0c9c565e101a`, `0105467f-fd91-517f-87c9-58e4b3bb4256`, `015ed70c-a417-58d4-8234-74d13852a09c` |
| `date` | TEXT | non | non | 0.2 % | 712 | `2024-02-09`, `2024-02-10`, `2024-02-11` |
| `split` | TEXT | oui | non | 0.0 % | 5 | `api_pmu`, `inference`, `test` |
| `m_implied` | REAL | non | non | 1.4 % | 131 | `0.0625`, `0.3333333333333333`, `0.058823529411764705` |
| `m_prob_norm` | REAL | non | non | 1.2 % | 9 709 | `0.04498039347446274`, `0.23989543186380127`, `0.04233448797596493` |
| `m_rank` | INTEGER | non | non | 1.2 % | 26 | `7`, `1`, `8` |
| `m_log_odds` | REAL | non | non | 1.4 % | 131 | `2.772588722239781`, `1.0986122886681098`, `2.833213344056216` |
| `m_rel_median` | REAL | non | non | 1.4 % | 1 484 | `1.0`, `0.1875`, `1.0625` |
| `m_is_fav` | INTEGER | non | non | 0.2 % | 2 | `0`, `1` |
| `f_musique_n` | INTEGER | non | non | 0.2 % | 11 | `4`, `5`, `3` |
| `f_musique_avg` | REAL | non | non | 3.6 % | 225 | `3.0`, `4.0`, `6.0` |
| `f_musique_best` | REAL | non | non | 3.6 % | 10 | `1.0`, `4.0`, `2.0` |
| `f_musique_winrate` | REAL | non | non | 0.2 % | 30 | `0.5`, `0.6`, `0.0` |
| `f_musique_top3rate` | REAL | non | non | 0.2 % | 35 | `0.75`, `0.6`, `0.0` |
| `f_gains_log` | REAL | non | non | 0.2 % | 11 949 | `12.231004253949012`, `12.483651350419267`, `12.498454904777747` |
| `f_age` | INTEGER | non | non | 0.0 % | 14 | `7`, `9`, `8` |
| `f_sex` | INTEGER | non | non | 0.2 % | 4 | `1`, `-1`, `0` |
| `f_field_size` | INTEGER | non | non | 0.2 % | 19 | `13`, `15`, `14` |
| `c_horse_starts` | INTEGER | non | non | 0.2 % | 25 | `0`, `1`, `2` |
| `c_horse_winrate` | REAL | non | non | 0.2 % | 31 | `0.0`, `1.0`, `0.5` |
| `c_horse_top3rate` | REAL | non | non | 0.2 % | 49 | `0.0`, `1.0`, `0.5` |
| `c_jockey_winrate` | REAL | non | non | 0.2 % | 1 299 | `0.0`, `0.3333333333333333`, `0.2` |
| `c_trainer_winrate` | REAL | non | non | 0.2 % | 501 | `0.0`, `1.0`, `0.25` |
| `label_win` | INTEGER | non | non | 0.2 % | 2 | `0`, `1` |
| `label_top3` | INTEGER | non | non | 0.2 % | 2 | `1`, `0` |

**`master_hippodrome`** — 98 lignes

| Colonne | Type | NOT NULL | PK | Taux de nullité | Distinct | Exemples |
|---|---|---|---|---:|---:|---|
| `hippodrome_id` | TEXT | non | oui | 0.0 % | 98 | `00aef98f-8ea0-47ef-9bb0-e563ef9ea8d2`, `02475693-5203-54eb-9c96-68ad47dfe505`, `05411480-7a57-4334-af95-b6ab0412ed11` |
| `label_canonical` | TEXT | oui | non | 0.0 % | 98 | `AGEN LA GARENNE`, `ANGERS`, `ANGERS EVENTARD` |
| `label_variants` | TEXT | non | non | 0.0 % | 97 | `AGEN LA GARENNE`, `ANGERS`, `ANGERS EVENTARD` |
| `country` | TEXT | non | non | 0.0 % | 1 | `FR` |
| `is_valid` | INTEGER | oui | non | 0.0 % | 1 | `1` |
| `quality_flag` | TEXT | oui | non | 0.0 % | 1 | `ok` |
| `n_courses` | INTEGER | oui | non | 0.0 % | 23 | `3`, `2`, `27` |

**`master_horse`** — 9 700 lignes

| Colonne | Type | NOT NULL | PK | Taux de nullité | Distinct | Exemples |
|---|---|---|---|---:|---:|---|
| `horse_id` | TEXT | non | oui | 0.0 % | 9 700 | `000bbb95-1b36-5ec3-aaef-9c5f00335b13`, `0036e82d-1c11-4acf-9e3c-39dec923a808`, `0040970c-4283-4b04-9034-524d889f1b20` |
| `name_normalized` | TEXT | oui | non | 0.0 % | 9 374 | `1 - C. ESCUDER`, `1 - M. SEROR`, `1 – R. DERIEUX` |
| `name_key` | TEXT | oui | non | 0.0 % | 9 700 | `1 C ESCUDER`, `1 M SEROR`, `1 R DERIEUX` |
| `resolution_method` | TEXT | oui | non | 0.0 % | 5 | `exact_name+sex_age`, `exact_name`, `name+pedigree` |
| `resolution_confidence` | REAL | oui | non | 0.0 % | 4 | `0.9`, `0.7`, `0.6` |
| `homonym_risk` | TEXT | oui | non | 0.0 % | 6 | `consistent_signal`, `no_signal`, `suspected_homonym` |
| `n_sex_birthyear_variants` | INTEGER | non | non | 0.1 % | 5 | `1`, `0`, `2` |
| `sex_birthyear_variants` | TEXT | non | non | 0.1 % | 197 | `H~2016`, ``, `F~2018 | H~2016` |
| `n_starts` | INTEGER | oui | non | 0.0 % | 24 | `1`, `2`, `5` |
| `first_seen_date` | TEXT | non | non | 0.1 % | 665 | `2026-01-30`, `2026-04-02`, `2026-02-03` |
| `last_seen_date` | TEXT | non | non | 0.1 % | 729 | `2026-01-30`, `2026-04-06`, `2026-03-18` |
| `pedigree_pere` | TEXT | non | non | 47.7 % | 1 333 | `RIO DE LA PLATA`, `BOLD EAGLE`, `RECOLETOS` |
| `pedigree_mere` | TEXT | non | non | 47.7 % | 4 818 | `ANCIENT EAST`, `WILL OF A WOMAN`, `TIA KIA` |
| `robe` | TEXT | non | non | 65.5 % | 20 | `BAI F.`, `BAI`, `ALEZAN` |
| `race` | TEXT | non | non | 47.7 % | 7 | `PUR-SANG`, `TROTTEUR ETRANGER`, `TROTTEUR FRANCAIS` |

**`master_person`** — 12 266 lignes

| Colonne | Type | NOT NULL | PK | Taux de nullité | Distinct | Exemples |
|---|---|---|---|---:|---:|---|
| `person_id` | TEXT | non | oui | 0.0 % | 12 266 | `000c8a52-09ef-40a9-8721-c462d687eec7`, `000ca919-b098-4c1c-a479-cb38d00d584b`, `00170396-6dd9-548d-b502-3a8c1bb33855` |
| `name_normalized` | TEXT | oui | non | 0.0 % | 10 864 | `7 - N. GEORGE & A. ZETTERHOLM`, `A.A. CHAVATTE`, `A. ABRIVARD` |
| `name_key` | TEXT | oui | non | 0.0 % | 10 919 | `7 N GEORGE A ZETTERHOLM`, `A A CHAVATTE`, `A ABRIVARD` |
| `role` | TEXT | oui | non | 0.0 % | 6 | `JOCKEY`, `OWNER`, `TRAINER` |
| `resolution_method` | TEXT | oui | non | 0.0 % | 3 | `exact_name`, `EXACT`, `api_pmu` |
| `resolution_confidence` | REAL | oui | non | 0.0 % | 1 | `1.0` |
| `n_appearances` | INTEGER | oui | non | 0.0 % | 131 | `3`, `8`, `205` |

**`master_race`** — 1 369 lignes

| Colonne | Type | NOT NULL | PK | Taux de nullité | Distinct | Exemples |
|---|---|---|---|---:|---:|---|
| `race_id` | TEXT | non | oui | 0.0 % | 1 369 | `001ab63d-80ca-52e8-8140-4e558d197284`, `0057ea67-00a0-5136-82a4-0c9c565e101a`, `0105467f-fd91-517f-87c9-58e4b3bb4256` |
| `source_document_id` | INTEGER | oui | non | 0.0 % | 939 | `1`, `2`, `3` |
| `date` | TEXT | non | non | 0.0 % | 742 | `1995-07-18`, `2024-01-19`, `2024-01-20` |
| `date_is_sentinel` | INTEGER | oui | non | 0.0 % | 2 | `0`, `1` |
| `hippodrome_id` | TEXT | non | non | 22.4 % | 98 | `00aef98f-8ea0-47ef-9bb0-e563ef9ea8d2`, `02475693-5203-54eb-9c96-68ad47dfe505`, `05411480-7a57-4334-af95-b6ab0412ed11` |
| `hippodrome_label_raw` | TEXT | non | non | 0.0 % | 128 | `DEAUVILLE NOCTURNE`, `PARIS-VINCENNES`, `11` |
| `discipline` | TEXT | non | non | 52.4 % | 11 | `PLAT`, `ATTELE`, `OBSTACLE` |
| `discipline_status` | TEXT | oui | non | 0.0 % | 4 | `present`, `missing`, `OK` |
| `distance_m` | INTEGER | non | non | 0.1 % | 99 | `1300`, `25`, `3400` |
| `montant_euros` | INTEGER | non | non | 1.0 % | 285 | `53000`, `4500`, `58000` |
| `partants_declares` | INTEGER | non | non | 0.7 % | 21 | `16`, `15`, `18` |
| `partants_effectifs` | INTEGER | non | non | 0.7 % | 20 | `15`, `14`, `13` |
| `type_course` | TEXT | non | non | 0.7 % | 3 | `HANDICAP`, ``, `AUTOSTART` |
| `titre` | TEXT | non | non | 0.0 % | 1 173 | `DEAUVILLE NOCTURNE - PRIX DU VOLCAN - PLAT`, `PARIS-VINCENNES - PRIX DE BREST - ATTELE`, `11 - FIFTY FIVE BOND : Excellent troisième du Pr` |
| `n_partants_source` | INTEGER | oui | non | 0.0 % | 20 | `15`, `14`, `13` |
| `n_runners_linked` | INTEGER | oui | non | 0.0 % | 20 | `15`, `14`, `13` |
| `result_status` | TEXT | oui | non | 0.0 % | 6 | `no_arrival_for_date`, `sentinel_date`, `arrival_available` |

**`master_runner`** — 18 282 lignes

| Colonne | Type | NOT NULL | PK | Taux de nullité | Distinct | Exemples |
|---|---|---|---|---:|---:|---|
| `runner_id` | TEXT | non | oui | 0.0 % | 18 282 | `0000634f-26be-5643-a4d4-6d1620ff6909`, `0000d280-19bd-5bed-9bc7-fdf1257ae616`, `00025f98-188c-5a4e-8c97-acaf61ef6749` |
| `race_id` | TEXT | oui | non | 0.0 % | 1 364 | `001ab63d-80ca-52e8-8140-4e558d197284`, `0057ea67-00a0-5136-82a4-0c9c565e101a`, `0105467f-fd91-517f-87c9-58e4b3bb4256` |
| `source_document_id` | INTEGER | oui | non | 0.0 % | 934 | `1`, `2`, `3` |
| `source_partant_id` | INTEGER | oui | non | 0.0 % | 13 286 | `1`, `2`, `3` |
| `numero` | INTEGER | non | non | 0.0 % | 26 | `1`, `2`, `3` |
| `horse_id` | TEXT | non | non | 0.0 % | 9 700 | `000bbb95-1b36-5ec3-aaef-9c5f00335b13`, `0036e82d-1c11-4acf-9e3c-39dec923a808`, `0040970c-4283-4b04-9034-524d889f1b20` |
| `jockey_id` | TEXT | non | non | 0.2 % | 2 222 | `00185bb9-eb82-52e2-8020-af1e414144c1`, `004d1393-b5ba-59d2-b4ed-74a618b438c8`, `0052f53c-4a5a-4b60-a85b-64298b46dd82` |
| `trainer_id` | TEXT | non | non | 0.6 % | 3 131 | `000ca919-b098-4c1c-a479-cb38d00d584b`, `00276e53-18fb-553b-b58f-d28b99bb64e0`, `003e55a4-9196-5a95-8360-07ffac68d9c3` |
| `owner_id` | TEXT | non | non | 5.2 % | 7 002 | `0496f548-cb12-5206-99cd-354ae23fe4c7`, `22776201-a47d-53be-921f-93c42b7c113e`, `2ed87667-9979-54ba-b0ae-de67ab83b195` |
| `cote_decimale` | REAL | non | non | 28.9 % | 220 | `35.0`, `39.0`, `26.0` |
| `gains_euros` | INTEGER | non | non | 5.6 % | 13 520 | `146785`, `115245`, `153110` |
| `performances_structured` | TEXT | non | non | 0.0 % | 15 829 | `[2, 2, 9, 5, 4]`, `[0, 0, 1, 7, 1]`, `[5, 9, 1, 3, 6]` |
| `sexe_raw` | TEXT | non | non | 0.7 % | 228 | `M.7`, `F.7`, `H.5` |
| `age_raw` | TEXT | non | non | 0.0 % | 14 | `7`, `5`, `4` |
| `poids_raw` | TEXT | non | non | 28.0 % | 1 | `` |
| `corde_raw` | TEXT | non | non | 28.0 % | 1 | `` |
| `result_position` | INTEGER | non | non | 60.8 % | 24 | `3`, `2`, `4` |
| `result_status` | TEXT | oui | non | 0.0 % | 8 | `no_arrival_for_date`, `sentinel_date`, `arrived` |

**`model_version`** — 0 lignes

| Colonne | Type | NOT NULL | PK | Taux de nullité | Distinct | Exemples |
|---|---|---|---|---:|---:|---|
| `version_id` | INTEGER | non | oui | — | 0 | — |
| `scope` | TEXT | oui | non | — | 0 | — |
| `version` | TEXT | oui | non | — | 0 | — |
| `created_at` | TEXT | oui | non | — | 0 | — |
| `notes` | TEXT | non | non | — | 0 | — |

**`phase3_leakage_audit`** — 5 lignes

| Colonne | Type | NOT NULL | PK | Taux de nullité | Distinct | Exemples |
|---|---|---|---|---:|---:|---|
| `check_name` | TEXT | non | oui | 0.0 % | 5 | `aucune_colonne_cible`, `cumul_strictement_anterieur`, `marche_coherent` |
| `result` | TEXT | oui | non | 0.0 % | 1 | `PASS` |
| `detail` | TEXT | non | non | 0.0 % | 5 | `train≤2025-11-05 < val≤2026-04-01 < test≤2026-09`, `0 lignes avec cote mais sans probabilité`, `0 courses dont la somme ≠ 1` |

**`prediction_snapshot`** — 0 lignes

| Colonne | Type | NOT NULL | PK | Taux de nullité | Distinct | Exemples |
|---|---|---|---|---:|---:|---|
| `snapshot_id` | INTEGER | non | oui | — | 0 | — |
| `race_id` | TEXT | non | non | — | 0 | — |
| `model_version` | TEXT | non | non | — | 0 | — |
| `cutoff_ts` | TEXT | non | non | — | 0 | — |
| `payload_json` | TEXT | non | non | — | 0 | — |
| `created_at` | TEXT | oui | non | — | 0 | — |

**`ref_discipline`** — 4 lignes

| Colonne | Type | NOT NULL | PK | Taux de nullité | Distinct | Exemples |
|---|---|---|---|---:|---:|---|
| `discipline_raw` | TEXT | non | oui | 0.0 % | 4 | ``, `ATTELE`, `OBSTACLE` |
| `discipline_norm` | TEXT | non | non | 25.0 % | 3 | `ATTELE`, `OBSTACLE`, `PLAT` |
| `status` | TEXT | oui | non | 0.0 % | 2 | `missing`, `present` |

**`ref_hippodrome`** — 86 lignes

| Colonne | Type | NOT NULL | PK | Taux de nullité | Distinct | Exemples |
|---|---|---|---|---:|---:|---|
| `label_variant` | TEXT | non | oui | 0.0 % | 86 | ``, `1`, `10` |
| `hippodrome_id` | TEXT | non | non | 23.3 % | 59 | `3f919aab-8053-5cb3-9337-fa0148065e9c`, `64f06856-9821-5c2e-869b-dec83dd089d6`, `ff09562f-4cdf-5561-a8d3-2ff7d5c3980f` |
| `quality_flag` | TEXT | oui | non | 0.0 % | 3 | `missing`, `numeric_parse_error`, `ok` |

### 2.3 Relations

| Source | Colonne | Cible | Origine |
|---|---|---|---|
| `comment_features` | `race_id` | `master_race` | inférée (nommage) |
| `comment_features` | `runner_id` | `master_runner` | déclarée (FOREIGN KEY) |
| `market_race_meta` | `race_id` | `master_race` | inférée (nommage) |
| `market_runner_features` | `race_id` | `master_race` | inférée (nommage) |
| `market_runner_features` | `runner_id` | `master_runner` | déclarée (FOREIGN KEY) |
| `master_race` | `hippodrome_id` | `master_hippodrome` | déclarée (FOREIGN KEY) |
| `master_runner` | `horse_id` | `master_horse` | déclarée (FOREIGN KEY) |
| `master_runner` | `race_id` | `master_race` | déclarée (FOREIGN KEY) |
| `prediction_snapshot` | `race_id` | `master_race` | inférée (nommage) |
| `ref_hippodrome` | `hippodrome_id` | `master_hippodrome` | inférée (nommage) |

## 2. Base `pmu-lonab-scraper/data/processed/pmu_lonab.db`

- Taille : **36.1 Mo**
- SHA-256 : `d71f6a013ff7fc5720ffd5824d0c71077cba1602c883073bd5bd60f41d2cdb42`
- Vues : aucune

### 2.1 Tables et volumes

| Table | Lignes | Clé primaire | Index |
|---|---:|---|---|
| `api_cotes` | 27 243 | `id` | `idx_cotes_course` |
| `api_courses` | 407 | `course_id` | — |
| `api_ecuries` | 2 | `id` | — |
| `api_meteo` | 0 | `id` | — |
| `api_partants` | 0 | `id` | — |
| `api_pronostics` | 407 | `id` | — |
| `api_rapports` | 2 492 | `id` | `idx_rapports_course` |
| `classements` | 1 | `id` | — |
| `commentaires` | 14 015 | `id` | — |
| `courses` | 929 | `id` | `idx_courses_hippo`, `idx_courses_date`, `idx_courses_doc` |
| `documents` | 2 711 | `id` | `idx_documents_date`, `idx_documents_type` |
| `ecd_courses` | 6 509 | `id` | `idx_ecd_courses_doc` |
| `ecd_documents` | 800 | `id` | `idx_ecd_doc` |
| `ecd_paris` | 11 879 | `id` | — |
| `media_selections` | 0 | `id` | — |
| `partants` | 13 163 | `id` | `idx_partants_nom`, `idx_partants_course`, `idx_partants_doc` |
| `partants_enrichis` | 185 | `id` | `idx_enrichis_date`, `idx_enrichis_cheval` |
| `rep_documents` | 45 | `id` | `idx_rep_doc` |
| `resultats` | 939 | `id` | `idx_resultats_date`, `idx_resultats_doc` |

### 2.2 Colonnes

**`api_cotes`** — 27 243 lignes

| Colonne | Type | NOT NULL | PK | Taux de nullité | Distinct | Exemples |
|---|---|---|---|---:|---:|---|
| `id` | INTEGER | non | oui | 0.0 % | 27 243 | `1`, `2`, `3` |
| `course_id` | TEXT | non | non | 0.0 % | 407 | `05092026_R1_C1`, `05092026_R1_C2`, `05092026_R1_C3` |
| `type_pari` | TEXT | non | non | 0.0 % | 15 | `E_SIMPLE_GAGNANT`, `E_DEUX_SUR_QUATRE`, `E_TRIO` |
| `numero` | INTEGER | non | non | 100.0 % | 0 | — |
| `cote_directe` | REAL | non | non | 100.0 % | 0 | — |
| `masse_enjeu` | INTEGER | non | non | 100.0 % | 0 | — |
| `cote_reference` | REAL | non | non | 100.0 % | 0 | — |
| `evolution_cote` | REAL | non | non | 100.0 % | 0 | — |
| `risque` | REAL | non | non | 100.0 % | 0 | — |
| `updatetime` | TEXT | non | non | 0.0 % | 702 | `1788607420000`, `1788607440000`, `1788609690000` |
| `synced_at` | DATETIME | non | non | 0.0 % | 407 | `2026-09-12 17:49:41`, `2026-09-12 17:49:43`, `2026-09-12 17:49:44` |

**`api_courses`** — 407 lignes

| Colonne | Type | NOT NULL | PK | Taux de nullité | Distinct | Exemples |
|---|---|---|---|---:|---:|---|
| `course_id` | TEXT | non | oui | 0.0 % | 407 | `05092026_R1_C1`, `05092026_R1_C2`, `05092026_R1_C3` |
| `date` | TEXT | non | non | 0.0 % | 7 | `05092026`, `06092026`, `07092026` |
| `reunion` | INTEGER | non | non | 0.0 % | 13 | `1`, `2`, `3` |
| `course_num` | INTEGER | non | non | 0.0 % | 12 | `1`, `2`, `3` |
| `hippodrome_code` | TEXT | non | non | 100.0 % | 0 | — |
| `hippodrome_nom` | TEXT | non | non | 100.0 % | 0 | — |
| `discipline` | TEXT | non | non | 0.0 % | 6 | `ATTELE`, `MONTE`, `PLAT` |
| `distance` | INTEGER | non | non | 0.0 % | 62 | `2175`, `2100`, `2700` |
| `type_course` | TEXT | non | non | 0.0 % | 4 | `TROT_ATTELE`, `TROT_MONTE`, `PLAT` |
| `titre` | TEXT | non | non | 0.0 % | 392 | `PRIX JOSEPH AVELINE`, `PRIX DE LUSIGNY`, `PRIX DE BEZIERS` |
| `heure_depart` | TEXT | non | non | 0.0 % | 259 | `13:23`, `13:58`, `14:33` |
| `partants_declares` | INTEGER | non | non | 0.0 % | 16 | `10`, `13`, `14` |
| `partants_effectifs` | INTEGER | non | non | 0.0 % | 1 | `0` |
| `data_json` | TEXT | non | non | 0.0 % | 407 | `{"cached": false, "departImminent": false, "arri`, `{"cached": false, "departImminent": false, "arri`, `{"cached": false, "departImminent": false, "arri` |
| `synced_at` | DATETIME | non | non | 0.0 % | 7 | `2026-09-12 17:49:41`, `2026-09-12 17:51:07`, `2026-09-12 17:52:46` |

**`api_ecuries`** — 2 lignes

| Colonne | Type | NOT NULL | PK | Taux de nullité | Distinct | Exemples |
|---|---|---|---|---:|---:|---|
| `id` | INTEGER | non | oui | 0.0 % | 2 | `1`, `4` |
| `nom` | TEXT | non | non | 0.0 % | 2 | `A`, `B` |
| `casaque_url` | TEXT | non | non | 100.0 % | 0 | — |
| `data_json` | TEXT | non | non | 0.0 % | 2 | `{"nom": "A"}`, `{"nom": "B"}` |

**`api_meteo`** — 0 lignes

| Colonne | Type | NOT NULL | PK | Taux de nullité | Distinct | Exemples |
|---|---|---|---|---:|---:|---|
| `id` | INTEGER | non | oui | — | 0 | — |
| `date` | TEXT | oui | non | — | 0 | — |
| `hippodrome_code` | TEXT | oui | non | — | 0 | — |
| `temperature` | REAL | non | non | — | 0 | — |
| `vent_force` | REAL | non | non | — | 0 | — |
| `vent_direction` | TEXT | non | non | — | 0 | — |
| `nebulosite_code` | INTEGER | non | non | — | 0 | — |
| `condition` | TEXT | non | non | — | 0 | — |
| `terrain` | TEXT | non | non | — | 0 | — |
| `data_json` | TEXT | non | non | — | 0 | — |

**`api_partants`** — 0 lignes

| Colonne | Type | NOT NULL | PK | Taux de nullité | Distinct | Exemples |
|---|---|---|---|---:|---:|---|
| `id` | INTEGER | non | oui | — | 0 | — |
| `course_id` | TEXT | oui | non | — | 0 | — |
| `numero_pmu` | INTEGER | non | non | — | 0 | — |
| `nom` | TEXT | non | non | — | 0 | — |
| `age` | INTEGER | non | non | — | 0 | — |
| `sexe` | TEXT | non | non | — | 0 | — |
| `race` | TEXT | non | non | — | 0 | — |
| `statut` | TEXT | non | non | — | 0 | — |
| `corde` | INTEGER | non | non | — | 0 | — |
| `oeilleres` | TEXT | non | non | — | 0 | — |
| `proprietaire` | TEXT | non | non | — | 0 | — |
| `entraineur` | TEXT | non | non | — | 0 | — |
| `deferre` | TEXT | non | non | — | 0 | — |
| `driver` | TEXT | non | non | — | 0 | — |
| `driver_change` | BOOLEAN | non | non | — | 0 | — |
| `musique` | TEXT | non | non | — | 0 | — |
| `nb_courses` | INTEGER | non | non | — | 0 | — |
| `nb_victoires` | INTEGER | non | non | — | 0 | — |
| `nb_places` | INTEGER | non | non | — | 0 | — |
| `gains_carriere` | INTEGER | non | non | — | 0 | — |
| `pere` | TEXT | non | non | — | 0 | — |
| `mere` | TEXT | non | non | — | 0 | — |
| `ordre_arrivee` | INTEGER | non | non | — | 0 | — |
| `engagement` | TEXT | non | non | — | 0 | — |
| `supplement` | BOOLEAN | non | non | — | 0 | — |
| `handicap_distance` | INTEGER | non | non | — | 0 | — |
| `poids` | INTEGER | non | non | — | 0 | — |
| `temps_obtenu` | TEXT | non | non | — | 0 | — |
| `reduction_km` | TEXT | non | non | — | 0 | — |
| `dernier_rapport_direct` | REAL | non | non | — | 0 | — |
| `dernier_rapport_reference` | REAL | non | non | — | 0 | — |
| `avis_entraineur` | TEXT | non | non | — | 0 | — |
| `data_json` | TEXT | non | non | — | 0 | — |

**`api_pronostics`** — 407 lignes

| Colonne | Type | NOT NULL | PK | Taux de nullité | Distinct | Exemples |
|---|---|---|---|---:|---:|---|
| `id` | INTEGER | non | oui | 0.0 % | 407 | `1`, `2`, `3` |
| `course_id` | TEXT | non | non | 0.0 % | 407 | `05092026_R1_C1`, `05092026_R1_C2`, `05092026_R1_C3` |
| `source` | TEXT | non | non | 0.0 % | 1 | `DATAHIPPIQUE` |
| `pronostics` | TEXT | non | non | 0.0 % | 407 | `{"prono_pmu_fr": {"selection": [{"cote_prob": "3`, `{"prono_pmu_fr": {"selection": [{"cote_prob": "3`, `{"prono_pmu_fr": {"selection": [{"cote_prob": "3` |
| `nb_partants` | INTEGER | non | non | 0.0 % | 16 | `10`, `13`, `14` |
| `data_json` | TEXT | non | non | 0.0 % | 407 | `{"nom_prix": "PRIX JOSEPH AVELINE", "id_nav_cour`, `{"nom_prix": "PRIX DE LUSIGNY", "id_nav_course":`, `{"nom_prix": "PRIX DE BEZIERS", "id_nav_course":` |

**`api_rapports`** — 2 492 lignes

| Colonne | Type | NOT NULL | PK | Taux de nullité | Distinct | Exemples |
|---|---|---|---|---:|---:|---|
| `id` | INTEGER | non | oui | 0.0 % | 2 492 | `1`, `2`, `3` |
| `course_id` | TEXT | non | non | 0.0 % | 407 | `05092026_R1_C1`, `05092026_R1_C2`, `05092026_R1_C3` |
| `type_pari` | TEXT | non | non | 0.0 % | 19 | `E_COUPLE_GAGNANT`, `E_COUPLE_PLACE`, `E_DEUX_SUR_QUATRE` |
| `arrivee` | TEXT | non | non | 0.0 % | 1 | `[]` |
| `arrivee_consolidee` | TEXT | non | non | 0.0 % | 1 | `[]` |
| `gains_base` | REAL | non | non | 100.0 % | 0 | — |
| `gains_ordre` | REAL | non | non | 100.0 % | 0 | — |
| `gains_desordre` | REAL | non | non | 100.0 % | 0 | — |
| `nb_gagnants` | INTEGER | non | non | 100.0 % | 0 | — |
| `masse_partager` | REAL | non | non | 100.0 % | 0 | — |
| `rapports_consolides` | TEXT | non | non | 0.0 % | 1 | `[]` |
| `risques` | TEXT | non | non | 0.0 % | 1 | `[]` |
| `data_json` | TEXT | non | non | 0.0 % | 2 457 | `{"typePari": "E_SIMPLE_GAGNANT", "miseBase": 100`, `{"typePari": "E_SIMPLE_PLACE", "miseBase": 100, `, `{"typePari": "E_COUPLE_GAGNANT", "miseBase": 100` |

**`classements`** — 1 lignes

| Colonne | Type | NOT NULL | PK | Taux de nullité | Distinct | Exemples |
|---|---|---|---|---:|---:|---|
| `id` | INTEGER | non | oui | 0.0 % | 1 | `1` |
| `document_id` | INTEGER | oui | non | 0.0 % | 1 | `393` |
| `course_id` | TEXT | oui | non | 0.0 % | 1 | `` |
| `forme` | TEXT | non | non | 0.0 % | 1 | `[]` |
| `classe` | TEXT | non | non | 0.0 % | 1 | `[]` |
| `progres` | TEXT | non | non | 0.0 % | 1 | `[]` |
| `regularite` | TEXT | non | non | 0.0 % | 1 | `[]` |

**`commentaires`** — 14 015 lignes

| Colonne | Type | NOT NULL | PK | Taux de nullité | Distinct | Exemples |
|---|---|---|---|---:|---:|---|
| `id` | INTEGER | non | oui | 0.0 % | 14 015 | `1`, `2`, `3` |
| `document_id` | INTEGER | oui | non | 0.0 % | 896 | `1`, `2`, `3` |
| `course_id` | TEXT | oui | non | 0.0 % | 577 | ``, `JH_21-01-2024`, `JH_22-01-2024` |
| `numero_cheval` | INTEGER | oui | non | 0.0 % | 20 | `1`, `2`, `3` |
| `texte` | TEXT | non | non | 0.0 % | 13 983 | `SHINNING OCEAN : Dominé en novembre par RAKAN (1`, `ZAYA DE LA PLATA : Cette jument de Thierry Taill`, `PEDRITO : Lauréat d'un gros handicap lors de la ` |

**`courses`** — 929 lignes

| Colonne | Type | NOT NULL | PK | Taux de nullité | Distinct | Exemples |
|---|---|---|---|---:|---:|---|
| `id` | INTEGER | non | oui | 0.0 % | 929 | `1`, `2`, `3` |
| `document_id` | INTEGER | oui | non | 0.0 % | 929 | `1`, `2`, `3` |
| `course_id` | TEXT | oui | non | 0.0 % | 605 | ``, `JH_21-01-2024`, `JH_22-01-2024` |
| `date` | TEXT | non | non | 0.0 % | 734 | `1995-07-18`, `2024-01-19`, `2024-01-20` |
| `reunion` | TEXT | non | non | 0.0 % | 1 | `` |
| `course_num` | INTEGER | non | non | 0.0 % | 10 | `0`, `4`, `2` |
| `hippodrome` | TEXT | non | non | 0.0 % | 86 | ``, `1`, `10` |
| `discipline` | TEXT | non | non | 0.0 % | 4 | `PLAT`, `ATTELE`, `` |
| `distance_raw` | TEXT | non | non | 0.0 % | 111 | `1300`, `25`, `3400` |
| `distance_m` | INTEGER | non | non | 0.2 % | 82 | `1300`, `25`, `3400` |
| `montant_raw` | TEXT | non | non | 0.0 % | 131 | `53 000`, `4500`, `58 000` |
| `montant_euros` | INTEGER | non | non | 0.5 % | 129 | `53000`, `4500`, `58000` |
| `partants_declares` | INTEGER | non | non | 0.0 % | 9 | `16`, `15`, `18` |
| `partants_effectifs` | INTEGER | non | non | 0.0 % | 8 | `15`, `14`, `13` |
| `type_course` | TEXT | non | non | 0.0 % | 3 | `HANDICAP`, ``, `AUTOSTART` |
| `titre` | TEXT | non | non | 0.0 % | 739 | `DEAUVILLE NOCTURNE - PRIX DU VOLCAN - PLAT`, `PARIS-VINCENNES - PRIX DE BREST - ATTELE`, `11 - FIFTY FIVE BOND : Excellent troisième du Pr` |
| `heure_depart` | TEXT | non | non | 0.0 % | 2 | ``, `18H 45mn` |
| `heure_arret_jeux` | TEXT | non | non | 0.0 % | 1 | `` |
| `raw_text` | TEXT | non | non | 100.0 % | 0 | — |

**`documents`** — 2 711 lignes

| Colonne | Type | NOT NULL | PK | Taux de nullité | Distinct | Exemples |
|---|---|---|---|---:|---:|---|
| `id` | INTEGER | non | oui | 0.0 % | 2 711 | `46`, `203`, `1400` |
| `filename` | TEXT | oui | non | 0.0 % | 2 711 | `19_06_2025_QUARTE.pdf`, `21_03_2026_TIERCE.pdf`, `25_03_2024_QUARTE.pdf` |
| `doc_type` | TEXT | oui | non | 0.0 % | 4 | `COURSE_EN_DIRECT`, `JOURNAL`, `REP` |
| `date_publication` | TEXT | non | non | 0.0 % | 935 | ``, `1995-07-18`, `2024-01-19` |
| `pages` | INTEGER | non | non | 0.0 % | 3 | `2`, `0`, `1` |
| `quality_score` | INTEGER | non | non | 100.0 % | 0 | — |
| `quality_status` | TEXT | non | non | 100.0 % | 0 | — |
| `parsing_errors` | TEXT | non | non | 0.0 % | 1 | `[]` |
| `created_at` | TIMESTAMP | non | non | 0.0 % | 1 | `2026-09-10 11:27:06` |

**`ecd_courses`** — 6 509 lignes

| Colonne | Type | NOT NULL | PK | Taux de nullité | Distinct | Exemples |
|---|---|---|---|---:|---:|---|
| `id` | INTEGER | non | oui | 0.0 % | 6 509 | `1`, `2`, `3` |
| `document_id` | INTEGER | oui | non | 0.0 % | 800 | `1914`, `1915`, `1916` |
| `course_id` | TEXT | oui | non | 0.0 % | 6 509 | `ECD_01-07-2026_R1_C1`, `ECD_01-07-2026_R1_C2`, `ECD_01-07-2026_R1_C3` |
| `numero_course` | INTEGER | non | non | 0.0 % | 9 | `1`, `2`, `3` |
| `arrivee_raw` | TEXT | non | non | 0.0 % | 5 862 | `10 950
69
0
0
0
0`, `5 350
162
0
0
0
0`, `62 550
14
0
0
0
0` |
| `arrivee_positions` | TEXT | non | non | 0.0 % | 5 862 | `[10, 950, 69, 0, 0, 0, 0]`, `[5, 350, 162, 0, 0, 0, 0]`, `[62, 550, 14, 0, 0, 0, 0]` |
| `gains_total_raw` | TEXT | non | non | 100.0 % | 0 | — |
| `gains_total_euros` | INTEGER | non | non | 100.0 % | 0 | — |
| `page_num` | INTEGER | non | non | 0.0 % | 2 | `1`, `2` |
| `y_position` | REAL | non | non | 0.0 % | 529 | `103.0`, `282.0`, `458.0` |
| `raw_text` | TEXT | non | non | 0.0 % | 6 501 | `1ère
3 - 8 - 7
8
550
3
3 - 7
3 050
105
7
550
2
8`, `2ième
9 - 5 - 7
5
0
0
9 - 7
1 200
311
7
0
0
5 - `, `3ième
11 - 5 - 10
5
700
5
11 - 10
4 500
103
10
1` |

**`ecd_documents`** — 800 lignes

| Colonne | Type | NOT NULL | PK | Taux de nullité | Distinct | Exemples |
|---|---|---|---|---:|---:|---|
| `id` | INTEGER | non | oui | 0.0 % | 800 | `1`, `2`, `3` |
| `document_id` | INTEGER | oui | non | 0.0 % | 800 | `1914`, `1915`, `1916` |
| `date` | TEXT | non | non | 0.0 % | 401 | `2026-07-01`, `2025-08-01`, `2026-08-01` |
| `reunion` | TEXT | non | non | 0.0 % | 5 | `1`, `3`, `4` |
| `hippodrome` | TEXT | non | non | 0.0 % | 72 | `ENGHIEN`, `NANTES`, `CABOURG` |
| `discipline` | TEXT | non | non | 100.0 % | 0 | — |
| `date_heure_extraction` | TEXT | non | non | 100.0 % | 0 | — |
| `raw_text` | TEXT | non | non | 0.0 % | 799 | `PARI
N°
MONTANT
NB
PARI
N°
MONTANT NB
GAGNANT
3
`, `PARI
N°
MONTANT
NB
PARI
N°
MONTANT NB
GAGNANT
5
`, `PARI
N°
MONTANT
NB
PARI
N°
MONTANT NB
GAGNANT
10` |

**`ecd_paris`** — 11 879 lignes

| Colonne | Type | NOT NULL | PK | Taux de nullité | Distinct | Exemples |
|---|---|---|---|---:|---:|---|
| `id` | INTEGER | non | oui | 0.0 % | 11 879 | `1`, `2`, `3` |
| `ecd_course_id` | INTEGER | oui | non | 0.0 % | 4 918 | `1`, `2`, `3` |
| `type_pari` | TEXT | non | non | 0.0 % | 2 | `GAGNANT`, `JUM GAGNANT` |
| `combinaison_raw` | TEXT | non | non | 0.0 % | 242 | ``, `9 - 5`, `4 - 9` |
| `combinaison_normalized` | TEXT | non | non | 0.0 % | 242 | `[]`, `[9, 5]`, `[4, 9]` |
| `montant_raw` | TEXT | non | non | 0.0 % | 455 | `0`, `800`, `11` |
| `montant_euros` | INTEGER | non | non | 16.9 % | 208 | `0`, `800`, `11` |
| `nb_paris` | INTEGER | non | non | 26.3 % | 240 | `0`, `2`, `4` |
| `position` | TEXT | non | non | 100.0 % | 0 | — |
| `uncertain` | BOOLEAN | non | non | 0.0 % | 1 | `0` |

**`media_selections`** — 0 lignes

| Colonne | Type | NOT NULL | PK | Taux de nullité | Distinct | Exemples |
|---|---|---|---|---:|---:|---|
| `id` | INTEGER | non | oui | — | 0 | — |
| `document_id` | INTEGER | oui | non | — | 0 | — |
| `course_id` | TEXT | oui | non | — | 0 | — |
| `source` | TEXT | non | non | — | 0 | — |
| `selection` | TEXT | non | non | — | 0 | — |
| `rang` | TEXT | non | non | — | 0 | — |

**`partants`** — 13 163 lignes

| Colonne | Type | NOT NULL | PK | Taux de nullité | Distinct | Exemples |
|---|---|---|---|---:|---:|---|
| `id` | INTEGER | non | oui | 0.0 % | 13 163 | `1`, `2`, `3` |
| `document_id` | INTEGER | oui | non | 0.0 % | 924 | `1`, `2`, `3` |
| `course_id` | TEXT | oui | non | 0.0 % | 603 | ``, `1995-07-18_11_C4`, `1995-07-18_12_C4` |
| `numero` | INTEGER | oui | non | 0.0 % | 20 | `1`, `2`, `3` |
| `nom_cheval_raw` | TEXT | non | non | 0.0 % | 4 890 | `SHINNING OCEAN`, `ZAYA DE LA PLATA`, `PEDRITO` |
| `nom_cheval_normalized` | TEXT | non | non | 0.0 % | 4 889 | `1 - C. ESCUDER`, `1 - M. SEROR`, `1 – R. DERIEUX` |
| `sexe` | TEXT | non | non | 0.0 % | 225 | `M.7`, `F.7`, `H.5` |
| `age` | TEXT | non | non | 0.0 % | 11 | `7`, `5`, `4` |
| `poids` | TEXT | non | non | 0.0 % | 1 | `` |
| `corde` | TEXT | non | non | 0.0 % | 1 | `` |
| `distance_raw` | TEXT | non | non | 0.0 % | 179 | `8`, `4`, `6` |
| `distance_m` | INTEGER | non | non | 99.9 % | 4 | `15`, `2`, `55` |
| `chrono_raw` | TEXT | non | non | 0.0 % | 197 | `60.KG`, `59,5.KG`, `57,5.KG` |
| `chrono_normalized` | TEXT | non | non | 0.0 % | 197 | `60.KG`, `59,5.KG`, `57,5.KG` |
| `performances_raw` | TEXT | non | non | 0.0 % | 11 235 | `2.2.9.5.4`, `0.0.1.7.1`, `5.9.1.3.6` |
| `performances_structured` | TEXT | non | non | 0.0 % | 11 234 | `[2, 2, 9, 5, 4]`, `[0, 0, 1, 7, 1]`, `[5, 9, 1, 3, 6]` |
| `gains_raw` | TEXT | non | non | 0.0 % | 10 829 | `146 785`, `115 245`, `153 110` |
| `gains_euros` | INTEGER | non | non | 6.9 % | 9 740 | `146785`, `115245`, `153110` |
| `driver_raw` | TEXT | non | non | 0.0 % | 919 | `D.SANTIAGO`, `T.BLANCHOUIN`, `T.PICCONE` |
| `driver_normalized` | TEXT | non | non | 0.0 % | 917 | `D.SANTIAGO`, `T.BLANCHOUIN`, `T.PICCONE` |
| `entraineur_raw` | TEXT | non | non | 0.0 % | 1 469 | `H.BLUME`, `J.BOISNARD`, `HA.PANTALL` |
| `entraineur_normalized` | TEXT | non | non | 0.0 % | 1 466 | `H.BLUME`, `J.BOISNARD`, `HA.PANTALL` |
| `proprietaire_raw` | TEXT | non | non | 0.0 % | 4 300 | `Y.MARIE-NELLY`, `T.TAILLEUR`, `HA.PANTALL` |
| `proprietaire_normalized` | TEXT | non | non | 0.0 % | 4 296 | `Y.MARIE-NELLY`, `T.TAILLEUR`, `HA.PANTALL` |
| `cote_raw` | TEXT | non | non | 0.0 % | 141 | `35/1`, `39/1`, `26/1` |
| `cote_decimale` | REAL | non | non | 2.1 % | 140 | `35.0`, `39.0`, `26.0` |
| `commentaire` | TEXT | non | non | 0.0 % | 12 682 | `SHINNING OCEAN : Dominé en novembre par RAKAN (1`, `ZAYA DE LA PLATA : Cette jument de Thierry Taill`, `PEDRITO : Lauréat d'un gros handicap lors de la ` |
| `raw_data` | TEXT | non | non | 0.0 % | 13 121 | `{"450": "TURF", "600": "34/1   41/1   24/1  11/1`, `{"440": "MAGAZINE\nPARIS", "30": "2", "70": "ZAY`, `{"440": "TIERCE", "600": "35/1   39/1  26/1    9` |

**`partants_enrichis`** — 185 lignes

| Colonne | Type | NOT NULL | PK | Taux de nullité | Distinct | Exemples |
|---|---|---|---|---:|---:|---|
| `id` | INTEGER | non | oui | 0.0 % | 185 | `35`, `36`, `37` |
| `document_id` | INTEGER | non | non | 0.0 % | 12 | `124`, `5`, `18` |
| `nom_cheval_normalized` | TEXT | oui | non | 0.0 % | 103 | `AETOS KRONOS`, `ALWAYS EK`, `AMPIA MEDE SM` |
| `date_course` | TEXT | oui | non | 0.0 % | 12 | `2024-01-28`, `2024-02-09`, `2024-02-11` |
| `reunion_num` | INTEGER | non | non | 0.0 % | 1 | `1` |
| `course_num` | INTEGER | non | non | 0.0 % | 6 | `4`, `7`, `3` |
| `numero_pmu` | INTEGER | non | non | 0.0 % | 18 | `1`, `2`, `3` |
| `deferre` | TEXT | non | non | 9.7 % | 7 | `DEFERRE_ANTERIEURS_POSTERIEURS`, `PROTEGE_ANTERIEURS`, `PROTEGE_ANTERIEURS_DEFERRRE_POSTERIEURS` |
| `musique_officielle` | TEXT | non | non | 0.0 % | 185 | `DA3A0A235A1A6ADA2A3M`, `1A6ADM7A2A231A8A0A0A`, `0A9A2A4ADA232A2A3A2A` |
| `nom_pere` | TEXT | non | non | 0.0 % | 72 | `NIKY`, `LUDO DE CASTELLE`, `LOOK DE STAR` |
| `nom_mere` | TEXT | non | non | 0.0 % | 101 | `ABRICOTINE`, `SILICE D'HERFRAIE`, `PERLE D'AVRIL` |
| `nom_pere_mere` | TEXT | non | non | 100.0 % | 0 | — |
| `race` | TEXT | non | non | 0.0 % | 2 | `TROTTEUR FRANCAIS`, `TROTTEUR ETRANGER` |
| `robe` | TEXT | non | non | 0.0 % | 6 | `BAI CL`, `BAI`, `ALEZAN` |
| `oeilleres` | TEXT | non | non | 0.0 % | 1 | `SANS_OEILLERES` |
| `gains_carriere_euros` | INTEGER | non | non | 0.0 % | 170 | `315950`, `332400`, `334980` |
| `gains_annee_euros` | INTEGER | non | non | 0.0 % | 118 | `12600`, `49710`, `24750` |
| `gains_victoires_euros` | INTEGER | non | non | 0.0 % | 119 | `145350`, `211500`, `216900` |
| `taux_reclamation` | INTEGER | non | non | 100.0 % | 0 | — |
| `raw_api_data` | TEXT | non | non | 0.0 % | 185 | `{"nom": "GHOSTBUSTER", "numPmu": 1, "age": 8, "s`, `{"nom": "GUINESS D'HERFRAIE", "numPmu": 2, "age"`, `{"nom": "GOLD DAIRPET", "numPmu": 3, "age": 8, "` |
| `enriched_at` | TIMESTAMP | non | non | 0.0 % | 12 | `2026-09-11 22:18:05`, `2026-09-11 22:18:24`, `2026-09-11 22:18:26` |

**`rep_documents`** — 45 lignes

| Colonne | Type | NOT NULL | PK | Taux de nullité | Distinct | Exemples |
|---|---|---|---|---:|---:|---|
| `id` | INTEGER | non | oui | 0.0 % | 45 | `1`, `2`, `3` |
| `document_id` | INTEGER | oui | non | 0.0 % | 45 | `1869`, `1870`, `1871` |
| `document_type` | TEXT | non | non | 0.0 % | 1 | `REP` |
| `date_document` | TEXT | non | non | 0.0 % | 39 | `2024-05-24`, `2025-04-12`, `2025-05-10` |
| `date_document_raw` | TEXT | non | non | 0.0 % | 39 | `24/05/2024`, `12/04/2025`, `10/05/2025` |
| `date_course_cible` | TEXT | non | non | 0.0 % | 37 | `2024-05-28`, `2025-04-16`, `2025-05-14` |
| `date_course_cible_raw` | TEXT | non | non | 0.0 % | 37 | `MARDI 28/05/2024`, `MERCREDI 16/04/2025`, `MERCREDI 14/05/2025` |
| `game_type` | TEXT | non | non | 0.0 % | 2 | `4+1`, `` |
| `report_ordre_raw` | TEXT | non | non | 0.0 % | 38 | `46 776 739`, `48 421 054`, `` |
| `report_ordre_euros` | INTEGER | non | non | 15.6 % | 37 | `46776739`, `48421054`, `99712433` |
| `tierce_v_raw` | TEXT | non | non | 0.0 % | 1 | `` |
| `tierce_v_value` | INTEGER | non | non | 100.0 % | 0 | — |
| `raw_text` | TEXT | non | non | 0.0 % | 45 | `"4+1" DU MARDI 28 MAI 2024
AUTEUIL - PRIX ALADDI`, `AN XXIV - N° 43 955 - GRATUIT
Numéros clientèle `, `Numéros clientèle : 25 49 72 00 / 70 20 01 10
AN` |

**`resultats`** — 939 lignes

| Colonne | Type | NOT NULL | PK | Taux de nullité | Distinct | Exemples |
|---|---|---|---|---:|---:|---|
| `id` | INTEGER | non | oui | 0.0 % | 939 | `1`, `2`, `3` |
| `document_id` | INTEGER | oui | non | 0.0 % | 937 | `46`, `203`, `403` |
| `course_id` | TEXT | oui | non | 0.0 % | 921 | ``, `2025-03-31_QUARTE_R1`, `2024-02-09_4PLUS1_R1` |
| `date` | TEXT | non | non | 0.0 % | 919 | ``, `2024-02-09`, `2024-02-10` |
| `type_pari` | TEXT | non | non | 0.0 % | 4 | ``, `QUARTE`, `4+1` |
| `arrivee` | TEXT | non | non | 0.0 % | 908 | `[]`, `[6, 2, 1, 4, 10]`, `[7, 18, 6, 15, 17]` |
| `arrivee_complete` | TEXT | non | non | 0.0 % | 908 | `[]`, `[{"position": 1, "numero": 6}, {"position": 2, "`, `[{"position": 1, "numero": 7}, {"position": 2, "` |
| `npo` | INTEGER | non | non | 0.0 % | 19 | `0`, `12`, `10` |
| `np` | INTEGER | non | non | 0.0 % | 18 | `0`, `5`, `13` |
| `disqualifies` | TEXT | non | non | 0.0 % | 1 | `[]` |
| `non_partants` | TEXT | non | non | 0.0 % | 2 | `[]`, `[0, 0]` |
| `gains_ordre_raw` | TEXT | non | non | 0.0 % | 877 | ``, `17 352 500 
     
5`, `1 053 000 
       
101` |
| `gains_ordre_euros` | INTEGER | non | non | 1.4 % | 816 | `17352500`, `1053000`, `2692500` |
| `gains_desordre_raw` | TEXT | non | non | 0.0 % | 916 | ``, `127 500 F (156 G)
       24 000 F (407 G)
      `, `82 500 
            
1 199` |
| `gains_desordre_euros` | INTEGER | non | non | 1.4 % | 429 | `82500`, `21000`, `47000` |
| `gains_bonus_raw` | TEXT | non | non | 0.0 % | 425 | ``, `4 000 
              
7 417
MAP "4+1"  :
215 348`, `1 000 
              
16 596
MAP "4+1"  :
178 28` |
| `gains_bonus_euros` | INTEGER | non | non | 54.1 % | 73 | `4000`, `1000`, `2000` |
| `nb_gagnants_ordre` | INTEGER | non | non | 5.6 % | 338 | `5`, `101`, `23` |
| `nb_gagnants_desordre` | INTEGER | non | non | 1.3 % | 823 | `407`, `1199`, `2635` |
| `nb_gagnants_bonus` | INTEGER | non | non | 54.1 % | 418 | `7417`, `16596`, `16326` |
| `masse_partager_raw` | TEXT | non | non | 0.0 % | 2 | ``, `48 393 000` |
| `masse_partager_euros` | INTEGER | non | non | 99.9 % | 1 | `48393000` |
| `rapport_gagnant_raw` | TEXT | non | non | 0.0 % | 920 | ``, `Couplé Placé A       :
Couplé Placé B       :
Co`, `13 000 
            
1 709` |
| `rapport_gagnant_euros` | INTEGER | non | non | 1.0 % | 200 | `13000`, `5000`, `6500` |
| `rapport_place_a_raw` | TEXT | non | non | 0.0 % | 907 | ``, `4 000 
              
2 849`, `1 500 
              
6 675` |
| `rapport_place_a_euros` | INTEGER | non | non | 1.8 % | 68 | `4000`, `1500`, `3500` |
| `rapport_place_b_raw` | TEXT | non | non | 0.0 % | 912 | ``, `10 000 
            
1 109 
                    `, `2 000 
              
4 649 
                   ` |
| `rapport_place_b_euros` | INTEGER | non | non | 1.9 % | 79 | `10000`, `2000`, `4000` |
| `map_paris_raw` | TEXT | non | non | 0.0 % | 917 | ``, `55 593 000`, `48 390 500` |
| `map_paris_euros` | INTEGER | non | non | 1.0 % | 914 | `55593000`, `48390500`, `42675500` |
| `raw_text` | TEXT | non | non | 100.0 % | 0 | — |

### 2.3 Relations

| Source | Colonne | Cible | Origine |
|---|---|---|---|
| `api_cotes` | `course_id` | `courses` | inférée (nommage) |
| `api_courses` | `course_id` | `courses` | inférée (nommage) |
| `api_partants` | `course_id` | `courses` | inférée (nommage) |
| `api_pronostics` | `course_id` | `courses` | inférée (nommage) |
| `api_rapports` | `course_id` | `courses` | inférée (nommage) |
| `classements` | `course_id` | `courses` | inférée (nommage) |
| `classements` | `document_id` | `documents` | déclarée (FOREIGN KEY) |
| `commentaires` | `course_id` | `courses` | inférée (nommage) |
| `commentaires` | `document_id` | `documents` | déclarée (FOREIGN KEY) |
| `courses` | `document_id` | `documents` | déclarée (FOREIGN KEY) |
| `ecd_courses` | `course_id` | `courses` | inférée (nommage) |
| `ecd_courses` | `document_id` | `documents` | déclarée (FOREIGN KEY) |
| `ecd_documents` | `document_id` | `documents` | déclarée (FOREIGN KEY) |
| `ecd_paris` | `ecd_course_id` | `ecd_courses` | déclarée (FOREIGN KEY) |
| `media_selections` | `course_id` | `courses` | inférée (nommage) |
| `media_selections` | `document_id` | `documents` | déclarée (FOREIGN KEY) |
| `partants` | `course_id` | `courses` | inférée (nommage) |
| `partants` | `document_id` | `documents` | déclarée (FOREIGN KEY) |
| `partants_enrichis` | `document_id` | `documents` | déclarée (FOREIGN KEY) |
| `rep_documents` | `document_id` | `documents` | déclarée (FOREIGN KEY) |
| `resultats` | `course_id` | `courses` | inférée (nommage) |
| `resultats` | `document_id` | `documents` | déclarée (FOREIGN KEY) |

## 2. Base `pmu-lonab-scraper/data/backups/phase1/pmu_lonab_phase1_backup_20260913_142930.db`

- Taille : **36.1 Mo**
- SHA-256 : `d71f6a013ff7fc5720ffd5824d0c71077cba1602c883073bd5bd60f41d2cdb42`
- Vues : aucune

### 2.1 Tables et volumes

| Table | Lignes | Clé primaire | Index |
|---|---:|---|---|
| `api_cotes` | 27 243 | `id` | `idx_cotes_course` |
| `api_courses` | 407 | `course_id` | — |
| `api_ecuries` | 2 | `id` | — |
| `api_meteo` | 0 | `id` | — |
| `api_partants` | 0 | `id` | — |
| `api_pronostics` | 407 | `id` | — |
| `api_rapports` | 2 492 | `id` | `idx_rapports_course` |
| `classements` | 1 | `id` | — |
| `commentaires` | 14 015 | `id` | — |
| `courses` | 929 | `id` | `idx_courses_hippo`, `idx_courses_date`, `idx_courses_doc` |
| `documents` | 2 711 | `id` | `idx_documents_date`, `idx_documents_type` |
| `ecd_courses` | 6 509 | `id` | `idx_ecd_courses_doc` |
| `ecd_documents` | 800 | `id` | `idx_ecd_doc` |
| `ecd_paris` | 11 879 | `id` | — |
| `media_selections` | 0 | `id` | — |
| `partants` | 13 163 | `id` | `idx_partants_nom`, `idx_partants_course`, `idx_partants_doc` |
| `partants_enrichis` | 185 | `id` | `idx_enrichis_date`, `idx_enrichis_cheval` |
| `rep_documents` | 45 | `id` | `idx_rep_doc` |
| `resultats` | 939 | `id` | `idx_resultats_date`, `idx_resultats_doc` |

### 2.2 Colonnes

**`api_cotes`** — 27 243 lignes

| Colonne | Type | NOT NULL | PK | Taux de nullité | Distinct | Exemples |
|---|---|---|---|---:|---:|---|
| `id` | INTEGER | non | oui | 0.0 % | 27 243 | `1`, `2`, `3` |
| `course_id` | TEXT | non | non | 0.0 % | 407 | `05092026_R1_C1`, `05092026_R1_C2`, `05092026_R1_C3` |
| `type_pari` | TEXT | non | non | 0.0 % | 15 | `E_SIMPLE_GAGNANT`, `E_DEUX_SUR_QUATRE`, `E_TRIO` |
| `numero` | INTEGER | non | non | 100.0 % | 0 | — |
| `cote_directe` | REAL | non | non | 100.0 % | 0 | — |
| `masse_enjeu` | INTEGER | non | non | 100.0 % | 0 | — |
| `cote_reference` | REAL | non | non | 100.0 % | 0 | — |
| `evolution_cote` | REAL | non | non | 100.0 % | 0 | — |
| `risque` | REAL | non | non | 100.0 % | 0 | — |
| `updatetime` | TEXT | non | non | 0.0 % | 702 | `1788607420000`, `1788607440000`, `1788609690000` |
| `synced_at` | DATETIME | non | non | 0.0 % | 407 | `2026-09-12 17:49:41`, `2026-09-12 17:49:43`, `2026-09-12 17:49:44` |

**`api_courses`** — 407 lignes

| Colonne | Type | NOT NULL | PK | Taux de nullité | Distinct | Exemples |
|---|---|---|---|---:|---:|---|
| `course_id` | TEXT | non | oui | 0.0 % | 407 | `05092026_R1_C1`, `05092026_R1_C2`, `05092026_R1_C3` |
| `date` | TEXT | non | non | 0.0 % | 7 | `05092026`, `06092026`, `07092026` |
| `reunion` | INTEGER | non | non | 0.0 % | 13 | `1`, `2`, `3` |
| `course_num` | INTEGER | non | non | 0.0 % | 12 | `1`, `2`, `3` |
| `hippodrome_code` | TEXT | non | non | 100.0 % | 0 | — |
| `hippodrome_nom` | TEXT | non | non | 100.0 % | 0 | — |
| `discipline` | TEXT | non | non | 0.0 % | 6 | `ATTELE`, `MONTE`, `PLAT` |
| `distance` | INTEGER | non | non | 0.0 % | 62 | `2175`, `2100`, `2700` |
| `type_course` | TEXT | non | non | 0.0 % | 4 | `TROT_ATTELE`, `TROT_MONTE`, `PLAT` |
| `titre` | TEXT | non | non | 0.0 % | 392 | `PRIX JOSEPH AVELINE`, `PRIX DE LUSIGNY`, `PRIX DE BEZIERS` |
| `heure_depart` | TEXT | non | non | 0.0 % | 259 | `13:23`, `13:58`, `14:33` |
| `partants_declares` | INTEGER | non | non | 0.0 % | 16 | `10`, `13`, `14` |
| `partants_effectifs` | INTEGER | non | non | 0.0 % | 1 | `0` |
| `data_json` | TEXT | non | non | 0.0 % | 407 | `{"cached": false, "departImminent": false, "arri`, `{"cached": false, "departImminent": false, "arri`, `{"cached": false, "departImminent": false, "arri` |
| `synced_at` | DATETIME | non | non | 0.0 % | 7 | `2026-09-12 17:49:41`, `2026-09-12 17:51:07`, `2026-09-12 17:52:46` |

**`api_ecuries`** — 2 lignes

| Colonne | Type | NOT NULL | PK | Taux de nullité | Distinct | Exemples |
|---|---|---|---|---:|---:|---|
| `id` | INTEGER | non | oui | 0.0 % | 2 | `1`, `4` |
| `nom` | TEXT | non | non | 0.0 % | 2 | `A`, `B` |
| `casaque_url` | TEXT | non | non | 100.0 % | 0 | — |
| `data_json` | TEXT | non | non | 0.0 % | 2 | `{"nom": "A"}`, `{"nom": "B"}` |

**`api_meteo`** — 0 lignes

| Colonne | Type | NOT NULL | PK | Taux de nullité | Distinct | Exemples |
|---|---|---|---|---:|---:|---|
| `id` | INTEGER | non | oui | — | 0 | — |
| `date` | TEXT | oui | non | — | 0 | — |
| `hippodrome_code` | TEXT | oui | non | — | 0 | — |
| `temperature` | REAL | non | non | — | 0 | — |
| `vent_force` | REAL | non | non | — | 0 | — |
| `vent_direction` | TEXT | non | non | — | 0 | — |
| `nebulosite_code` | INTEGER | non | non | — | 0 | — |
| `condition` | TEXT | non | non | — | 0 | — |
| `terrain` | TEXT | non | non | — | 0 | — |
| `data_json` | TEXT | non | non | — | 0 | — |

**`api_partants`** — 0 lignes

| Colonne | Type | NOT NULL | PK | Taux de nullité | Distinct | Exemples |
|---|---|---|---|---:|---:|---|
| `id` | INTEGER | non | oui | — | 0 | — |
| `course_id` | TEXT | oui | non | — | 0 | — |
| `numero_pmu` | INTEGER | non | non | — | 0 | — |
| `nom` | TEXT | non | non | — | 0 | — |
| `age` | INTEGER | non | non | — | 0 | — |
| `sexe` | TEXT | non | non | — | 0 | — |
| `race` | TEXT | non | non | — | 0 | — |
| `statut` | TEXT | non | non | — | 0 | — |
| `corde` | INTEGER | non | non | — | 0 | — |
| `oeilleres` | TEXT | non | non | — | 0 | — |
| `proprietaire` | TEXT | non | non | — | 0 | — |
| `entraineur` | TEXT | non | non | — | 0 | — |
| `deferre` | TEXT | non | non | — | 0 | — |
| `driver` | TEXT | non | non | — | 0 | — |
| `driver_change` | BOOLEAN | non | non | — | 0 | — |
| `musique` | TEXT | non | non | — | 0 | — |
| `nb_courses` | INTEGER | non | non | — | 0 | — |
| `nb_victoires` | INTEGER | non | non | — | 0 | — |
| `nb_places` | INTEGER | non | non | — | 0 | — |
| `gains_carriere` | INTEGER | non | non | — | 0 | — |
| `pere` | TEXT | non | non | — | 0 | — |
| `mere` | TEXT | non | non | — | 0 | — |
| `ordre_arrivee` | INTEGER | non | non | — | 0 | — |
| `engagement` | TEXT | non | non | — | 0 | — |
| `supplement` | BOOLEAN | non | non | — | 0 | — |
| `handicap_distance` | INTEGER | non | non | — | 0 | — |
| `poids` | INTEGER | non | non | — | 0 | — |
| `temps_obtenu` | TEXT | non | non | — | 0 | — |
| `reduction_km` | TEXT | non | non | — | 0 | — |
| `dernier_rapport_direct` | REAL | non | non | — | 0 | — |
| `dernier_rapport_reference` | REAL | non | non | — | 0 | — |
| `avis_entraineur` | TEXT | non | non | — | 0 | — |
| `data_json` | TEXT | non | non | — | 0 | — |

**`api_pronostics`** — 407 lignes

| Colonne | Type | NOT NULL | PK | Taux de nullité | Distinct | Exemples |
|---|---|---|---|---:|---:|---|
| `id` | INTEGER | non | oui | 0.0 % | 407 | `1`, `2`, `3` |
| `course_id` | TEXT | non | non | 0.0 % | 407 | `05092026_R1_C1`, `05092026_R1_C2`, `05092026_R1_C3` |
| `source` | TEXT | non | non | 0.0 % | 1 | `DATAHIPPIQUE` |
| `pronostics` | TEXT | non | non | 0.0 % | 407 | `{"prono_pmu_fr": {"selection": [{"cote_prob": "3`, `{"prono_pmu_fr": {"selection": [{"cote_prob": "3`, `{"prono_pmu_fr": {"selection": [{"cote_prob": "3` |
| `nb_partants` | INTEGER | non | non | 0.0 % | 16 | `10`, `13`, `14` |
| `data_json` | TEXT | non | non | 0.0 % | 407 | `{"nom_prix": "PRIX JOSEPH AVELINE", "id_nav_cour`, `{"nom_prix": "PRIX DE LUSIGNY", "id_nav_course":`, `{"nom_prix": "PRIX DE BEZIERS", "id_nav_course":` |

**`api_rapports`** — 2 492 lignes

| Colonne | Type | NOT NULL | PK | Taux de nullité | Distinct | Exemples |
|---|---|---|---|---:|---:|---|
| `id` | INTEGER | non | oui | 0.0 % | 2 492 | `1`, `2`, `3` |
| `course_id` | TEXT | non | non | 0.0 % | 407 | `05092026_R1_C1`, `05092026_R1_C2`, `05092026_R1_C3` |
| `type_pari` | TEXT | non | non | 0.0 % | 19 | `E_COUPLE_GAGNANT`, `E_COUPLE_PLACE`, `E_DEUX_SUR_QUATRE` |
| `arrivee` | TEXT | non | non | 0.0 % | 1 | `[]` |
| `arrivee_consolidee` | TEXT | non | non | 0.0 % | 1 | `[]` |
| `gains_base` | REAL | non | non | 100.0 % | 0 | — |
| `gains_ordre` | REAL | non | non | 100.0 % | 0 | — |
| `gains_desordre` | REAL | non | non | 100.0 % | 0 | — |
| `nb_gagnants` | INTEGER | non | non | 100.0 % | 0 | — |
| `masse_partager` | REAL | non | non | 100.0 % | 0 | — |
| `rapports_consolides` | TEXT | non | non | 0.0 % | 1 | `[]` |
| `risques` | TEXT | non | non | 0.0 % | 1 | `[]` |
| `data_json` | TEXT | non | non | 0.0 % | 2 457 | `{"typePari": "E_SIMPLE_GAGNANT", "miseBase": 100`, `{"typePari": "E_SIMPLE_PLACE", "miseBase": 100, `, `{"typePari": "E_COUPLE_GAGNANT", "miseBase": 100` |

**`classements`** — 1 lignes

| Colonne | Type | NOT NULL | PK | Taux de nullité | Distinct | Exemples |
|---|---|---|---|---:|---:|---|
| `id` | INTEGER | non | oui | 0.0 % | 1 | `1` |
| `document_id` | INTEGER | oui | non | 0.0 % | 1 | `393` |
| `course_id` | TEXT | oui | non | 0.0 % | 1 | `` |
| `forme` | TEXT | non | non | 0.0 % | 1 | `[]` |
| `classe` | TEXT | non | non | 0.0 % | 1 | `[]` |
| `progres` | TEXT | non | non | 0.0 % | 1 | `[]` |
| `regularite` | TEXT | non | non | 0.0 % | 1 | `[]` |

**`commentaires`** — 14 015 lignes

| Colonne | Type | NOT NULL | PK | Taux de nullité | Distinct | Exemples |
|---|---|---|---|---:|---:|---|
| `id` | INTEGER | non | oui | 0.0 % | 14 015 | `1`, `2`, `3` |
| `document_id` | INTEGER | oui | non | 0.0 % | 896 | `1`, `2`, `3` |
| `course_id` | TEXT | oui | non | 0.0 % | 577 | ``, `JH_21-01-2024`, `JH_22-01-2024` |
| `numero_cheval` | INTEGER | oui | non | 0.0 % | 20 | `1`, `2`, `3` |
| `texte` | TEXT | non | non | 0.0 % | 13 983 | `SHINNING OCEAN : Dominé en novembre par RAKAN (1`, `ZAYA DE LA PLATA : Cette jument de Thierry Taill`, `PEDRITO : Lauréat d'un gros handicap lors de la ` |

**`courses`** — 929 lignes

| Colonne | Type | NOT NULL | PK | Taux de nullité | Distinct | Exemples |
|---|---|---|---|---:|---:|---|
| `id` | INTEGER | non | oui | 0.0 % | 929 | `1`, `2`, `3` |
| `document_id` | INTEGER | oui | non | 0.0 % | 929 | `1`, `2`, `3` |
| `course_id` | TEXT | oui | non | 0.0 % | 605 | ``, `JH_21-01-2024`, `JH_22-01-2024` |
| `date` | TEXT | non | non | 0.0 % | 734 | `1995-07-18`, `2024-01-19`, `2024-01-20` |
| `reunion` | TEXT | non | non | 0.0 % | 1 | `` |
| `course_num` | INTEGER | non | non | 0.0 % | 10 | `0`, `4`, `2` |
| `hippodrome` | TEXT | non | non | 0.0 % | 86 | ``, `1`, `10` |
| `discipline` | TEXT | non | non | 0.0 % | 4 | `PLAT`, `ATTELE`, `` |
| `distance_raw` | TEXT | non | non | 0.0 % | 111 | `1300`, `25`, `3400` |
| `distance_m` | INTEGER | non | non | 0.2 % | 82 | `1300`, `25`, `3400` |
| `montant_raw` | TEXT | non | non | 0.0 % | 131 | `53 000`, `4500`, `58 000` |
| `montant_euros` | INTEGER | non | non | 0.5 % | 129 | `53000`, `4500`, `58000` |
| `partants_declares` | INTEGER | non | non | 0.0 % | 9 | `16`, `15`, `18` |
| `partants_effectifs` | INTEGER | non | non | 0.0 % | 8 | `15`, `14`, `13` |
| `type_course` | TEXT | non | non | 0.0 % | 3 | `HANDICAP`, ``, `AUTOSTART` |
| `titre` | TEXT | non | non | 0.0 % | 739 | `DEAUVILLE NOCTURNE - PRIX DU VOLCAN - PLAT`, `PARIS-VINCENNES - PRIX DE BREST - ATTELE`, `11 - FIFTY FIVE BOND : Excellent troisième du Pr` |
| `heure_depart` | TEXT | non | non | 0.0 % | 2 | ``, `18H 45mn` |
| `heure_arret_jeux` | TEXT | non | non | 0.0 % | 1 | `` |
| `raw_text` | TEXT | non | non | 100.0 % | 0 | — |

**`documents`** — 2 711 lignes

| Colonne | Type | NOT NULL | PK | Taux de nullité | Distinct | Exemples |
|---|---|---|---|---:|---:|---|
| `id` | INTEGER | non | oui | 0.0 % | 2 711 | `46`, `203`, `1400` |
| `filename` | TEXT | oui | non | 0.0 % | 2 711 | `19_06_2025_QUARTE.pdf`, `21_03_2026_TIERCE.pdf`, `25_03_2024_QUARTE.pdf` |
| `doc_type` | TEXT | oui | non | 0.0 % | 4 | `COURSE_EN_DIRECT`, `JOURNAL`, `REP` |
| `date_publication` | TEXT | non | non | 0.0 % | 935 | ``, `1995-07-18`, `2024-01-19` |
| `pages` | INTEGER | non | non | 0.0 % | 3 | `2`, `0`, `1` |
| `quality_score` | INTEGER | non | non | 100.0 % | 0 | — |
| `quality_status` | TEXT | non | non | 100.0 % | 0 | — |
| `parsing_errors` | TEXT | non | non | 0.0 % | 1 | `[]` |
| `created_at` | TIMESTAMP | non | non | 0.0 % | 1 | `2026-09-10 11:27:06` |

**`ecd_courses`** — 6 509 lignes

| Colonne | Type | NOT NULL | PK | Taux de nullité | Distinct | Exemples |
|---|---|---|---|---:|---:|---|
| `id` | INTEGER | non | oui | 0.0 % | 6 509 | `1`, `2`, `3` |
| `document_id` | INTEGER | oui | non | 0.0 % | 800 | `1914`, `1915`, `1916` |
| `course_id` | TEXT | oui | non | 0.0 % | 6 509 | `ECD_01-07-2026_R1_C1`, `ECD_01-07-2026_R1_C2`, `ECD_01-07-2026_R1_C3` |
| `numero_course` | INTEGER | non | non | 0.0 % | 9 | `1`, `2`, `3` |
| `arrivee_raw` | TEXT | non | non | 0.0 % | 5 862 | `10 950
69
0
0
0
0`, `5 350
162
0
0
0
0`, `62 550
14
0
0
0
0` |
| `arrivee_positions` | TEXT | non | non | 0.0 % | 5 862 | `[10, 950, 69, 0, 0, 0, 0]`, `[5, 350, 162, 0, 0, 0, 0]`, `[62, 550, 14, 0, 0, 0, 0]` |
| `gains_total_raw` | TEXT | non | non | 100.0 % | 0 | — |
| `gains_total_euros` | INTEGER | non | non | 100.0 % | 0 | — |
| `page_num` | INTEGER | non | non | 0.0 % | 2 | `1`, `2` |
| `y_position` | REAL | non | non | 0.0 % | 529 | `103.0`, `282.0`, `458.0` |
| `raw_text` | TEXT | non | non | 0.0 % | 6 501 | `1ère
3 - 8 - 7
8
550
3
3 - 7
3 050
105
7
550
2
8`, `2ième
9 - 5 - 7
5
0
0
9 - 7
1 200
311
7
0
0
5 - `, `3ième
11 - 5 - 10
5
700
5
11 - 10
4 500
103
10
1` |

**`ecd_documents`** — 800 lignes

| Colonne | Type | NOT NULL | PK | Taux de nullité | Distinct | Exemples |
|---|---|---|---|---:|---:|---|
| `id` | INTEGER | non | oui | 0.0 % | 800 | `1`, `2`, `3` |
| `document_id` | INTEGER | oui | non | 0.0 % | 800 | `1914`, `1915`, `1916` |
| `date` | TEXT | non | non | 0.0 % | 401 | `2026-07-01`, `2025-08-01`, `2026-08-01` |
| `reunion` | TEXT | non | non | 0.0 % | 5 | `1`, `3`, `4` |
| `hippodrome` | TEXT | non | non | 0.0 % | 72 | `ENGHIEN`, `NANTES`, `CABOURG` |
| `discipline` | TEXT | non | non | 100.0 % | 0 | — |
| `date_heure_extraction` | TEXT | non | non | 100.0 % | 0 | — |
| `raw_text` | TEXT | non | non | 0.0 % | 799 | `PARI
N°
MONTANT
NB
PARI
N°
MONTANT NB
GAGNANT
3
`, `PARI
N°
MONTANT
NB
PARI
N°
MONTANT NB
GAGNANT
5
`, `PARI
N°
MONTANT
NB
PARI
N°
MONTANT NB
GAGNANT
10` |

**`ecd_paris`** — 11 879 lignes

| Colonne | Type | NOT NULL | PK | Taux de nullité | Distinct | Exemples |
|---|---|---|---|---:|---:|---|
| `id` | INTEGER | non | oui | 0.0 % | 11 879 | `1`, `2`, `3` |
| `ecd_course_id` | INTEGER | oui | non | 0.0 % | 4 918 | `1`, `2`, `3` |
| `type_pari` | TEXT | non | non | 0.0 % | 2 | `GAGNANT`, `JUM GAGNANT` |
| `combinaison_raw` | TEXT | non | non | 0.0 % | 242 | ``, `9 - 5`, `4 - 9` |
| `combinaison_normalized` | TEXT | non | non | 0.0 % | 242 | `[]`, `[9, 5]`, `[4, 9]` |
| `montant_raw` | TEXT | non | non | 0.0 % | 455 | `0`, `800`, `11` |
| `montant_euros` | INTEGER | non | non | 16.9 % | 208 | `0`, `800`, `11` |
| `nb_paris` | INTEGER | non | non | 26.3 % | 240 | `0`, `2`, `4` |
| `position` | TEXT | non | non | 100.0 % | 0 | — |
| `uncertain` | BOOLEAN | non | non | 0.0 % | 1 | `0` |

**`media_selections`** — 0 lignes

| Colonne | Type | NOT NULL | PK | Taux de nullité | Distinct | Exemples |
|---|---|---|---|---:|---:|---|
| `id` | INTEGER | non | oui | — | 0 | — |
| `document_id` | INTEGER | oui | non | — | 0 | — |
| `course_id` | TEXT | oui | non | — | 0 | — |
| `source` | TEXT | non | non | — | 0 | — |
| `selection` | TEXT | non | non | — | 0 | — |
| `rang` | TEXT | non | non | — | 0 | — |

**`partants`** — 13 163 lignes

| Colonne | Type | NOT NULL | PK | Taux de nullité | Distinct | Exemples |
|---|---|---|---|---:|---:|---|
| `id` | INTEGER | non | oui | 0.0 % | 13 163 | `1`, `2`, `3` |
| `document_id` | INTEGER | oui | non | 0.0 % | 924 | `1`, `2`, `3` |
| `course_id` | TEXT | oui | non | 0.0 % | 603 | ``, `1995-07-18_11_C4`, `1995-07-18_12_C4` |
| `numero` | INTEGER | oui | non | 0.0 % | 20 | `1`, `2`, `3` |
| `nom_cheval_raw` | TEXT | non | non | 0.0 % | 4 890 | `SHINNING OCEAN`, `ZAYA DE LA PLATA`, `PEDRITO` |
| `nom_cheval_normalized` | TEXT | non | non | 0.0 % | 4 889 | `1 - C. ESCUDER`, `1 - M. SEROR`, `1 – R. DERIEUX` |
| `sexe` | TEXT | non | non | 0.0 % | 225 | `M.7`, `F.7`, `H.5` |
| `age` | TEXT | non | non | 0.0 % | 11 | `7`, `5`, `4` |
| `poids` | TEXT | non | non | 0.0 % | 1 | `` |
| `corde` | TEXT | non | non | 0.0 % | 1 | `` |
| `distance_raw` | TEXT | non | non | 0.0 % | 179 | `8`, `4`, `6` |
| `distance_m` | INTEGER | non | non | 99.9 % | 4 | `15`, `2`, `55` |
| `chrono_raw` | TEXT | non | non | 0.0 % | 197 | `60.KG`, `59,5.KG`, `57,5.KG` |
| `chrono_normalized` | TEXT | non | non | 0.0 % | 197 | `60.KG`, `59,5.KG`, `57,5.KG` |
| `performances_raw` | TEXT | non | non | 0.0 % | 11 235 | `2.2.9.5.4`, `0.0.1.7.1`, `5.9.1.3.6` |
| `performances_structured` | TEXT | non | non | 0.0 % | 11 234 | `[2, 2, 9, 5, 4]`, `[0, 0, 1, 7, 1]`, `[5, 9, 1, 3, 6]` |
| `gains_raw` | TEXT | non | non | 0.0 % | 10 829 | `146 785`, `115 245`, `153 110` |
| `gains_euros` | INTEGER | non | non | 6.9 % | 9 740 | `146785`, `115245`, `153110` |
| `driver_raw` | TEXT | non | non | 0.0 % | 919 | `D.SANTIAGO`, `T.BLANCHOUIN`, `T.PICCONE` |
| `driver_normalized` | TEXT | non | non | 0.0 % | 917 | `D.SANTIAGO`, `T.BLANCHOUIN`, `T.PICCONE` |
| `entraineur_raw` | TEXT | non | non | 0.0 % | 1 469 | `H.BLUME`, `J.BOISNARD`, `HA.PANTALL` |
| `entraineur_normalized` | TEXT | non | non | 0.0 % | 1 466 | `H.BLUME`, `J.BOISNARD`, `HA.PANTALL` |
| `proprietaire_raw` | TEXT | non | non | 0.0 % | 4 300 | `Y.MARIE-NELLY`, `T.TAILLEUR`, `HA.PANTALL` |
| `proprietaire_normalized` | TEXT | non | non | 0.0 % | 4 296 | `Y.MARIE-NELLY`, `T.TAILLEUR`, `HA.PANTALL` |
| `cote_raw` | TEXT | non | non | 0.0 % | 141 | `35/1`, `39/1`, `26/1` |
| `cote_decimale` | REAL | non | non | 2.1 % | 140 | `35.0`, `39.0`, `26.0` |
| `commentaire` | TEXT | non | non | 0.0 % | 12 682 | `SHINNING OCEAN : Dominé en novembre par RAKAN (1`, `ZAYA DE LA PLATA : Cette jument de Thierry Taill`, `PEDRITO : Lauréat d'un gros handicap lors de la ` |
| `raw_data` | TEXT | non | non | 0.0 % | 13 121 | `{"450": "TURF", "600": "34/1   41/1   24/1  11/1`, `{"440": "MAGAZINE\nPARIS", "30": "2", "70": "ZAY`, `{"440": "TIERCE", "600": "35/1   39/1  26/1    9` |

**`partants_enrichis`** — 185 lignes

| Colonne | Type | NOT NULL | PK | Taux de nullité | Distinct | Exemples |
|---|---|---|---|---:|---:|---|
| `id` | INTEGER | non | oui | 0.0 % | 185 | `35`, `36`, `37` |
| `document_id` | INTEGER | non | non | 0.0 % | 12 | `124`, `5`, `18` |
| `nom_cheval_normalized` | TEXT | oui | non | 0.0 % | 103 | `AETOS KRONOS`, `ALWAYS EK`, `AMPIA MEDE SM` |
| `date_course` | TEXT | oui | non | 0.0 % | 12 | `2024-01-28`, `2024-02-09`, `2024-02-11` |
| `reunion_num` | INTEGER | non | non | 0.0 % | 1 | `1` |
| `course_num` | INTEGER | non | non | 0.0 % | 6 | `4`, `7`, `3` |
| `numero_pmu` | INTEGER | non | non | 0.0 % | 18 | `1`, `2`, `3` |
| `deferre` | TEXT | non | non | 9.7 % | 7 | `DEFERRE_ANTERIEURS_POSTERIEURS`, `PROTEGE_ANTERIEURS`, `PROTEGE_ANTERIEURS_DEFERRRE_POSTERIEURS` |
| `musique_officielle` | TEXT | non | non | 0.0 % | 185 | `DA3A0A235A1A6ADA2A3M`, `1A6ADM7A2A231A8A0A0A`, `0A9A2A4ADA232A2A3A2A` |
| `nom_pere` | TEXT | non | non | 0.0 % | 72 | `NIKY`, `LUDO DE CASTELLE`, `LOOK DE STAR` |
| `nom_mere` | TEXT | non | non | 0.0 % | 101 | `ABRICOTINE`, `SILICE D'HERFRAIE`, `PERLE D'AVRIL` |
| `nom_pere_mere` | TEXT | non | non | 100.0 % | 0 | — |
| `race` | TEXT | non | non | 0.0 % | 2 | `TROTTEUR FRANCAIS`, `TROTTEUR ETRANGER` |
| `robe` | TEXT | non | non | 0.0 % | 6 | `BAI CL`, `BAI`, `ALEZAN` |
| `oeilleres` | TEXT | non | non | 0.0 % | 1 | `SANS_OEILLERES` |
| `gains_carriere_euros` | INTEGER | non | non | 0.0 % | 170 | `315950`, `332400`, `334980` |
| `gains_annee_euros` | INTEGER | non | non | 0.0 % | 118 | `12600`, `49710`, `24750` |
| `gains_victoires_euros` | INTEGER | non | non | 0.0 % | 119 | `145350`, `211500`, `216900` |
| `taux_reclamation` | INTEGER | non | non | 100.0 % | 0 | — |
| `raw_api_data` | TEXT | non | non | 0.0 % | 185 | `{"nom": "GHOSTBUSTER", "numPmu": 1, "age": 8, "s`, `{"nom": "GUINESS D'HERFRAIE", "numPmu": 2, "age"`, `{"nom": "GOLD DAIRPET", "numPmu": 3, "age": 8, "` |
| `enriched_at` | TIMESTAMP | non | non | 0.0 % | 12 | `2026-09-11 22:18:05`, `2026-09-11 22:18:24`, `2026-09-11 22:18:26` |

**`rep_documents`** — 45 lignes

| Colonne | Type | NOT NULL | PK | Taux de nullité | Distinct | Exemples |
|---|---|---|---|---:|---:|---|
| `id` | INTEGER | non | oui | 0.0 % | 45 | `1`, `2`, `3` |
| `document_id` | INTEGER | oui | non | 0.0 % | 45 | `1869`, `1870`, `1871` |
| `document_type` | TEXT | non | non | 0.0 % | 1 | `REP` |
| `date_document` | TEXT | non | non | 0.0 % | 39 | `2024-05-24`, `2025-04-12`, `2025-05-10` |
| `date_document_raw` | TEXT | non | non | 0.0 % | 39 | `24/05/2024`, `12/04/2025`, `10/05/2025` |
| `date_course_cible` | TEXT | non | non | 0.0 % | 37 | `2024-05-28`, `2025-04-16`, `2025-05-14` |
| `date_course_cible_raw` | TEXT | non | non | 0.0 % | 37 | `MARDI 28/05/2024`, `MERCREDI 16/04/2025`, `MERCREDI 14/05/2025` |
| `game_type` | TEXT | non | non | 0.0 % | 2 | `4+1`, `` |
| `report_ordre_raw` | TEXT | non | non | 0.0 % | 38 | `46 776 739`, `48 421 054`, `` |
| `report_ordre_euros` | INTEGER | non | non | 15.6 % | 37 | `46776739`, `48421054`, `99712433` |
| `tierce_v_raw` | TEXT | non | non | 0.0 % | 1 | `` |
| `tierce_v_value` | INTEGER | non | non | 100.0 % | 0 | — |
| `raw_text` | TEXT | non | non | 0.0 % | 45 | `"4+1" DU MARDI 28 MAI 2024
AUTEUIL - PRIX ALADDI`, `AN XXIV - N° 43 955 - GRATUIT
Numéros clientèle `, `Numéros clientèle : 25 49 72 00 / 70 20 01 10
AN` |

**`resultats`** — 939 lignes

| Colonne | Type | NOT NULL | PK | Taux de nullité | Distinct | Exemples |
|---|---|---|---|---:|---:|---|
| `id` | INTEGER | non | oui | 0.0 % | 939 | `1`, `2`, `3` |
| `document_id` | INTEGER | oui | non | 0.0 % | 937 | `46`, `203`, `403` |
| `course_id` | TEXT | oui | non | 0.0 % | 921 | ``, `2025-03-31_QUARTE_R1`, `2024-02-09_4PLUS1_R1` |
| `date` | TEXT | non | non | 0.0 % | 919 | ``, `2024-02-09`, `2024-02-10` |
| `type_pari` | TEXT | non | non | 0.0 % | 4 | ``, `QUARTE`, `4+1` |
| `arrivee` | TEXT | non | non | 0.0 % | 908 | `[]`, `[6, 2, 1, 4, 10]`, `[7, 18, 6, 15, 17]` |
| `arrivee_complete` | TEXT | non | non | 0.0 % | 908 | `[]`, `[{"position": 1, "numero": 6}, {"position": 2, "`, `[{"position": 1, "numero": 7}, {"position": 2, "` |
| `npo` | INTEGER | non | non | 0.0 % | 19 | `0`, `12`, `10` |
| `np` | INTEGER | non | non | 0.0 % | 18 | `0`, `5`, `13` |
| `disqualifies` | TEXT | non | non | 0.0 % | 1 | `[]` |
| `non_partants` | TEXT | non | non | 0.0 % | 2 | `[]`, `[0, 0]` |
| `gains_ordre_raw` | TEXT | non | non | 0.0 % | 877 | ``, `17 352 500 
     
5`, `1 053 000 
       
101` |
| `gains_ordre_euros` | INTEGER | non | non | 1.4 % | 816 | `17352500`, `1053000`, `2692500` |
| `gains_desordre_raw` | TEXT | non | non | 0.0 % | 916 | ``, `127 500 F (156 G)
       24 000 F (407 G)
      `, `82 500 
            
1 199` |
| `gains_desordre_euros` | INTEGER | non | non | 1.4 % | 429 | `82500`, `21000`, `47000` |
| `gains_bonus_raw` | TEXT | non | non | 0.0 % | 425 | ``, `4 000 
              
7 417
MAP "4+1"  :
215 348`, `1 000 
              
16 596
MAP "4+1"  :
178 28` |
| `gains_bonus_euros` | INTEGER | non | non | 54.1 % | 73 | `4000`, `1000`, `2000` |
| `nb_gagnants_ordre` | INTEGER | non | non | 5.6 % | 338 | `5`, `101`, `23` |
| `nb_gagnants_desordre` | INTEGER | non | non | 1.3 % | 823 | `407`, `1199`, `2635` |
| `nb_gagnants_bonus` | INTEGER | non | non | 54.1 % | 418 | `7417`, `16596`, `16326` |
| `masse_partager_raw` | TEXT | non | non | 0.0 % | 2 | ``, `48 393 000` |
| `masse_partager_euros` | INTEGER | non | non | 99.9 % | 1 | `48393000` |
| `rapport_gagnant_raw` | TEXT | non | non | 0.0 % | 920 | ``, `Couplé Placé A       :
Couplé Placé B       :
Co`, `13 000 
            
1 709` |
| `rapport_gagnant_euros` | INTEGER | non | non | 1.0 % | 200 | `13000`, `5000`, `6500` |
| `rapport_place_a_raw` | TEXT | non | non | 0.0 % | 907 | ``, `4 000 
              
2 849`, `1 500 
              
6 675` |
| `rapport_place_a_euros` | INTEGER | non | non | 1.8 % | 68 | `4000`, `1500`, `3500` |
| `rapport_place_b_raw` | TEXT | non | non | 0.0 % | 912 | ``, `10 000 
            
1 109 
                    `, `2 000 
              
4 649 
                   ` |
| `rapport_place_b_euros` | INTEGER | non | non | 1.9 % | 79 | `10000`, `2000`, `4000` |
| `map_paris_raw` | TEXT | non | non | 0.0 % | 917 | ``, `55 593 000`, `48 390 500` |
| `map_paris_euros` | INTEGER | non | non | 1.0 % | 914 | `55593000`, `48390500`, `42675500` |
| `raw_text` | TEXT | non | non | 100.0 % | 0 | — |

### 2.3 Relations

| Source | Colonne | Cible | Origine |
|---|---|---|---|
| `api_cotes` | `course_id` | `courses` | inférée (nommage) |
| `api_courses` | `course_id` | `courses` | inférée (nommage) |
| `api_partants` | `course_id` | `courses` | inférée (nommage) |
| `api_pronostics` | `course_id` | `courses` | inférée (nommage) |
| `api_rapports` | `course_id` | `courses` | inférée (nommage) |
| `classements` | `course_id` | `courses` | inférée (nommage) |
| `classements` | `document_id` | `documents` | déclarée (FOREIGN KEY) |
| `commentaires` | `course_id` | `courses` | inférée (nommage) |
| `commentaires` | `document_id` | `documents` | déclarée (FOREIGN KEY) |
| `courses` | `document_id` | `documents` | déclarée (FOREIGN KEY) |
| `ecd_courses` | `course_id` | `courses` | inférée (nommage) |
| `ecd_courses` | `document_id` | `documents` | déclarée (FOREIGN KEY) |
| `ecd_documents` | `document_id` | `documents` | déclarée (FOREIGN KEY) |
| `ecd_paris` | `ecd_course_id` | `ecd_courses` | déclarée (FOREIGN KEY) |
| `media_selections` | `course_id` | `courses` | inférée (nommage) |
| `media_selections` | `document_id` | `documents` | déclarée (FOREIGN KEY) |
| `partants` | `course_id` | `courses` | inférée (nommage) |
| `partants` | `document_id` | `documents` | déclarée (FOREIGN KEY) |
| `partants_enrichis` | `document_id` | `documents` | déclarée (FOREIGN KEY) |
| `rep_documents` | `document_id` | `documents` | déclarée (FOREIGN KEY) |
| `resultats` | `course_id` | `courses` | inférée (nommage) |
| `resultats` | `document_id` | `documents` | déclarée (FOREIGN KEY) |

## 2. Base `debug.db`

- Taille : **20.0 Ko**
- SHA-256 : `86d4b5d2bb66fe73023e8bdf0d8f263b8edd4fcac0fd89e96b1c1869fa45fc6e`
- Vues : aucune

### 2.1 Tables et volumes

| Table | Lignes | Clé primaire | Index |
|---|---:|---|---|
| `documents` | 1 | `id` | — |
| `partants` | 1 | `id` | — |

### 2.2 Colonnes

**`documents`** — 1 lignes

| Colonne | Type | NOT NULL | PK | Taux de nullité | Distinct | Exemples |
|---|---|---|---|---:|---:|---|
| `id` | INTEGER | non | oui | 0.0 % | 1 | `1` |
| `filename` | TEXT | oui | non | 0.0 % | 1 | `test.pdf` |
| `doc_type` | TEXT | oui | non | 0.0 % | 1 | `JOURNAL` |
| `date_publication` | TEXT | non | non | 100.0 % | 0 | — |
| `pages` | INTEGER | non | non | 100.0 % | 0 | — |
| `quality_score` | INTEGER | non | non | 100.0 % | 0 | — |
| `quality_status` | TEXT | non | non | 100.0 % | 0 | — |
| `parsing_errors` | TEXT | non | non | 100.0 % | 0 | — |
| `created_at` | TIMESTAMP | non | non | 0.0 % | 1 | `2026-09-10 10:44:42` |

**`partants`** — 1 lignes

| Colonne | Type | NOT NULL | PK | Taux de nullité | Distinct | Exemples |
|---|---|---|---|---:|---:|---|
| `id` | INTEGER | non | oui | 0.0 % | 1 | `1` |
| `document_id` | INTEGER | oui | non | 0.0 % | 1 | `1` |
| `course_id` | TEXT | oui | non | 0.0 % | 1 | `` |
| `numero` | INTEGER | oui | non | 0.0 % | 1 | `1` |
| `nom_cheval_raw` | TEXT | non | non | 0.0 % | 1 | `SHINNING OCEAN` |
| `nom_cheval_normalized` | TEXT | non | non | 0.0 % | 1 | `SHINNING OCEAN` |
| `sexe` | TEXT | non | non | 0.0 % | 1 | `M.7` |
| `age` | TEXT | non | non | 0.0 % | 1 | `7` |
| `poids` | TEXT | non | non | 0.0 % | 1 | `` |
| `corde` | TEXT | non | non | 0.0 % | 1 | `` |
| `distance_raw` | TEXT | non | non | 0.0 % | 1 | `8` |
| `distance_m` | INTEGER | non | non | 100.0 % | 0 | — |
| `chrono_raw` | TEXT | non | non | 0.0 % | 1 | `60.KG` |
| `chrono_normalized` | TEXT | non | non | 0.0 % | 1 | `60.KG` |
| `performances_raw` | TEXT | non | non | 0.0 % | 1 | `2.2.9.5.4` |
| `performances_structured` | TEXT | non | non | 0.0 % | 1 | `[2, 2, 9, 5, 4]` |
| `gains_raw` | TEXT | non | non | 0.0 % | 1 | `146 785` |
| `gains_euros` | INTEGER | non | non | 0.0 % | 1 | `146785` |
| `driver_raw` | TEXT | non | non | 0.0 % | 1 | `D.SANTIAGO` |
| `driver_normalized` | TEXT | non | non | 0.0 % | 1 | `D.SANTIAGO` |
| `entraineur_raw` | TEXT | non | non | 0.0 % | 1 | `H.BLUME` |
| `entraineur_normalized` | TEXT | non | non | 0.0 % | 1 | `H.BLUME` |
| `proprietaire_raw` | TEXT | non | non | 0.0 % | 1 | `Y.MARIE-NELLY` |
| `proprietaire_normalized` | TEXT | non | non | 0.0 % | 1 | `Y.MARIE-NELLY` |
| `cote_raw` | TEXT | non | non | 0.0 % | 1 | `35/1` |
| `cote_decimale` | REAL | non | non | 0.0 % | 1 | `35.0` |
| `commentaire` | TEXT | non | non | 0.0 % | 1 | `comment` |
| `raw_data` | TEXT | non | non | 0.0 % | 1 | `{}` |

### 2.3 Relations

| Source | Colonne | Cible | Origine |
|---|---|---|---|
| `partants` | `document_id` | `documents` | déclarée (FOREIGN KEY) |

## 2. Base `debug2.db`

- Taille : **20.0 Ko**
- SHA-256 : `d06ba9a6007741d35b44e7d218610626d0b22f0f311d609659f4d71e00272bac`
- Vues : aucune

### 2.1 Tables et volumes

| Table | Lignes | Clé primaire | Index |
|---|---:|---|---|
| `documents` | 1 | `id` | — |
| `partants` | 1 | `id` | — |

### 2.2 Colonnes

**`documents`** — 1 lignes

| Colonne | Type | NOT NULL | PK | Taux de nullité | Distinct | Exemples |
|---|---|---|---|---:|---:|---|
| `id` | INTEGER | non | oui | 0.0 % | 1 | `1` |
| `filename` | TEXT | oui | non | 0.0 % | 1 | `test.pdf` |
| `doc_type` | TEXT | oui | non | 0.0 % | 1 | `JOURNAL` |
| `date_publication` | TEXT | non | non | 100.0 % | 0 | — |
| `pages` | INTEGER | non | non | 100.0 % | 0 | — |
| `quality_score` | INTEGER | non | non | 100.0 % | 0 | — |
| `quality_status` | TEXT | non | non | 100.0 % | 0 | — |
| `parsing_errors` | TEXT | non | non | 100.0 % | 0 | — |
| `created_at` | TIMESTAMP | non | non | 0.0 % | 1 | `2026-09-10 10:45:12` |

**`partants`** — 1 lignes

| Colonne | Type | NOT NULL | PK | Taux de nullité | Distinct | Exemples |
|---|---|---|---|---:|---:|---|
| `id` | INTEGER | non | oui | 0.0 % | 1 | `1` |
| `document_id` | INTEGER | oui | non | 0.0 % | 1 | `1` |
| `course_id` | TEXT | oui | non | 0.0 % | 1 | `` |
| `numero` | INTEGER | oui | non | 0.0 % | 1 | `1` |
| `nom_cheval_raw` | TEXT | non | non | 0.0 % | 1 | `SHINNING OCEAN` |
| `nom_cheval_normalized` | TEXT | non | non | 0.0 % | 1 | `SHINNING OCEAN` |
| `sexe` | TEXT | non | non | 0.0 % | 1 | `M.7` |
| `age` | TEXT | non | non | 0.0 % | 1 | `7` |
| `poids` | TEXT | non | non | 0.0 % | 1 | `` |
| `corde` | TEXT | non | non | 0.0 % | 1 | `` |
| `distance_raw` | TEXT | non | non | 0.0 % | 1 | `8` |
| `distance_m` | INTEGER | non | non | 100.0 % | 0 | — |
| `chrono_raw` | TEXT | non | non | 0.0 % | 1 | `60.KG` |
| `chrono_normalized` | TEXT | non | non | 0.0 % | 1 | `60.KG` |
| `performances_raw` | TEXT | non | non | 0.0 % | 1 | `2.2.9.5.4` |
| `performances_structured` | TEXT | non | non | 0.0 % | 1 | `[2, 2, 9, 5, 4]` |
| `gains_raw` | TEXT | non | non | 0.0 % | 1 | `146 785` |
| `gains_euros` | INTEGER | non | non | 0.0 % | 1 | `146785` |
| `driver_raw` | TEXT | non | non | 0.0 % | 1 | `D.SANTIAGO` |
| `driver_normalized` | TEXT | non | non | 0.0 % | 1 | `D.SANTIAGO` |
| `entraineur_raw` | TEXT | non | non | 0.0 % | 1 | `H.BLUME` |
| `entraineur_normalized` | TEXT | non | non | 0.0 % | 1 | `H.BLUME` |
| `proprietaire_raw` | TEXT | non | non | 0.0 % | 1 | `Y.MARIE-NELLY` |
| `proprietaire_normalized` | TEXT | non | non | 0.0 % | 1 | `Y.MARIE-NELLY` |
| `cote_raw` | TEXT | non | non | 0.0 % | 1 | `35/1` |
| `cote_decimale` | REAL | non | non | 0.0 % | 1 | `35.0` |
| `commentaire` | TEXT | non | non | 0.0 % | 1 | `comment` |
| `raw_data` | TEXT | non | non | 0.0 % | 1 | `{}` |

### 2.3 Relations

| Source | Colonne | Cible | Origine |
|---|---|---|---|
| `partants` | `document_id` | `documents` | déclarée (FOREIGN KEY) |

## 2. Base `test.db`

- Taille : **12.0 Ko**
- SHA-256 : `2153925f29051d9d7b3ac7f0453e92e1c9657cf0e91d927eac9720e1fe19866e`
- Vues : aucune

### 2.1 Tables et volumes

| Table | Lignes | Clé primaire | Index |
|---|---:|---|---|
| `partants` | 0 | `id` | — |

### 2.2 Colonnes

**`partants`** — 0 lignes

| Colonne | Type | NOT NULL | PK | Taux de nullité | Distinct | Exemples |
|---|---|---|---|---:|---:|---|
| `id` | INTEGER | non | oui | — | 0 | — |
| `document_id` | INTEGER | oui | non | — | 0 | — |
| `course_id` | TEXT | oui | non | — | 0 | — |
| `numero` | INTEGER | oui | non | — | 0 | — |
| `nom_cheval_raw` | TEXT | non | non | — | 0 | — |
| `nom_cheval_normalized` | TEXT | non | non | — | 0 | — |
| `sexe` | TEXT | non | non | — | 0 | — |
| `age` | TEXT | non | non | — | 0 | — |
| `poids` | TEXT | non | non | — | 0 | — |
| `corde` | TEXT | non | non | — | 0 | — |
| `distance_raw` | TEXT | non | non | — | 0 | — |
| `distance_m` | INTEGER | non | non | — | 0 | — |
| `chrono_raw` | TEXT | non | non | — | 0 | — |
| `chrono_normalized` | TEXT | non | non | — | 0 | — |
| `performances_raw` | TEXT | non | non | — | 0 | — |
| `performances_structured` | TEXT | non | non | — | 0 | — |
| `gains_raw` | TEXT | non | non | — | 0 | — |
| `gains_euros` | INTEGER | non | non | — | 0 | — |
| `driver_raw` | TEXT | non | non | — | 0 | — |
| `driver_normalized` | TEXT | non | non | — | 0 | — |
| `entraineur_raw` | TEXT | non | non | — | 0 | — |
| `entraineur_normalized` | TEXT | non | non | — | 0 | — |
| `proprietaire_raw` | TEXT | non | non | — | 0 | — |
| `proprietaire_normalized` | TEXT | non | non | — | 0 | — |
| `cote_raw` | TEXT | non | non | — | 0 | — |
| `cote_decimale` | REAL | non | non | — | 0 | — |
| `commentaire` | TEXT | non | non | — | 0 | — |
| `raw_data` | TEXT | non | non | — | 0 | — |

### 2.3 Relations

_Aucune relation détectée._

## 2. Base `test2.db`

- Taille : **12.0 Ko**
- SHA-256 : `2153925f29051d9d7b3ac7f0453e92e1c9657cf0e91d927eac9720e1fe19866e`
- Vues : aucune

### 2.1 Tables et volumes

| Table | Lignes | Clé primaire | Index |
|---|---:|---|---|
| `partants` | 0 | `id` | — |

### 2.2 Colonnes

**`partants`** — 0 lignes

| Colonne | Type | NOT NULL | PK | Taux de nullité | Distinct | Exemples |
|---|---|---|---|---:|---:|---|
| `id` | INTEGER | non | oui | — | 0 | — |
| `document_id` | INTEGER | oui | non | — | 0 | — |
| `course_id` | TEXT | oui | non | — | 0 | — |
| `numero` | INTEGER | oui | non | — | 0 | — |
| `nom_cheval_raw` | TEXT | non | non | — | 0 | — |
| `nom_cheval_normalized` | TEXT | non | non | — | 0 | — |
| `sexe` | TEXT | non | non | — | 0 | — |
| `age` | TEXT | non | non | — | 0 | — |
| `poids` | TEXT | non | non | — | 0 | — |
| `corde` | TEXT | non | non | — | 0 | — |
| `distance_raw` | TEXT | non | non | — | 0 | — |
| `distance_m` | INTEGER | non | non | — | 0 | — |
| `chrono_raw` | TEXT | non | non | — | 0 | — |
| `chrono_normalized` | TEXT | non | non | — | 0 | — |
| `performances_raw` | TEXT | non | non | — | 0 | — |
| `performances_structured` | TEXT | non | non | — | 0 | — |
| `gains_raw` | TEXT | non | non | — | 0 | — |
| `gains_euros` | INTEGER | non | non | — | 0 | — |
| `driver_raw` | TEXT | non | non | — | 0 | — |
| `driver_normalized` | TEXT | non | non | — | 0 | — |
| `entraineur_raw` | TEXT | non | non | — | 0 | — |
| `entraineur_normalized` | TEXT | non | non | — | 0 | — |
| `proprietaire_raw` | TEXT | non | non | — | 0 | — |
| `proprietaire_normalized` | TEXT | non | non | — | 0 | — |
| `cote_raw` | TEXT | non | non | — | 0 | — |
| `cote_decimale` | REAL | non | non | — | 0 | — |
| `commentaire` | TEXT | non | non | — | 0 | — |
| `raw_data` | TEXT | non | non | — | 0 | — |

### 2.3 Relations

_Aucune relation détectée._

## 2. Base `test3.db`

- Taille : **12.0 Ko**
- SHA-256 : `2153925f29051d9d7b3ac7f0453e92e1c9657cf0e91d927eac9720e1fe19866e`
- Vues : aucune

### 2.1 Tables et volumes

| Table | Lignes | Clé primaire | Index |
|---|---:|---|---|
| `partants` | 0 | `id` | — |

### 2.2 Colonnes

**`partants`** — 0 lignes

| Colonne | Type | NOT NULL | PK | Taux de nullité | Distinct | Exemples |
|---|---|---|---|---:|---:|---|
| `id` | INTEGER | non | oui | — | 0 | — |
| `document_id` | INTEGER | oui | non | — | 0 | — |
| `course_id` | TEXT | oui | non | — | 0 | — |
| `numero` | INTEGER | oui | non | — | 0 | — |
| `nom_cheval_raw` | TEXT | non | non | — | 0 | — |
| `nom_cheval_normalized` | TEXT | non | non | — | 0 | — |
| `sexe` | TEXT | non | non | — | 0 | — |
| `age` | TEXT | non | non | — | 0 | — |
| `poids` | TEXT | non | non | — | 0 | — |
| `corde` | TEXT | non | non | — | 0 | — |
| `distance_raw` | TEXT | non | non | — | 0 | — |
| `distance_m` | INTEGER | non | non | — | 0 | — |
| `chrono_raw` | TEXT | non | non | — | 0 | — |
| `chrono_normalized` | TEXT | non | non | — | 0 | — |
| `performances_raw` | TEXT | non | non | — | 0 | — |
| `performances_structured` | TEXT | non | non | — | 0 | — |
| `gains_raw` | TEXT | non | non | — | 0 | — |
| `gains_euros` | INTEGER | non | non | — | 0 | — |
| `driver_raw` | TEXT | non | non | — | 0 | — |
| `driver_normalized` | TEXT | non | non | — | 0 | — |
| `entraineur_raw` | TEXT | non | non | — | 0 | — |
| `entraineur_normalized` | TEXT | non | non | — | 0 | — |
| `proprietaire_raw` | TEXT | non | non | — | 0 | — |
| `proprietaire_normalized` | TEXT | non | non | — | 0 | — |
| `cote_raw` | TEXT | non | non | — | 0 | — |
| `cote_decimale` | REAL | non | non | — | 0 | — |
| `commentaire` | TEXT | non | non | — | 0 | — |
| `raw_data` | TEXT | non | non | — | 0 | — |

### 2.3 Relations

_Aucune relation détectée._

## 2. Base `test4.db`

- Taille : **12.0 Ko**
- SHA-256 : `bbaf7b71880ea8adb16edea3c098b93d0e452c35154ae61c4bb7d6af35a47339`
- Vues : aucune

### 2.1 Tables et volumes

| Table | Lignes | Clé primaire | Index |
|---|---:|---|---|
| `partants` | 0 | `id` | — |

### 2.2 Colonnes

**`partants`** — 0 lignes

| Colonne | Type | NOT NULL | PK | Taux de nullité | Distinct | Exemples |
|---|---|---|---|---:|---:|---|
| `id` | INTEGER | non | oui | — | 0 | — |
| `document_id` | INTEGER | oui | non | — | 0 | — |
| `course_id` | TEXT | non | non | — | 0 | — |
| `numero` | INTEGER | oui | non | — | 0 | — |
| `nom_cheval_raw` | TEXT | non | non | — | 0 | — |
| `nom_cheval_normalized` | TEXT | non | non | — | 0 | — |
| `sexe` | TEXT | non | non | — | 0 | — |
| `age` | TEXT | non | non | — | 0 | — |
| `poids` | TEXT | non | non | — | 0 | — |
| `corde` | TEXT | non | non | — | 0 | — |
| `distance_raw` | TEXT | non | non | — | 0 | — |
| `distance_m` | INTEGER | non | non | — | 0 | — |
| `chrono_raw` | TEXT | non | non | — | 0 | — |
| `chrono_normalized` | TEXT | non | non | — | 0 | — |
| `performances_raw` | TEXT | non | non | — | 0 | — |
| `performances_structured` | TEXT | non | non | — | 0 | — |
| `gains_raw` | TEXT | non | non | — | 0 | — |
| `gains_euros` | INTEGER | non | non | — | 0 | — |
| `driver_raw` | TEXT | non | non | — | 0 | — |
| `driver_normalized` | TEXT | non | non | — | 0 | — |
| `entraineur_raw` | TEXT | non | non | — | 0 | — |
| `entraineur_normalized` | TEXT | non | non | — | 0 | — |
| `proprietaire_raw` | TEXT | non | non | — | 0 | — |
| `proprietaire_normalized` | TEXT | non | non | — | 0 | — |
| `cote_raw` | TEXT | non | non | — | 0 | — |
| `cote_decimale` | REAL | non | non | — | 0 | — |
| `commentaire` | TEXT | non | non | — | 0 | — |
| `raw_data` | TEXT | non | non | — | 0 | — |

### 2.3 Relations

_Aucune relation détectée._

## 2. Base `test5.db`

- Taille : **12.0 Ko**
- SHA-256 : `3c7dbbf00631b49ad53582ea5cd0e85a466bd3096ac202089747d018cfb1fb55`
- Vues : aucune

### 2.1 Tables et volumes

| Table | Lignes | Clé primaire | Index |
|---|---:|---|---|
| `partants` | 1 | `id` | — |

### 2.2 Colonnes

**`partants`** — 1 lignes

| Colonne | Type | NOT NULL | PK | Taux de nullité | Distinct | Exemples |
|---|---|---|---|---:|---:|---|
| `id` | INTEGER | non | oui | 0.0 % | 1 | `1` |
| `document_id` | INTEGER | oui | non | 0.0 % | 1 | `1` |
| `course_id` | TEXT | non | non | 0.0 % | 1 | `` |
| `numero` | INTEGER | oui | non | 0.0 % | 1 | `1` |

### 2.3 Relations

_Aucune relation détectée._

## 2. Base `test6.db`

- Taille : **12.0 Ko**
- SHA-256 : `0c961e24ae343b833611abd40e7bff111a2cc014aa7f17795cb82a5c169cfc12`
- Vues : aucune

### 2.1 Tables et volumes

| Table | Lignes | Clé primaire | Index |
|---|---:|---|---|
| `partants` | 11 | `id` | — |

### 2.2 Colonnes

**`partants`** — 11 lignes

| Colonne | Type | NOT NULL | PK | Taux de nullité | Distinct | Exemples |
|---|---|---|---|---:|---:|---|
| `id` | INTEGER | non | oui | 0.0 % | 11 | `1`, `2`, `3` |
| `document_id` | INTEGER | oui | non | 0.0 % | 1 | `1` |
| `course_id` | TEXT | non | non | 0.0 % | 1 | `` |
| `numero` | INTEGER | oui | non | 0.0 % | 1 | `1` |
| `nom_cheval_raw` | TEXT | non | non | 9.1 % | 1 | `SHINNING OCEAN` |
| `nom_cheval_normalized` | TEXT | non | non | 18.2 % | 1 | `SHINNING OCEAN` |
| `sexe` | TEXT | non | non | 27.3 % | 1 | `M.7` |
| `age` | TEXT | non | non | 36.4 % | 1 | `7` |
| `poids` | TEXT | non | non | 45.5 % | 1 | `` |
| `corde` | TEXT | non | non | 54.5 % | 1 | `` |
| `distance_raw` | TEXT | non | non | 63.6 % | 1 | `8` |
| `distance_m` | INTEGER | non | non | 100.0 % | 0 | — |
| `chrono_raw` | TEXT | non | non | 81.8 % | 1 | `60.KG` |
| `chrono_normalized` | TEXT | non | non | 90.9 % | 1 | `60.KG` |
| `performances_raw` | TEXT | non | non | 100.0 % | 0 | — |
| `performances_structured` | TEXT | non | non | 100.0 % | 0 | — |
| `gains_raw` | TEXT | non | non | 100.0 % | 0 | — |
| `gains_euros` | INTEGER | non | non | 100.0 % | 0 | — |
| `driver_raw` | TEXT | non | non | 100.0 % | 0 | — |
| `driver_normalized` | TEXT | non | non | 100.0 % | 0 | — |
| `entraineur_raw` | TEXT | non | non | 100.0 % | 0 | — |
| `entraineur_normalized` | TEXT | non | non | 100.0 % | 0 | — |
| `proprietaire_raw` | TEXT | non | non | 100.0 % | 0 | — |
| `proprietaire_normalized` | TEXT | non | non | 100.0 % | 0 | — |
| `cote_raw` | TEXT | non | non | 100.0 % | 0 | — |
| `cote_decimale` | REAL | non | non | 100.0 % | 0 | — |
| `commentaire` | TEXT | non | non | 100.0 % | 0 | — |
| `raw_data` | TEXT | non | non | 100.0 % | 0 | — |

### 2.3 Relations

_Aucune relation détectée._

## 2. Base `test7.db`

- Taille : **12.0 Ko**
- SHA-256 : `07c3fde5174c7a248768f284a067221819d17e8c8f78fbc7b3a8765ae749cee6`
- Vues : aucune

### 2.1 Tables et volumes

| Table | Lignes | Clé primaire | Index |
|---|---:|---|---|
| `partants` | 7 | `id` | — |

### 2.2 Colonnes

**`partants`** — 7 lignes

| Colonne | Type | NOT NULL | PK | Taux de nullité | Distinct | Exemples |
|---|---|---|---|---:|---:|---|
| `id` | INTEGER | non | oui | 0.0 % | 7 | `1`, `2`, `3` |
| `document_id` | INTEGER | oui | non | 0.0 % | 1 | `1` |
| `course_id` | TEXT | non | non | 0.0 % | 1 | `` |
| `numero` | INTEGER | oui | non | 0.0 % | 1 | `1` |
| `nom_cheval_raw` | TEXT | non | non | 0.0 % | 1 | `SHINNING OCEAN` |
| `nom_cheval_normalized` | TEXT | non | non | 0.0 % | 1 | `SHINNING OCEAN` |
| `sexe` | TEXT | non | non | 0.0 % | 1 | `M.7` |
| `age` | TEXT | non | non | 0.0 % | 1 | `7` |
| `poids` | TEXT | non | non | 0.0 % | 1 | `` |
| `corde` | TEXT | non | non | 0.0 % | 1 | `` |
| `distance_raw` | TEXT | non | non | 0.0 % | 1 | `8` |
| `distance_m` | INTEGER | non | non | 100.0 % | 0 | — |
| `chrono_raw` | TEXT | non | non | 0.0 % | 1 | `60.KG` |
| `chrono_normalized` | TEXT | non | non | 0.0 % | 1 | `60.KG` |
| `performances_raw` | TEXT | non | non | 0.0 % | 1 | `2.2.9.5.4` |
| `performances_structured` | TEXT | non | non | 14.3 % | 1 | `[2, 2, 9, 5, 4]` |
| `gains_raw` | TEXT | non | non | 28.6 % | 1 | `146 785` |
| `gains_euros` | INTEGER | non | non | 42.9 % | 1 | `146785` |
| `driver_raw` | TEXT | non | non | 57.1 % | 1 | `D.SANTIAGO` |
| `driver_normalized` | TEXT | non | non | 71.4 % | 1 | `D.SANTIAGO` |
| `entraineur_raw` | TEXT | non | non | 85.7 % | 1 | `H.BLUME` |
| `entraineur_normalized` | TEXT | non | non | 100.0 % | 0 | — |
| `proprietaire_raw` | TEXT | non | non | 100.0 % | 0 | — |
| `proprietaire_normalized` | TEXT | non | non | 100.0 % | 0 | — |
| `cote_raw` | TEXT | non | non | 100.0 % | 0 | — |
| `cote_decimale` | REAL | non | non | 100.0 % | 0 | — |
| `commentaire` | TEXT | non | non | 100.0 % | 0 | — |
| `raw_data` | TEXT | non | non | 100.0 % | 0 | — |

### 2.3 Relations

_Aucune relation détectée._

## 2. Base `test8.db`

- Taille : **12.0 Ko**
- SHA-256 : `4ea4c0ab47587a6988b06bef3897da2b51d8096575d5624c1f327919c9065c92`
- Vues : aucune

### 2.1 Tables et volumes

| Table | Lignes | Clé primaire | Index |
|---|---:|---|---|
| `partants` | 7 | `id` | — |

### 2.2 Colonnes

**`partants`** — 7 lignes

| Colonne | Type | NOT NULL | PK | Taux de nullité | Distinct | Exemples |
|---|---|---|---|---:|---:|---|
| `id` | INTEGER | non | oui | 0.0 % | 7 | `1`, `2`, `3` |
| `document_id` | INTEGER | oui | non | 0.0 % | 1 | `1` |
| `course_id` | TEXT | non | non | 0.0 % | 1 | `` |
| `numero` | INTEGER | oui | non | 0.0 % | 1 | `1` |
| `nom_cheval_raw` | TEXT | non | non | 0.0 % | 1 | `SHINNING OCEAN` |
| `nom_cheval_normalized` | TEXT | non | non | 0.0 % | 1 | `SHINNING OCEAN` |
| `sexe` | TEXT | non | non | 0.0 % | 1 | `M.7` |
| `age` | TEXT | non | non | 0.0 % | 1 | `7` |
| `poids` | TEXT | non | non | 0.0 % | 1 | `` |
| `corde` | TEXT | non | non | 0.0 % | 1 | `` |
| `distance_raw` | TEXT | non | non | 0.0 % | 1 | `8` |
| `distance_m` | INTEGER | non | non | 100.0 % | 0 | — |
| `chrono_raw` | TEXT | non | non | 0.0 % | 1 | `60.KG` |
| `chrono_normalized` | TEXT | non | non | 0.0 % | 1 | `60.KG` |
| `performances_raw` | TEXT | non | non | 0.0 % | 1 | `2.2.9.5.4` |
| `performances_structured` | TEXT | non | non | 0.0 % | 1 | `[2, 2, 9, 5, 4]` |
| `gains_raw` | TEXT | non | non | 0.0 % | 1 | `146 785` |
| `gains_euros` | INTEGER | non | non | 0.0 % | 1 | `146785` |
| `driver_raw` | TEXT | non | non | 0.0 % | 1 | `D.SANTIAGO` |
| `driver_normalized` | TEXT | non | non | 0.0 % | 1 | `D.SANTIAGO` |
| `entraineur_raw` | TEXT | non | non | 0.0 % | 1 | `H.BLUME` |
| `entraineur_normalized` | TEXT | non | non | 0.0 % | 1 | `H.BLUME` |
| `proprietaire_raw` | TEXT | non | non | 14.3 % | 1 | `Y.MARIE-NELLY` |
| `proprietaire_normalized` | TEXT | non | non | 28.6 % | 1 | `Y.MARIE-NELLY` |
| `cote_raw` | TEXT | non | non | 42.9 % | 1 | `35/1` |
| `cote_decimale` | REAL | non | non | 57.1 % | 1 | `35.0` |
| `commentaire` | TEXT | non | non | 71.4 % | 1 | `comment` |
| `raw_data` | TEXT | non | non | 85.7 % | 1 | `{}` |

### 2.3 Relations

_Aucune relation détectée._

## 2. Base `test9.db`

- Taille : **12.0 Ko**
- SHA-256 : `be62e808343a99e15476833cf0325feb4f0c67f18b0ccad4afe4d5879e4e8523`
- Vues : aucune

### 2.1 Tables et volumes

| Table | Lignes | Clé primaire | Index |
|---|---:|---|---|
| `partants` | 0 | `id` | — |

### 2.2 Colonnes

**`partants`** — 0 lignes

| Colonne | Type | NOT NULL | PK | Taux de nullité | Distinct | Exemples |
|---|---|---|---|---:|---:|---|
| `id` | INTEGER | non | oui | — | 0 | — |
| `document_id` | INTEGER | oui | non | — | 0 | — |
| `course_id` | TEXT | non | non | — | 0 | — |
| `numero` | INTEGER | oui | non | — | 0 | — |
| `nom_cheval_raw` | TEXT | non | non | — | 0 | — |
| `nom_cheval_normalized` | TEXT | non | non | — | 0 | — |
| `sexe` | TEXT | non | non | — | 0 | — |
| `age` | TEXT | non | non | — | 0 | — |
| `poids` | TEXT | non | non | — | 0 | — |
| `corde` | TEXT | non | non | — | 0 | — |
| `distance_raw` | TEXT | non | non | — | 0 | — |
| `distance_m` | INTEGER | non | non | — | 0 | — |
| `chrono_raw` | TEXT | non | non | — | 0 | — |
| `chrono_normalized` | TEXT | non | non | — | 0 | — |
| `performances_raw` | TEXT | non | non | — | 0 | — |
| `performances_structured` | TEXT | non | non | — | 0 | — |
| `gains_raw` | TEXT | non | non | — | 0 | — |
| `gains_euros` | INTEGER | non | non | — | 0 | — |
| `driver_raw` | TEXT | non | non | — | 0 | — |
| `driver_normalized` | TEXT | non | non | — | 0 | — |
| `entraineur_raw` | TEXT | non | non | — | 0 | — |
| `entraineur_normalized` | TEXT | non | non | — | 0 | — |
| `proprietaire_raw` | TEXT | non | non | — | 0 | — |
| `proprietaire_normalized` | TEXT | non | non | — | 0 | — |
| `cote_raw` | TEXT | non | non | — | 0 | — |
| `cote_decimale` | REAL | non | non | — | 0 | — |
| `commentaire` | TEXT | non | non | — | 0 | — |
| `raw_data` | TEXT | non | non | — | 0 | — |

### 2.3 Relations

_Aucune relation détectée._

