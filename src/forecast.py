from pymongo import MongoClient
import pandas as pd
from sklearn.linear_model import LinearRegression
import numpy as np

client = MongoClient("mongodb://localhost:27017")
db = client["velib"]
col = db["stations_status_real"]

def get_timeseries_total_bikes():
    pipeline = [
        {"$group": {"_id": "$timestamp", "total_bikes": {"$sum": "$numbikesavailable"}}},
        {"$sort": {"_id": 1}},
    ]
    return list(col.aggregate(pipeline))

if __name__ == "__main__":
    ts_data = get_timeseries_total_bikes()
    ts_clean = [d for d in ts_data if d["_id"] is not None]
    df = pd.DataFrame(
        [{"timestamp": d["_id"], "total_bikes": d["total_bikes"]} for d in ts_clean]
    ).sort_values("timestamp")

    # Heure de la journée
    df["hour"] = df["timestamp"].dt.hour

    #Jour de la semaine
    df["weekday"] = df["timestamp"].dt.weekday  # 0=lundi, 6=dimanche

    # indicateur week-end
    df["is_weekend"] = df["weekday"].isin([5, 6]).astype(int)

    # Feature simple : t = 0,1,2,...
    df["t"] = np.arange(len(df))

    X = df[["t", "hour", "weekday", "is_weekend"]].values
    y = df["total_bikes"].values

    model = LinearRegression()
    model.fit(X, y)

    # Prédiction pour les points existants + un point futur
    df["pred"] = model.predict(X)

    t_future = len(df)
    last_hour = df["hour"].iloc[-1]
    last_weekday = df["weekday"].iloc[-1]
    last_is_weekend = df["is_weekend"].iloc[-1]

    y_future = model.predict([[t_future, last_hour, last_weekday, last_is_weekend]])[0]

    print(df[["timestamp", "total_bikes", "pred"]])
    print("\nProchaine prédiction (t+1) :", y_future)
    print(df[["timestamp", "t", "hour", "weekday", "is_weekend", "total_bikes", "pred"]])
    print("Prochaine prédiction :", y_future)

