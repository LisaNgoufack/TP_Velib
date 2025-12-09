import json
from datetime import datetime, timedelta
from pymongo import MongoClient

# 1) Connexion Mongo
client = MongoClient("mongodb://localhost:27017")
db = client["velib"]
col = db["stations_status"]

# 2) Lecture du fichier JSON (snapshot unique)
with open("../velib-disponibilite-en-temps-reel.json", "r", encoding="utf-8") as f:
    data_snapshot = json.load(f)

print(f"Snapshot de base : {len(data_snapshot)} stations")

# 3) Paramètres d'historique simulé
start_time = datetime(2025, 1, 1, 8, 0, 0)  # début (à adapter si tu veux)
n_steps = 10                                 # nombre de timestamps
step = timedelta(hours=1)                    # pas de 1 heure

all_docs = []

for i in range(n_steps):
    ts = start_time + i * step
    for doc in data_snapshot:
        new_doc = doc.copy()
        new_doc["timestamp"] = ts
        all_docs.append(new_doc)

print(f"Nombre total de documents à insérer : {len(all_docs)}")

# 4) Insertion en base
if all_docs:
    col.insert_many(all_docs)
    print("Insertion historique simulée OK.")
else:
    print("Aucun document à insérer.")
