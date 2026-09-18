# Guide d'Enrichissement des Données Hippique - APIs & Stratégies

> Document de référence pour améliorer les analyses prédictives PMU/LONAB
> Généré le 2026-09-10

---

## 1. État Actuel de la Base de Données

### Tables principales (SQLite: `pmu_lonab.db`)

| Table | Enregistrements | Description |
|-------|----------------|-------------|
| `documents` | 2 711 | Métadonnées PDF (JOURNAL, RESULTAT, ECD, REP) |
| `courses` | 929 | Courses avec hippodrome, discipline, distance, montant |
| `partants` | 13 163 | Chevaux par course avec forme, gains, cotes, driver, entraîneur |
| `resultats` | 939 | Arrivées Tiercé/Quarté/4+1 avec rapports |
| `ecd_documents` | 800 | Courses en direct (arrivées, paris PMU) |
| `ecd_courses` | 6 509 | Détails courses ECD |
| `ecd_paris` | 11 879 | Paris par course ECD |
| `rep_documents` | 45 | Rapports PMU (rapports ordre/désordre) |

### Features disponibles par cheval (`partants`)

| Variable | Type | Qualité | Notes |
|----------|------|---------|-------|
| `nom_cheval_normalized` | TEXT | ✅ | Nom nettoyé |
| `sexe` / `age` | TEXT | ✅ | H/F/M + âge |
| `gains_euros` | INTEGER | ✅ | Gains carrière |
| `chrono_normalized` | TEXT | ✅ | Ex: `1:11.60` |
| `distance_m` | INTEGER | ✅ | Distance course |
| `performances_structured` | JSON | ✅ | Ex: `[2, 2, 9, 5, 4]` (5 dernières) |
| `cote_decimale` | REAL | ✅ | **Cible principale** (ex: 7.0) |
| `driver_normalized` | TEXT | ✅ | |
| `entraineur_normalized` | TEXT | ✅ | |
| `poids` / `corde` | TEXT | ⚠️ | Souvent vide |

### Cibles (Targets) possibles

| Target | Type | Description |
|--------|------|-------------|
| `cote_decimale` | Régression | Prédire la cote PMU |
| `cote_decimale < 5` | Classification binaire | Favori (oui/non) |
| `TOP 3 cotes` | Classement | Podium cotes |

---

## 2. APIs pour Enrichir les Données

### 2.1 APIs Officielles Françaises (Priorité HAUTE)

| API | Accès | Données clés | Statut |
|-----|-------|--------------|--------|
| **PMU Open Data** | `https://data.pmu.fr` | Courses, partants, cotes temps réel, résultats, rapports | ✅ Gratuit, public |
| **France Galop** | Partenariat requis | Programmes, engagements, perfs complètes, vidéos | 🟡 Sur demande |
| **Le Trot Open Data** | `https://data.letrot.com` | Courses attelé, drivers, entraîneurs, stats | ✅ Gratuit |

**Endpoints PMU utiles :**
```
GET /services/racing/card/{date}/{reunion}/{course_num}  # Cotes temps réel
GET /services/racing/results/{date}                       # Résultats du jour
GET /services/racing/program/{date}                       # Programme complet
```

### 2.2 APIs Météo & Terrain (Priorité HAUTE - Impact ★★★★★)

| API | Données | Coût | Intégration |
|-----|---------|------|-------------|
| **Météo-France** | Prévisions précises, vigilances, historique | Gratuit (recherche) | API REST |
| **OpenWeatherMap** | Historique + prévisions 48h, radar pluie | Freemium (1000/jour gratuit) | REST simple |
| **WeatherAPI.com** | Historique par GPS, alertes | Payant ~40€/mois | REST |

**Coordonnées GPS hippodromes principaux :**
```python
HIPPODROMES_GPS = {
    "PARIS-VINCENNES": (48.838, 2.419),
    "PARIS-VINCENNES NOCTURNE": (48.838, 2.419),
    "CHANTILLY": (49.192, 2.461),
    "DEAUVILLE": (49.360, 0.083),
    "CAGNES-SUR-MER": (43.664, 7.145),
    "AUTEUIL": (48.862, 2.255),
    "SAINT-CLOUD": (48.841, 2.221),
    "ENGHIEN": (48.974, 2.310),
    "LONGCHAMP": (48.852, 2.253),
}
```

### 2.3 APIs Marché & Cotes (Priorité MOYENNE)

| API | Spécificité | Accès |
|-----|-------------|-------|
| **Betfair API** | Cotes échange, volumes, liquidité, graphiques | Gratuit (compte actif requis) |
| **PMU Cotes Temps Réel** | Évolution cotes J-1 → départ, volumes | Open Data |
| **Timeform** | Ratings experts, analyses | Très cher (500-5000€/mois) |
| **Racing Post** | Données UK/IRL référence | Partenariat |

### 2.4 Données Complémentaires

| Source | Données | Difficulté |
|--------|---------|------------|
| **Historique complet cheval** | Toute carrière, pas seulement 5 dernières | France Galop/Le Trot (partenariat) |
| **Stats driver/entraîneur par hippodrome** | Taux de réussite locaux | Calculable depuis ECD |
| **Poids porté (handicap)** | Programme officiel | France Galop |
| **Corde / position départ** | Programme | France Galop |
| **Vidéo replay** | Analyse visuelle allures | Equidia/PMU |

---

## 3. Nouvelles Features par Enrichissement

| Feature | Source | Impact Prédictif | Effort |
|---------|--------|------------------|--------|
| **État terrain** (bon/mouillé/collant/lourd) | Météo + déclaration officielle | ★★★★★ **CRITIQUE** | Faible |
| **Température / Humidité / Vent** | Météo | ★★★★ | Faible |
| **Précipitations 24h/48h avant** | Météo | ★★★★ | Faible |
| **Cotes ouverture → clôture** | PMU/Betfair | ★★★★★ "Smart money" | Moyen |
| **Volume paris par cheval** | Betfair/PMU | ★★★★ | Moyen |
| **Écart cote ouverture/clôture** | PMU | ★★★★ | Moyen |
| **Historique complet (toute carrière)** | France Galop/Le Trot | ★★★★★ | Élevé (partenariat) |
| **Stats driver/entraîneur sur hippodrome** | ECD + calcul | ★★★★ | Faible |
| **Poids porté (handicap)** | Programmes | ★★★★ | Moyen |
| **Position corde / boîte** | Programmes | ★★★ | Moyen |
| **Jours depuis dernière course** | Calculable | ★★★ | Faible |
| **Spécialité distance/hippodrome** | Calculable | ★★★ | Faible |

---

## 4. Architecture d'Enrichissement Proposée

```
┌──────────────────┐     ┌────────────────────┐     ┌─────────────────────┐
│  Base SQLite     │────▶│  Pipeline ETL      │────▶│  Base Enrichie      │
│  (actuelle)      │     │  (quotidien/cron)  │     │  + ml_features      │
└──────────────────┘     └────────────────────┘     └─────────────────────┘
                                │
              ┌─────────────────┼─────────────────┐
              ▼                 ▼                 ▼
       ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
       │  PMU API    │   │  Météo API  │   │  Calculs    │
       │ (cotes,     │   │ (terrain,   │   │ (features   │
       │  partants,  │   │  vent,      │   │  dérivées)  │
       │  résultats) │   │  pluie)     │   │             │
       └─────────────┘   └─────────────┘   └─────────────┘
```

### Tables d'enrichissement à créer

```sql
-- Météo par course
CREATE TABLE weather_course (
    course_id TEXT PRIMARY KEY,
    temperature REAL,
    humidity INTEGER,
    wind_speed REAL,
    wind_direction INTEGER,
    precipitation_24h REAL,
    precipitation_48h REAL,
    condition TEXT,           -- 'Clear', 'Rain', 'Clouds'
    terrain_etat TEXT,        -- 'Bon', 'Mouillé', 'Lourd', 'Collant'
    FOREIGN KEY (course_id) REFERENCES courses(course_id)
);

-- Cotes temps réel
CREATE TABLE odds_realtime (
    course_id TEXT,
    numero INTEGER,
    cote_ouverture REAL,
    cote_milieu REAL,
    cote_cloture REAL,
    evolution_pct REAL,       -- (cloture - ouverture) / ouverture
    volume_paris INTEGER,
    rang_ouverture INTEGER,
    rang_cloture INTEGER,
    timestamp DATETIME,
    PRIMARY KEY (course_id, numero, timestamp),
    FOREIGN KEY (course_id) REFERENCES courses(course_id)
);

-- Stats driver/entraîneur par hippodrome (calculées)
CREATE TABLE stats_driver_hippo (
    driver TEXT,
    hippodrome TEXT,
    nb_courses INTEGER,
    nb_victoires INTEGER,
    nb_podiums INTEGER,
    taux_victoire REAL,
    gains_moyens REAL,
    PRIMARY KEY (driver, hippodrome)
);

CREATE TABLE stats_entraineur_hippo (
    entraineur TEXT,
    hippodrome TEXT,
    nb_courses INTEGER,
    nb_victoires INTEGER,
    taux_victoire REAL,
    PRIMARY KEY (entraineur, hippodrome)
);

-- Table ML unifiée (feature store)
CREATE TABLE ml_features AS
SELECT 
    p.course_id,
    p.numero,
    p.nom_cheval_normalized,
    
    -- Cheval
    p.gains_euros,
    p.age,
    p.sexe,
    json_extract(p.performances_structured, '$[0]') as perf_1,
    json_extract(p.performances_structured, '$[1]') as perf_2,
    (SELECT AVG(CAST(value AS REAL)) FROM json_each(p.performances_structured) 
     WHERE json_type(value) = 'integer') as perf_moy_5,
    (SELECT SUM(CASE WHEN CAST(value AS INTEGER) = 1 THEN 1 ELSE 0 END) 
     FROM json_each(p.performances_structured)) as nb_vic_5,
    (SELECT SUM(CASE WHEN CAST(value AS INTEGER) <= 3 THEN 1 ELSE 0 END) 
     FROM json_each(p.performances_structured)) as nb_pod_5,
    
    -- Course
    c.hippodrome,
    c.discipline,
    c.distance_m,
    c.type_course,
    c.partants_effectifs,
    
    -- Météo
    w.temperature,
    w.precipitation_24h,
    w.wind_speed,
    w.terrain_etat,
    
    -- Cotes marché
    o.cote_ouverture,
    o.cote_cloture,
    o.evolution_pct,
    o.volume_paris,
    
    -- Stats driver/entraîneur
    sd.taux_victoire as driver_taux_vic_hippo,
    se.taux_victoire as entraineur_taux_vic_hippo,
    
    -- Target
    p.cote_decimale as target_cote,
    CASE WHEN p.cote_decimale < 5 THEN 1 ELSE 0 END as target_favori
    
FROM partants p
JOIN courses c ON p.course_id = c.course_id
LEFT JOIN weather_course w ON c.course_id = w.course_id
LEFT JOIN odds_realtime o ON c.course_id = o.course_id AND p.numero = o.numero
LEFT JOIN stats_driver_hippo sd ON p.driver_normalized = sd.driver AND c.hippodrome = sd.hippodrome
LEFT JOIN stats_entraineur_hippo se ON p.entraineur_normalized = se.entraineur AND c.hippodrome = se.hippodrome
WHERE p.cote_decimale IS NOT NULL;
```

---

## 5. Pipeline ETL Quotidien (Pseudo-code)

```python
# enrich_daily.py - À lancer chaque matin 6h
import sqlite3
import requests
from datetime import datetime, timedelta

DB_PATH = "pmu_lonab.db"
PMU_API = "https://www.pmu.fr/services/racing"
OPENWEATHER_KEY = "votre_cle"

def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Courses à venir (J à J+3)
    upcoming = get_upcoming_courses(cursor, days=3)
    
    for course in upcoming:
        course_id, date, reunion, course_num, hippodrome = course
        
        # 2. Enrichir météo
        enrich_weather(cursor, course_id, hippodrome, date)
        
        # 3. Récupérer cotes PMU temps réel
        enrich_odds_realtime(cursor, course_id, date, reunion, course_num)
        
        # 4. Mettre à jour stats driver/entraîneur
        update_driver_entraineur_stats(cursor)
    
    # 5. Régénérer table ML
    rebuild_ml_features(cursor)
    
    conn.commit()
    conn.close()
    print(f"Enrichissement terminé: {datetime.now()}")

def enrich_weather(cursor, course_id, hippodrome, date):
    """Récupère météo jour de course via OpenWeatherMap."""
    coords = HIPPODROMES_GPS.get(hippodrome.upper())
    if not coords:
        return
    
    lat, lon = coords
    dt = int(datetime.strptime(date, "%Y-%m-%d").timestamp())
    
    url = "https://api.openweathermap.org/data/2.5/onecall/timemachine"
    params = {"lat": lat, "lon": lon, "dt": dt, "appid": OPENWEATHER_KEY, "units": "metric"}
    
    try:
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()
        current = data.get("current", {})
        
        # Déterminer état terrain
        precip = current.get("rain", {}).get("1h", 0)
        if precip > 10: terrain = "Lourd"
        elif precip > 2: terrain = "Mouillé"
        elif precip > 0: terrain = "Collant"
        else: terrain = "Bon"
        
        cursor.execute("""
            INSERT OR REPLACE INTO weather_course 
            (course_id, temperature, humidity, wind_speed, wind_direction,
             precipitation_24h, condition, terrain_etat)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            course_id,
            current.get("temp"),
            current.get("humidity"),
            current.get("wind_speed"),
            current.get("wind_deg"),
            precip,
            current.get("weather", [{}])[0].get("main"),
            terrain
        ))
    except Exception as e:
        print(f"Erreur météo {course_id}: {e}")

def enrich_odds_realtime(cursor, course_id, date, reunion, course_num):
    """Récupère cotes PMU officielles."""
    url = f"{PMU_API}/card/{date}/{reunion}/{course_num}"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        
        for participant in data.get("participants", []):
            num = participant.get("numero")
            cote = participant.get("cote", {}).get("directe")
            if cote:
                cursor.execute("""
                    INSERT INTO odds_realtime 
                    (course_id, numero, cote_cloture, timestamp)
                    VALUES (?, ?, ?, datetime('now'))
                    ON CONFLICT(course_id, numero) DO UPDATE SET
                        cote_cloture=excluded.cote_cloture,
                        timestamp=excluded.timestamp
                """, (course_id, num, float(cote)))
    except Exception as e:
        print(f"Erreur cotes {course_id}: {e}")

def update_driver_entraineur_stats(cursor):
    """Recalcule stats driver/entraîneur par hippodrome depuis ECD."""
    cursor.execute("""
        INSERT OR REPLACE INTO stats_driver_hippo
        SELECT 
            p.driver_normalized as driver,
            c.hippodrome,
            COUNT(*) as nb_courses,
            SUM(CASE WHEN p.numero = json_extract(ec.arrivee_positions, '$[0]') THEN 1 ELSE 0 END) as nb_victoires,
            SUM(CASE WHEN p.numero IN (
                json_extract(ec.arrivee_positions, '$[0]'),
                json_extract(ec.arrivee_positions, '$[1]'),
                json_extract(ec.arrivee_positions, '$[2]')
            ) THEN 1 ELSE 0 END) as nb_podiums,
            CAST(SUM(CASE WHEN p.numero = json_extract(ec.arrivee_positions, '$[0]') THEN 1 ELSE 0 END) AS REAL) / COUNT(*) as taux_victoire,
            AVG(p.gains_euros) as gains_moyens
        FROM partants p
        JOIN courses c ON p.course_id = c.course_id
        JOIN ecd_courses ec ON c.course_id = ec.course_id
        WHERE p.driver_normalized IS NOT NULL
        GROUP BY p.driver_normalized, c.hippodrome
    """)
    # Même chose pour entraîneurs...

def rebuild_ml_features(cursor):
    """Régénère la table ml_features complète."""
    cursor.execute("DROP TABLE IF EXISTS ml_features")
    cursor.execute("""
        CREATE TABLE ml_features AS
        -- (Requête complète du section 3)
    """)
    print("Table ml_features régénérée")

if __name__ == "__main__":
    main()
```

---

## 6. Modélisation ML - Approche Recommandée

### Baseline rapide (XGBoost)

```python
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, roc_auc_score

conn = sqlite3.connect(DB_PATH)
df = pd.read_sql("SELECT * FROM ml_features", conn)

# Préparation
y_reg = df['target_cote']
y_clf = df['target_favori']
X = df.drop(['target_cote', 'target_favori', 'course_id', 'numero', 'nom_cheval_normalized'], axis=1)

# Encodage categorical
X = pd.get_dummies(X, columns=['hippodrome', 'discipline', 'sexe', 'type_course', 'terrain_etat'])

# Split temporel (pas random!)
split_date = '2025-01-01'  # À adapter
# Mieux: utiliser course_id pour split temporel

X_train, X_test, y_train, y_test = train_test_split(X, y_reg, test_size=0.2, shuffle=False)

# Modèle régression cote
model_reg = xgb.XGBRegressor(
    n_estimators=500,
    max_depth=6,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42
)
model_reg.fit(X_train, y_train)
preds = model_reg.predict(X_test)
print(f"MAE: {mean_absolute_error(y_test, preds):.2f}")

# Modèle classification favori
model_clf = xgb.XGBClassifier(
    n_estimators=300,
    max_depth=5,
    learning_rate=0.05,
    scale_pos_weight=len(y_clf[y_clf==0])/len(y_clf[y_clf==1])
)
model_clf.fit(X_train, y_clf)
print(f"AUC: {roc_auc_score(y_clf, model_clf.predict_proba(X_test)[:,1]):.3f}")

# Feature importance
importance = pd.DataFrame({
    'feature': X.columns,
    'importance': model_reg.feature_importances_
}).sort_values('importance', ascending=False)
print(importance.head(20))
```

### Features les plus importantes attendues

1. `cote_ouverture` / `cote_cloture` (marché = meilleure info)
2. `perf_moy_5` / `nb_vic_5` (forme récente)
3. `gains_euros` (niveau du cheval)
4. `driver_taux_vic_hippo` / `entraineur_taux_vic_hippo`
5. `terrain_etat` (bon/mouillé/lourd)
6. `distance_m` + `hippodrome` (spécialité)
7. `evolution_pct` (mouvement cote = info parieurs avertis)

---

## 7. Coûts & Budget Mensuel Estimé

| Service | Coût/mois | Priorité |
|---------|-----------|----------|
| PMU Open Data | 0€ | ✅ Obligatoire |
| OpenWeatherMap Pro | 40€ | ✅ Obligatoire |
| Météo-France | 0€ | ✅ Obligatoire |
| Betfair API | 0€ (compte) | 🟡 Recommandé |
| France Galop / Le Trot | Négocié | 🟡 Partenariat |
| Timeform / Racing Post | 500-5000€ | ❌ Optionnel |
| Serveur/cron (VPS) | 5-20€ | ✅ Nécessaire |

**Budget minimum viable : ~45€/mois** (météo pro + VPS)

---

## 8. Checklist d'Implémentation

### Phase 1 - Base (Semaine 1) ✅ FAIT
- [x] Base SQLite unifiée créée
- [x] Parsing 2756 PDFs terminé (99.7% succès)
- [x] Qualité moyenne 92.3/100

### Phase 2 - Enrichissement Core (Semaine 2)
- [ ] Script `enrich_weather.py` (OpenWeatherMap)
- [ ] Script `enrich_odds_pmu.py` (cotes temps réel)
- [ ] Tables `weather_course`, `odds_realtime`
- [ ] Cron journalier 6h00

### Phase 3 - Features Avancées (Semaine 3)
- [ ] Stats driver/entraîneur par hippodrome
- [ ] Table `ml_features` régénérée
- [ ] Feature engineering : forme, spécialité, jours repos

### Phase 4 - Modélisation (Semaine 4)
- [ ] Baseline XGBoost (régression cote + classif favori)
- [ ] Validation walk-forward temporelle
- [ ] Backtest sur 2025-2026

### Phase 5 - Production (Semaine 5+)
- [ ] API REST pour prédictions (FastAPI)
- [ ] Dashboard monitoring (Grafana/Streamlit)
- [ ] Alertes "value bets" (cote prédite < cote marché)

---

## 9. Ressources & Liens Utiles

### Documentation APIs
- [PMU Open Data](https://data.pmu.fr) - Catalogue datasets
- [Le Trot Open Data](https://data.letrot.com) - Datasets attelé
- [OpenWeatherMap API](https://openweathermap.org/api) - One Call API 3.0
- [Betfair API Docs](https://docs.developer.betfair.com/) - Streaming API

### Papers & Références
- "Predicting Horse Race Outcomes" - Journal of Quantitative Analysis in Sports
- "Market Efficiency in Betting Markets" - Economic Journal
- "Weather Effects on Horse Racing" - Weather and Climate Extremes

### Outils Python
```bash
pip install xgboost lightgbm scikit-learn pandas sqlite3 requests
pip install fastapi uvicorn  # Pour API prédictions
pip install streamlit plotly  # Pour dashboard
```

---

## 10. Prochaines Actions Immédiates

1. **Créer clé OpenWeatherMap** (gratuit 1000/jour, ou 40€/mois pro)
2. **Tester endpoint PMU** : `curl "https://www.pmu.fr/services/racing/card/2026-09-10/R1/C1"`
3. **Lancer script météo** sur historiques 2024-2025 pour peupler `weather_course`
4. **Calculer stats driver/entraîneur** depuis tables ECD existantes
5. **Premier entraînement XGBoost** sur `ml_features` actuelle (sans météo/cotes temps réel)

---

*Document maintenu à jour au fur et à mesure de l'implémentation.*