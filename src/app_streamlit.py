import streamlit as st
import pandas as pd
import plotly.express as px
from sklearn.linear_model import LinearRegression
from analytics import (
    get_global_types,
    get_stats_by_city,
    get_top_stations,
    get_all_stations,
    get_timeseries_total_bikes,
    get_forecast_total_bikes,
    get_station_emptiness,
    get_timeseries_for_station,
)


st.title("Dashboard Vélib – Snapshot")

# 1) Global mécaniques vs électriques
types_data = get_global_types()
if types_data:
    st.subheader("Répartition des types de vélos")
    df_types = pd.DataFrame(
        {
            "type": ["Mécaniques", "Électriques"],
            "nombre": [types_data["total_mech"], types_data["total_ebike"]],
        }
    )
    st.bar_chart(df_types, x="type", y="nombre")

# 2) Top communes par vélos disponibles
stats_city = get_stats_by_city(limit=10)
if stats_city:
    st.subheader("Top communes par vélos disponibles")
    df_city = pd.DataFrame(
        [
            {
                "commune": d["_id"],
                "sum_bikes": d["sum_bikes"],
                "avg_bikes": d["avg_bikes"],
            }
            for d in stats_city
            if d["_id"] is not None
        ]
    )
    st.bar_chart(df_city, x="commune", y="sum_bikes")

# 3) Top stations par vélos disponibles
top_stations = get_top_stations(limit=10)
if top_stations:
    st.subheader("Top 10 stations par vélos disponibles")
    df_st = pd.DataFrame(top_stations)
    df_st["station"] = df_st["stationcode"] + " - " + df_st["name"]
    st.bar_chart(df_st, x="station", y="avg_bikes")  # ou "sum_bikes"


# Filtre par communes sur la carte

st.subheader("Carte des stations Vélib")

stations = get_all_stations()
if stations:
    df_map = pd.DataFrame(stations).dropna(subset=["lat", "lon"])

    communes = sorted(df_map["commune"].dropna().unique())
    selected_commune = st.selectbox("Filtrer par commune", options=["Toutes"] + communes)

    if selected_commune != "Toutes":
        df_map = df_map[df_map["commune"] == selected_commune]

# carte
st.subheader("Carte des stations Vélib")

stations = get_all_stations()
if stations:
    df_map = pd.DataFrame(stations).dropna(subset=["lat", "lon"])

    df_map["hover"] = (
        "Station : " + df_map["name"]
        + "<br>Code : " + df_map["stationcode"].astype(str)
        + "<br>Commune : " + df_map["commune"]
        + "<br>Vélos dispo : " + df_map["numbikesavailable"].astype(str)
        + "<br>Mécaniques : " + df_map["mechanical"].astype(str)
        + "<br>Électriques : " + df_map["ebike"].astype(str)
    )

    fig_map = px.scatter_mapbox(
        df_map,
        lat="lat",
        lon="lon",
        hover_name="name",
        hover_data={
            "numbikesavailable": True,
            "mechanical": True,
            "ebike": True,
            "commune": True,
            "stationcode": True,
        },
        zoom=11,
        height=500,
    )
    fig_map.update_layout(
        mapbox_style="open-street-map",
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
    )
    st.plotly_chart(fig_map, use_container_width=True, key="map_stations")

# Série temporelle
st.subheader("Série temporelle – total de vélos disponibles (par heure)")

ts_data = get_timeseries_total_bikes()
if ts_data:
    # On enlève éventuellement le point avec _id = None
    ts_clean = [d for d in ts_data if d["_id"] is not None]
    df_ts = pd.DataFrame(
        [{"timestamp": d["_id"], "total_bikes": d["total_bikes"]} for d in ts_clean]
    ).sort_values("timestamp")
    st.line_chart(df_ts, x="timestamp", y="total_bikes")

# Prévisions du nombre de vélos
st.subheader("Prévision globale du nombre de vélos (LinReg vs RandomForest)")

forecast_res = get_forecast_total_bikes()
if forecast_res is not None:
    df_hist = forecast_res["history"].copy()

    df_plot = pd.DataFrame({
        "timestamp": pd.concat([df_hist["timestamp"], df_hist["timestamp"], df_hist["timestamp"]]),
        "value": pd.concat([df_hist["total_bikes"], df_hist["pred_lin"], df_hist["pred_rf"]]),
        "type": (["observé"] * len(df_hist)
                 + ["prédit (linéaire)"] * len(df_hist)
                 + ["prédit (RandomForest)"] * len(df_hist)),
    })

    st.line_chart(df_plot, x="timestamp", y="value", color="type")

    st.write(f"RMSE régression linéaire : {forecast_res['rmse_lin']:.2f}")
    st.write(f"RMSE RandomForest : {forecast_res['rmse_rf']:.2f}")
    st.write(
        f"Prochaine prédiction linéaire : {forecast_res['next_pred_lin']:.1f} vélos, "
        f"RandomForest : {forecast_res['next_pred_rf']:.1f} vélos."
    )
else:
    st.write("Pas encore assez de données historiques pour calculer une prévision.")

# TOp 10 des stations par vélo
top_stations = get_top_stations(limit=10)
if top_stations:
    st.subheader("Top 10 stations par vélos disponibles")
    df_st = pd.DataFrame(top_stations)
    df_st["station"] = df_st["stationcode"] + " - " + df_st["name"]
    st.bar_chart(df_st, x="station", y="avg_bikes")  # ou sum_bikes

    st.subheader("Répartition des vélos pour les 10 stations (camembert)")
    fig_pie = px.pie(
        df_st,
        names="station",         # labels des parts
        values="avg_bikes",      # ou "sum_bikes"
        title="Top 10 stations – part des vélos disponibles",
    )
    st.plotly_chart(fig_pie, use_container_width=True, key="pie_top10")

    #Histogramme des capacités des stations
    st.subheader("Histogramme des capacités des stations")

    stations = get_all_stations()
    if stations:
        df_cap = pd.DataFrame(stations)
        if "capacity" in df_cap.columns:
            # On enlève les valeurs manquantes
            df_cap = df_cap.dropna(subset=["capacity"])
            st.bar_chart(df_cap["capacity"].value_counts().sort_index())

    # Histogramme des heures (hour)
    st.subheader("Distribution des vélos par heure de la journée")

    ts_data = get_timeseries_total_bikes()
    if ts_data:
        df_ts = pd.DataFrame(
            [{"timestamp": d["_id"], "total_bikes": d["total_bikes"]} for d in ts_data if d["_id"] is not None]
        ).sort_values("timestamp")
        df_ts["hour"] = df_ts["timestamp"].dt.hour

        # moyenne des vélos par heure
        df_hour = df_ts.groupby("hour", as_index=False)["total_bikes"].mean()
        st.bar_chart(df_hour, x="hour", y="total_bikes")


    #Semaine vs weekend (is_weekend)
    st.subheader("Semaine vs week-end")

    df_ts["weekday"] = df_ts["timestamp"].dt.weekday
    df_ts["is_weekend"] = df_ts["weekday"].isin([5, 6]).astype(int)

    df_we = df_ts.groupby("is_weekend", as_index=False)["total_bikes"].mean()
    df_we["type"] = df_we["is_weekend"].map({0: "Semaine", 1: "Week-end"})

    st.bar_chart(df_we, x="type", y="total_bikes")

    #Jour de la semaine (weekend)
    st.subheader("Moyenne des vélos par jour de la semaine")

    df_wd = df_ts.groupby("weekday", as_index=False)["total_bikes"].mean()
    # option : mapper 0..6 vers noms de jours
    days = {0: "Lun", 1: "Mar", 2: "Mer", 3: "Jeu", 4: "Ven", 5: "Sam", 6: "Dim"}
    df_wd["day"] = df_wd["weekday"].map(days)

    st.bar_chart(df_wd, x="day", y="total_bikes")

st.subheader("Effet de l'heure et du week-end sur le nombre de vélos")

ts_data = get_timeseries_total_bikes()
if ts_data:
    df_ts = pd.DataFrame(
        [{"timestamp": d["_id"], "total_bikes": d["total_bikes"]} for d in ts_data if d["_id"] is not None]
    ).sort_values("timestamp")

    df_ts["hour"] = df_ts["timestamp"].dt.hour
    df_ts["weekday"] = df_ts["timestamp"].dt.weekday
    df_ts["is_weekend"] = df_ts["weekday"].isin([5, 6]).astype(int)
    df_ts["week_type"] = df_ts["is_weekend"].map({0: "Semaine", 1: "Week-end"})

    fig = px.scatter(
        df_ts,
        x="timestamp",
        y="total_bikes",
        color="week_type",      # Semaine vs week-end
        size="hour",            # Heure → taille du point
        hover_data=["hour", "weekday"],
        title="Total de vélos en fonction du temps (heure + semaine/week-end)",
    )
    st.plotly_chart(fig, use_container_width=True, key="scatter_hour_weekend")

    #Stations souvent vides (Top 10)
    st.subheader("Stations souvent vides (top 10)")

    emptiness = get_station_emptiness(limit=10)
    if emptiness:
        df_empty = pd.DataFrame(emptiness)
        df_empty["station"] = df_empty["stationcode"] + " - " + df_empty["name"]
        st.dataframe(df_empty[["station", "pct_empty", "pct_full", "total_snapshots"]])
        st.bar_chart(df_empty, x="station", y="pct_empty")


    #  Prévision par station avec selectbox
    st.subheader("Prévision par station")

    stations = get_all_stations()
    if stations:
        df_st_all = pd.DataFrame(stations)
        codes = sorted(df_st_all["stationcode"].unique())
        code = st.selectbox("Choisir une station", options=codes)

        ts_station = get_timeseries_for_station(code)
        ts_station = [d for d in ts_station if d["_id"] is not None]

        if len(ts_station) >= 3:
            df_s = pd.DataFrame(
                [{"timestamp": d["_id"], "bikes": d["bikes"]} for d in ts_station]
            ).sort_values("timestamp")
            df_s["t"] = range(len(df_s))

            X = df_s[["t"]].values
            y = df_s["bikes"].values

            model = LinearRegression()
            model.fit(X, y)

            df_s["pred"] = model.predict(X)
            next_pred = model.predict([[len(df_s)]])[0]

            st.line_chart(df_s[["timestamp", "bikes"]].set_index("timestamp"))
            st.line_chart(df_s[["timestamp", "pred"]].set_index("timestamp"))

            st.write(f"Station {code} : prédiction prochaine valeur ≈ {next_pred:.1f} vélos.")
        else:
            st.write("Pas encore assez d'historique pour cette station.")