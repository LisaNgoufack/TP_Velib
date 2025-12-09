from pymongo import MongoClient
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error
import numpy as np

client = MongoClient("mongodb://localhost:27017")
db = client["velib"]
## col = db["stations_status"]
col = db["stations_status_real"]

def get_global_types():
    pipeline = [
        {
            "$group": {
                "_id": None,
                "total_mech": {"$sum": "$mechanical"},
                "total_ebike": {"$sum": "$ebike"}
            }
        }
    ]
    res = list(col.aggregate(pipeline))
    return res[0] if res else None

def get_stats_by_city(limit=10):
    pipeline = [
        {
            "$group": {
                "_id": "$nom_arrondissement_communes",
                "avg_bikes": {"$avg": "$numbikesavailable"},
                "sum_bikes": {"$sum": "$numbikesavailable"}
            }
        },
        {"$sort": {"sum_bikes": -1}},
        {"$limit": limit}
    ]
    return list(col.aggregate(pipeline))

def get_top_stations(limit=10):
    pipeline = [
        {
            "$group": {
                "_id": {"stationcode": "$stationcode", "name": "$name"},
                "avg_bikes": {"$avg": "$numbikesavailable"},
                "sum_bikes": {"$sum": "$numbikesavailable"},
            }
        },
        {"$sort": {"avg_bikes": -1}},   # ou "sum_bikes"
        {"$limit": limit},
        {
            "$project": {
                "_id": 0,
                "stationcode": "$_id.stationcode",
                "name": "$_id.name",
                "avg_bikes": 1,
                "sum_bikes": 1,
            }
        },
    ]
    return list(col.aggregate(pipeline))


def get_all_stations():
    pipeline = [
        {
            "$project": {
                "_id": 0,
                "stationcode": 1,
                "name": 1,
                "numbikesavailable": 1,
                "mechanical": 1,
                "ebike": 1,
                "lat": "$coordonnees_geo.lat",
                "lon": "$coordonnees_geo.lon",
                "commune": "$nom_arrondissement_communes",
            }
        }
    ]
    return list(col.aggregate(pipeline))

def get_timeseries_total_bikes():
    pipeline = [
        {
            "$group": {
                "_id": "$timestamp",
                "total_bikes": {"$sum": "$numbikesavailable"},
            }
        },
        {"$sort": {"_id": 1}},
    ]
    return list(col.aggregate(pipeline))

def get_forecast_total_bikes():
    pipeline = [
        {"$group": {"_id": "$timestamp", "total_bikes": {"$sum": "$numbikesavailable"}}},
        {"$sort": {"_id": 1}},
    ]
    data = list(col.aggregate(pipeline))
    data = [d for d in data if d["_id"] is not None]

    if len(data) < 3:
        return None

    df = pd.DataFrame(
        [{"timestamp": d["_id"], "total_bikes": d["total_bikes"]} for d in data]
    ).sort_values("timestamp")

    # Features temporelles
    df["t"] = np.arange(len(df))
    df["hour"] = df["timestamp"].dt.hour
    df["weekday"] = df["timestamp"].dt.weekday
    df["is_weekend"] = df["weekday"].isin([5, 6]).astype(int)

    X = df[["t", "hour", "weekday", "is_weekend"]].values
    y = df["total_bikes"].values

    # 1) Modèle linéaire
    lin = LinearRegression()
    lin.fit(X, y)
    df["pred_lin"] = lin.predict(X)

    # 2) Random Forest
    rf = RandomForestRegressor(
        n_estimators=200,
        random_state=0,
    )
    rf.fit(X, y)
    df["pred_rf"] = rf.predict(X)

    # Erreurs (RMSE) sur l’historique
    mse_lin = mean_squared_error(y, df["pred_lin"])
    mse_rf = mean_squared_error(y, df["pred_rf"])

    rmse_lin = np.sqrt(mse_lin)
    rmse_rf = np.sqrt(mse_rf)

    # Prédiction future (on prolonge t et garde les mêmes features temporelles que le dernier point)
    t_future = len(df)
    last_hour = df["hour"].iloc[-1]
    last_weekday = df["weekday"].iloc[-1]
    last_is_weekend = df["is_weekend"].iloc[-1]
    next_lin = lin.predict([[t_future, last_hour, last_weekday, last_is_weekend]])[0]
    next_rf = rf.predict([[t_future, last_hour, last_weekday, last_is_weekend]])[0]

    return {
        "history": df,          # contient total_bikes, pred_lin, pred_rf
        "next_t": t_future,
        "next_pred_lin": next_lin,
        "next_pred_rf": next_rf,
        "rmse_lin": rmse_lin,
        "rmse_rf": rmse_rf,
    }

def get_timeseries_for_station(stationcode):
    pipeline = [
        {"$match": {"stationcode": stationcode}},
        {"$group": {"_id": "$timestamp", "bikes": {"$sum": "$numbikesavailable"}}},
        {"$sort": {"_id": 1}},
    ]
    return list(col.aggregate(pipeline))



if __name__ == "__main__":
    print(get_global_types())
    print(get_stats_by_city())
    print(get_all_stations()[:3])
    print(get_timeseries_total_bikes())
    res = get_forecast_total_bikes()
    if res:
        print(res["history"][["timestamp", "total_bikes", "pred_lin", "pred_rf"]])
        print("Prochaine prédiction linéaire :", res["next_pred_lin"])
        print("Prochaine prédiction RandomForest :", res["next_pred_rf"])
        print("RMSE linéaire :", res["rmse_lin"])
        print("RMSE RandomForest :", res["rmse_rf"])

def get_station_emptiness(limit=10):
    pipeline = [
        {
            "$group": {
                "_id": {"stationcode": "$stationcode", "name": "$name"},
                "total_snapshots": {"$sum": 1},
                "empty_count": {"$sum": {"$cond": [{"$eq": ["$numbikesavailable", 0]}, 1, 0]}},
                "full_count": {"$sum": {"$cond": [{"$eq": ["$numdocksavailable", 0]}, 1, 0]}},
            }
        },
        {
            "$project": {
                "_id": 0,
                "stationcode": "$_id.stationcode",
                "name": "$_id.name",
                "total_snapshots": 1,
                "pct_empty": {
                    "$multiply": [
                        {"$cond": [{"$gt": ["$total_snapshots", 0]}, {"$divide": ["$empty_count", "$total_snapshots"]}, 0]},
                        100,
                    ]
                },
                "pct_full": {
                    "$multiply": [
                        {"$cond": [{"$gt": ["$total_snapshots", 0]}, {"$divide": ["$full_count", "$total_snapshots"]}, 0]},
                        100,
                    ]
                },
            }
        },
        {"$sort": {"pct_empty": -1}},
        {"$limit": limit},
    ]
    return list(col.aggregate(pipeline))





