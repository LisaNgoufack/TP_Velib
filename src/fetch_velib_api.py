import requests
import time
from datetime import datetime
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017")
db = client["velib"]
## col = db["stations_status"]
col = db["stations_status_real"]  # <- nouvelle collection pour les données API réelles

URL = "https://opendata.paris.fr/api/explore/v2.1/catalog/datasets/velib-disponibilite-en-temps-reel/records?limit=20"

def fetch_and_insert():
    r = requests.get(URL, timeout=10)
    r.raise_for_status()
    data = r.json()  # structure: {"total_count":..., "results":[...]}
    records = data.get("results", [])

    ts = datetime.utcnow()
    docs = []
    for rec in records:
        doc = rec.copy()
        doc["timestamp"] = ts
        docs.append(doc)

    if docs:
        col.insert_many(docs)
        print(f"{len(docs)} docs insérés à {ts}")
    else:
        print("Aucun enregistrement reçu.")

if __name__ == "__main__":
    fetch_and_insert()
    while True:
        fetch_and_insert()
        time.sleep(300)  # 300 s = 5 minutes
