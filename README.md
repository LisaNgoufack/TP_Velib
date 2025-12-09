## Dashboard Vélib – ETL MongoDB & IA (Streamlit)

## TP_modèle_Bigdata : mise en place d’un pipeline de collecte en temps réel des données Vélib, stockage dans MongoDB, analyses spatiales et temporelles, et modèles de prévision (Régression Linéaire vs RandomForestRegressor) exposés dans un dashboard Streamlit.

1. ## Objectifs du projet
Collecter automatiquement les données temps réel des stations Vélib (vélos disponibles, bornes libres, types de vélos).

Stocker l’historique dans MongoDB pour permettre des analyses ultérieures.

Construire des indicateurs clés : disponibilité par station, par commune, capacités, stations souvent vides/pleines.

Visualiser les données via un dashboard interactif (Streamlit + Plotly).

Entraîner des modèles de prévision du nombre total de vélos disponibles (modèle global) et par station.

Comparer la performance d’un modèle linéaire et d’un modèle plus avancé (RandomForestRegressor).

2. ## Architecture générale
L’architecture technique suit un schéma ETL simple :

- Extraction

- Script fetch_velib_api.py qui interroge périodiquement l’API publique Vélib (open data) et récupère l’état temps réel des stations.

- Transformation

- Nettoyage minimal, ajout d’un champ timestamp, typage des champs numériques.

- Chargement & stockage

- Insertion des documents dans MongoDB, base velib, collection stations_status_real.

- Analytics & IA :

Script analytics.py qui regroupe toutes les fonctions d’agrégation MongoDB, de création de séries temporelles et d’entraînement des modèles de prévision (LinReg + RandomForest).

-Visualisation :

Application app_streamlit.py qui consomme ces fonctions et propose un dashboard interactif.

Un schéma détaillé est disponible dans docs/architecture.png.

3. ## Données
- Source : API “Vélib - Vélos et bornes - Disponibilité temps réel” (Paris Data).

- Principaux champs utilisés :

stationcode, name, nom_arrondissement_communes (commune / arrondissement)

capacity : capacité totale de la station

numbikesavailable : vélos disponibles (mécaniques + électriques)

numdocksavailable : bornes libres

mechanical, ebike : détail par type de vélo

timestamp : date/heure du snapshot

Chaque appel à l’API génère un snapshot de l’état du réseau. Ces snapshots successifs permettent de calculer des indicateurs temporels (séries, pourcentages de stations vides/pleines, etc.).

4. ## Structure du dépôt
* fichier src/

- fetch_velib_api.py : script de collecte temps réel et insertion dans MongoDB.

- analytics.py :

    - fonctions d’agrégation MongoDB (totaux, top communes/stations, histogramme des capacités) ;

    - construction des séries temporelles globales et par station ;

    - entraînement des modèles de prévision :

    - Régression Linéaire (features temporelles : t, hour, weekday, is_weekend) ;

    - RandomForestRegressor, avec calcul des métriques (RMSE).

- app_streamlit.py : application Streamlit (dashboard).

- etl_velib.py / forecast.py : scripts utilisés pour les tests et la mise au point des modèles.

* docs/

  - architecture.png : schéma global ETL + MongoDB + Streamlit + IA.

  - ml_model.png : schéma des modèles de prévision (features → LinReg / RandomForest → prédictions).

* README.md : documentation du projet.

* requirements.txt : dépendances Python.

5. ## Dashboard Streamlit
Le dashboard propose plusieurs sections :

 - Vue globale du réseau

 - Répartition des vélos mécaniques vs électriques.

 - Top 10 des communes en nombre de vélos disponibles.

 - Top stations (nombre moyen / total de vélos).

 - Analyses spatiales

 - Carte interactive des stations (Plotly Mapbox), colorée selon le nombre de vélos disponibles ou la capacité.

 - Possibilité de filtrer par commune/arrondissement.

 - Analyses temporelles

 - Série temporelle du nombre total de vélos disponibles sur le réseau.

 - Scatter plot heure de la journée vs nombre de vélos, avec indicateur semaine / week-end.

 - Stations “critiques”

 - Calcul, pour chaque station, de :

 - total_snapshots : nombre total de relevés pour cette station.

 - pct_empty : pourcentage de snapshots où numbikesavailable = 0 (station vide).

 - pct_full : pourcentage de snapshots où numdocksavailable = 0 (station pleine).

 - Graphique des stations les plus souvent vides / pleines.

 - Prévision globale (IA)

 - Modèle de Régression Linéaire et modèle RandomForestRegressor entraînés sur les features temporelles (t, hour, weekday, is_weekend).

 - Visualisation des trois courbes :

 - valeurs observées,

 - prédictions du modèle linéaire,

 - prédictions du Random Forest.

 - Affichage des RMSE des deux modèles et de la prochaine prédiction (horizon immédiat).

 - Prévision par station

 - Selectbox pour choisir un stationcode.

 - Série temporelle locale de la station et petit modèle de régression (LinReg) pour illustrer une prévision au pas suivant.

6. ## Modèles de prévision
- Features
Pour le modèle global, les features utilisées sont :

  - t : index temporel (0, 1, 2, …)

  - hour : heure de la journée

  - weekday : jour de la semaine (0 = lundi, …, 6 = dimanche)

  - is_weekend : indicateur binaire (1 si samedi/dimanche, 0 sinon)

Ces variables sont extraites à partir du timestamp avant l’entraînement.

- Modèles
    - Régression Linéaire (LinearRegression)

    - Simple, interprétable, sert de baseline.

    - RandomForestRegressor

    - Modèle d’ensemble non linéaire, plus flexible.

    - Entraîné avec plusieurs arbres (par ex. n_estimators=200).

    - Une comparaison des erreurs (RMSE) montre que, sur l’historique collecté, le RandomForest capture mieux les variations du nombre de vélos disponibles que le modèle linéaire.

7. ## Difficultés rencontrées
- Gestion de l’API Vélib (formats de champs, ajout du timestamp, robustesse aux erreurs de requête).

- Volume d’historique limité pour les premières expérimentations de prévision, ce qui peut entraîner un léger sur-apprentissage des modèles.

- Conception de l’interface Streamlit pour qu’elle reste lisible malgré plusieurs graphes : choix des bonnes sections, organisation verticale, gestion des filtres.

- Intégration de deux modèles de prévision dans la même fonction / même graphique et gestion des métriques associées.

8. ## Améliorations possibles
- Collecte sur plusieurs jours / semaines pour enrichir l’historique, lisser le bruit et évaluer les modèles de manière plus robuste.

- Nouvelles features : météo (pluie, température), vacances scolaires, événements, jours fériés.

- Modèles plus avancés :

- XGBoost / Gradient Boosting ;

- modèles de séries temporelles (LSTM, modèles séquentiels).

- Alerting opérationnel : déclencher des alertes (mail/Slack) si certaines stations dépassent un seuil critique de pct_empty ou pct_full.

- Déploiement : conteneurisation avec Docker et déploiement sur un service cloud (Streamlit Cloud, Heroku, etc.).

- Tests automatisés : tests unitaires sur les fonctions d’agrégation et sur les transformations de features.

9. ## Installation et exécution
* Prérequis
  - Python 3.x

  - MongoDB en local (ou instance distante accessible)

* Installation
  - git clone https://github.com/LisaNgoufack/TP_Velib.git
  - bash : cd TP_Velib
  - pip install -r requirements.txt
  - Lancer la collecte : python src/fetch_velib_api.py
Le script interroge l’API Vélib à intervalle régulier et alimente la base MongoDB velib (collection stations_status_real).

  - Lancer le dashboard : streamlit run src/app_streamlit.py
Ouvrir ensuite le lien local fourni par Streamlit dans le navigateur pour explorer les indicateurs et les modèles.

