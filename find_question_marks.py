sql = """
                    INSERT INTO resultats (document_id, course_id, date, type_pari, arrivee, arrivee_complete,
                                         npo, np, disqualifies, non_partants,
                                         gains_ordre_raw, gains_ordre_euros, gains_desordre_raw,
                                         gains_desordre_euros, gains_bonus_raw, gains_bonus_euros,
                                         nb_gagnants_ordre, nb_gagnants_desordre, nb_gagnants_bonus,
                                         masse_partager_raw, masse_partager_euros,
                                         rapport_gagnant_raw, rapport_gagnant_euros,
                                         rapport_place_a_raw, rapport_place_a_euros,
                                         rapport_place_b_raw, rapport_place_b_euros,
                                         map_paris_raw, map_paris_euros, raw_text)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """

print(f'Total ?: {sql.count("?")}')

# Find all ? positions
for i, ch in enumerate(sql):
    if ch == '?':
        context = sql[max(0,i-15):i+15]
        print(f'Position {i}: ...{context}...')