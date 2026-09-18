-- ============================================================
-- Hippo Engine — migration 002 : vues analytiques
-- ============================================================

-- Vue : partants d'une course avec leurs référentiels résolus
CREATE OR REPLACE VIEW v_runners_full AS
SELECT
    r.id                AS runner_id,
    r.race_id,
    r.number,
    h.name              AS horse_name,
    h.sex,
    h.age,
    j.name              AS jockey_name,
    t.name              AS trainer_name,
    r.draw,
    r.weight,
    r.official_rating,
    r.morning_odds,
    r.current_odds,
    r.final_odds,
    r.status
FROM race_runners r
JOIN horses  h ON h.id = r.horse_id
LEFT JOIN jockeys  j ON j.id = r.jockey_id
LEFT JOIN trainers t ON t.id = r.trainer_id;

-- Vue : forme du cheval (5 dernières sorties)
CREATE OR REPLACE VIEW v_horse_form AS
SELECT
    horse_id,
    COUNT(*)                                                   AS starts,
    COUNT(*) FILTER (WHERE finish_position = 1)                AS wins,
    COUNT(*) FILTER (WHERE finish_position <= 3)               AS top3,
    COUNT(*) FILTER (WHERE finish_position <= 5)               AS top5,
    ROUND(AVG(finish_position), 3)                             AS avg_finish,
    MIN(finish_position)                                       AS best_finish,
    MAX(finish_position)                                       AS worst_finish
FROM horse_results
GROUP BY horse_id;

-- Vue : performance d'une prédiction vs résultat réel
CREATE OR REPLACE VIEW v_prediction_accuracy AS
SELECT
    p.race_id,
    p.model_version,
    p.confidence,
    pp.top3_hit,
    pp.top5_hit,
    pp.quinte_hit,
    pp.brier_score,
    pp.log_loss,
    pp.roi,
    r.date,
    r.hippodrome
FROM predictions p
JOIN prediction_performance pp ON pp.prediction_id = p.id
JOIN races r ON r.id = p.race_id;

-- Vue : taux de réussite agrégé, avec période et volume
-- (obligatoire pour toute statistique publiée — cf. règle #31)
CREATE OR REPLACE VIEW v_accuracy_summary AS
SELECT
    model_version,
    COUNT(*)                                        AS races_tested,
    MIN(date)                                       AS period_from,
    MAX(date)                                       AS period_to,
    ROUND(100.0 * COUNT(*) FILTER (WHERE top3_hit)   / NULLIF(COUNT(*),0), 2) AS top3_hit_rate,
    ROUND(100.0 * COUNT(*) FILTER (WHERE top5_hit)   / NULLIF(COUNT(*),0), 2) AS top5_hit_rate,
    ROUND(100.0 * COUNT(*) FILTER (WHERE quinte_hit) / NULLIF(COUNT(*),0), 2) AS quinte_hit_rate,
    ROUND(AVG(brier_score), 6)                      AS avg_brier_score,
    ROUND(AVG(log_loss), 6)                         AS avg_log_loss,
    ROUND(AVG(roi), 4)                              AS avg_roi
FROM v_prediction_accuracy
GROUP BY model_version;
