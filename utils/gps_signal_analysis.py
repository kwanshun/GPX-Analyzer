import altair as alt
import branca.colormap as cm
import folium
import numpy as np
import pandas as pd
import requests
import streamlit as st
from folium.plugins import HeatMap
from geopy.distance import geodesic
from sklearn.neighbors import BallTree
from streamlit_folium import st_folium


def run_gps_signal_analysis(df, radius: int = 10) -> None:
    st.title("📡 GPS Signal Quality Analyzer")

    if df.empty:
        st.warning("No points found in GPX.")
        return

    # Reduce number of points (every 2nd point)
    df = df.iloc[::2].reset_index(drop=True)
    st.markdown(f"🔢 Points after reduction: {len(df)}")

    # ────── Bounding Box & Overpass Query
    min_lat, max_lat = df["lat"].min(), df["lat"].max()
    min_lon, max_lon = df["lon"].min(), df["lon"].max()
    bbox_key = f"{min_lat:.5f}-{min_lon:.5f}-{max_lat:.5f}-{max_lon:.5f}"

    if "building_cache" not in st.session_state:
        st.session_state["building_cache"] = {}

    if bbox_key in st.session_state["building_cache"]:
        buildings_df = st.session_state["building_cache"][bbox_key]
    else:
        query = f"""
        [out:json];
        (
            way["building"]({min_lat},{min_lon},{max_lat},{max_lon});
            relation["building"]({min_lat},{min_lon},{max_lat},{max_lon});
        );
        out center;
        """

        overpass_endpoints = [
            "http://overpass-api.de/api/interpreter",
            "https://overpass.kumi.systems/api/interpreter",
            "https://overpass.openstreetmap.ru/api/interpreter",
        ]

        response = None
        for endpoint in overpass_endpoints:
            try:
                response = requests.get(endpoint, params={"data": query}, timeout=25)
                response.raise_for_status()
                raw_data = response.json()
                break
            except Exception as e:
                st.warning(f"❌ Overpass endpoint failed: {endpoint} — {e}")
                continue

        if response is None:
            st.error("❌ All Overpass API endpoints failed. Try again later.")
            return

        buildings = []
        for el in raw_data["elements"]:
            lat_ = el.get("lat") or el.get("center", {}).get("lat")
            lon_ = el.get("lon") or el.get("center", {}).get("lon")
            if lat_ is None or lon_ is None:
                continue
            tags = el.get("tags", {})
            h = tags.get("height")
            l = tags.get("building:levels")
            height = None
            levels = None
            if h:
                try:
                    height = float(h)
                except:
                    pass
            if l and levels is None:
                try:
                    levels = int(l)
                except:
                    pass
            buildings.append(
                {"lat": lat_, "lon": lon_, "height": height, "levels": levels}
            )
        buildings_df = pd.DataFrame(buildings)
        st.session_state["building_cache"][bbox_key] = buildings_df

    if buildings_df.empty:
        st.warning("No buildings found in the area.")
        return

    # ────── Risk Calculation (using BallTree)
    earth_radius_m = 6371000
    radius_rad = radius / earth_radius_m

    tree = BallTree(np.radians(buildings_df[["lat", "lon"]].values), metric="haversine")
    risk_scores = []
    heatmap_data = []
    used_buildings_idx = set()

    building_heights = (
        buildings_df.apply(
            lambda row: (
                row["height"] if pd.notnull(row["height"]) else (row["levels"] or 0) * 3
            ),
            axis=1,
        )
        .fillna(0)
        .values
    )

    for _, row in df.iterrows():
        point_rad = np.radians([[row["lat"], row["lon"]]])
        ind = tree.query_radius(point_rad, r=radius_rad)[0]
        total_score = 0.0
        for i in ind:
            b_lat, b_lon = buildings_df.loc[i, ["lat", "lon"]]
            d = geodesic((row["lat"], row["lon"]), (b_lat, b_lon)).meters
            h = building_heights[i]
            if h > 0 and d > 1:
                total_score += h / d
                used_buildings_idx.add(i)
        heatmap_data.append([row["lat"], row["lon"], total_score])
        risk_scores.append(total_score)

    df["risk_score"] = (
        pd.Series(risk_scores).rolling(window=5, center=True).mean().bfill().ffill()
    )

    gps_score = "✅ High"
    danger_ratio = (df["risk_score"] >= 1.0).mean()
    if danger_ratio > 0.5:
        gps_score = "❌ Low"
    elif danger_ratio > 0.2:
        gps_score = "⚠️ Medium"

    st.markdown(f"### 📡 Estimated GPS Precision: {gps_score}")

    # ────── Map
    center = [df["lat"].mean(), df["lon"].mean()]
    m = folium.Map(location=center, zoom_start=14)

    for i in range(len(df) - 1):
        lat1, lon1 = df.loc[i, ["lat", "lon"]]
        lat2, lon2 = df.loc[i + 1, ["lat", "lon"]]
        avg_risk = (df.loc[i, "risk_score"] + df.loc[i + 1, "risk_score"]) / 2
        color = "green" if avg_risk < 0.5 else "orange" if avg_risk < 1.0 else "red"
        folium.PolyLine(
            [(lat1, lon1), (lat2, lon2)], color=color, weight=5, opacity=0.9
        ).add_to(m)

    filtered_buildings_df = buildings_df.iloc[list(used_buildings_idx)]

    heights = []
    for _, b in filtered_buildings_df.iterrows():
        h = b["height"] if pd.notnull(b["height"]) else (b["levels"] or 0) * 3
        if h > 0:
            heights.append(h)

    if len(heights) < 2:
        heights = [10, 100]
    min_h, max_h = float(min(heights)), float(max(heights))
    if min_h == max_h:
        min_h -= 1
        max_h += 1
    if min_h > max_h:
        min_h, max_h = max_h - 1, max_h

    colormap = cm.linear.YlOrRd_09.scale(min_h, max_h).to_step(n=10)
    colormap.caption = "Building Height (m)"
    colormap.add_to(m)

    for _, b in filtered_buildings_df.iterrows():
        h = b["height"] if pd.notnull(b["height"]) else (b["levels"] or 0) * 3
        color = colormap(h) if h else "#999999"
        folium.CircleMarker(
            location=[b["lat"], b["lon"]],
            radius=5,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.8,
        ).add_to(m)

    HeatMap(heatmap_data, radius=25, blur=15, max_zoom=17).add_to(m)

    st.markdown("### 🗺️ Map: Buildings & Risk Zones")
    st_folium(m, width=1000, height=600)

    st.markdown("### 📈 Risk Score by Point")
    st.altair_chart(
        alt.Chart(df.reset_index())
        .mark_line()
        .encode(
            x=alt.X("index", title="Point Index"),
            y=alt.Y("risk_score", title="Weighted Interference (Σ height / distance)"),
        )
        .properties(height=250, width=800),
        use_container_width=True,
    )

    st.markdown("### 📊 Histogram of GPS Risk Levels")
    df["risk_level"] = pd.cut(
        df["risk_score"],
        bins=[-1, 0.5, 1.0, float("inf")],
        labels=["Low", "Medium", "High"],
    )
    st.altair_chart(
        alt.Chart(df)
        .mark_bar()
        .encode(
            x=alt.X("risk_level:N", title="Risk Level"),
            y=alt.Y("count():Q", title="Number of Points"),
            color="risk_level:N",
        )
        .properties(height=250, width=600),
        use_container_width=True,
    )

    st.download_button(
        "⬇️ Download Buildings CSV",
        filtered_buildings_df.to_csv(index=False),
        file_name="buildings.csv",
    )
