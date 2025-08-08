import altair as alt
import folium
import numpy as np
import pandas as pd
import streamlit as st
from geopy.distance import geodesic
from streamlit_folium import st_folium


def run_pace_analysis(df) -> None:
    st.title("🏃‍♂️ Pace & Speed Analyzer")

    if (
        df.empty
        or "lat" not in df.columns
        or "lon" not in df.columns
        or "time" not in df.columns
    ):
        st.warning("GPX data is missing required columns.")
        return

    df = df.copy()
    df["timestamp"] = pd.to_datetime(df["time"], errors="coerce")
    df = df.dropna(subset=["timestamp"])

    df["seconds"] = (df["timestamp"] - df["timestamp"].iloc[0]).dt.total_seconds()
    df["distance"] = [0.0] + [
        geodesic(
            (df.loc[i - 1, "lat"], df.loc[i - 1, "lon"]),
            (df.loc[i, "lat"], df.loc[i, "lon"]),
        ).meters
        for i in range(1, len(df))
    ]
    df["cum_dist"] = df["distance"].cumsum()
    df["speed_kmh"] = (
        df["distance"] / df["seconds"].diff().replace(0, np.nan).fillna(1) * 3.6
    )
    df["pace_min_per_km"] = 60 / df["speed_kmh"].replace(0, np.nan)

    st.markdown("### 📈 Speed and Pace Over Time")

    st.altair_chart(
        alt.Chart(df)
        .mark_line(color="steelblue")
        .encode(
            x=alt.X("seconds", title="Time (s)"),
            y=alt.Y("speed_kmh", title="Speed (km/h)"),
        )
        .properties(title="Speed over Time", height=250),
        use_container_width=True,
    )

    st.altair_chart(
        alt.Chart(df)
        .mark_line(color="darkred")
        .encode(
            x=alt.X("seconds", title="Time (s)"),
            y=alt.Y("pace_min_per_km", title="Pace (min/km)"),
        )
        .properties(title="Pace over Time", height=250),
        use_container_width=True,
    )

    st.markdown("### 🔁 Route Colored by Speed")

    m = folium.Map(location=[df["lat"].mean(), df["lon"].mean()], zoom_start=13)

    for i in range(len(df) - 1):
        lat1, lon1 = df.loc[i, ["lat", "lon"]]
        lat2, lon2 = df.loc[i + 1, ["lat", "lon"]]
        spd = df.loc[i, "speed_kmh"]
        color = "green" if spd < 8 else "orange" if spd < 14 else "red"
        folium.PolyLine(
            [(lat1, lon1), (lat2, lon2)], color=color, weight=4, opacity=0.9
        ).add_to(m)

    st_folium(m, width=1000, height=500)

    st.markdown("### 📏 Pacing Consistency by km")

    df["km_bin"] = (df["cum_dist"] // 1000).astype(int)
    grouped = df.groupby("km_bin")["pace_min_per_km"].agg(["mean", "std"]).reset_index()
    grouped.columns = ["km_segment", "mean_pace", "std_pace"]

    st.dataframe(grouped, use_container_width=True)

    st.altair_chart(
        alt.Chart(grouped)
        .mark_bar()
        .encode(
            x=alt.X("km_segment:O", title="Kilometer Segment"),
            y=alt.Y("mean_pace", title="Avg Pace (min/km)"),
            color=alt.value("#F63366"),
        )
        .properties(title="Average Pace per km", height=250),
        use_container_width=True,
    )

    cv = grouped["std_pace"].mean() / grouped["mean_pace"].mean()
    st.markdown(
        f"**Coefficient of Variation:** {cv:.2%} — lower means more consistent pacing"
    )
