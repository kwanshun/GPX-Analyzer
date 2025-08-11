import folium
from streamlit_folium import st_folium

from components.core.utils import get_color
from components.ui.elevation_chart import get_smoothed_grade


def update_display_route_map(
    df,
    tile_style: str = "OpenStreetMap",
    climbs_df=None,
    descents_df=None,
    color_by_slope: bool = True,
) -> None:
    df["plot_grade"] = get_smoothed_grade(df)
    coords = df[["lat", "lon"]].values.tolist()

    # Map center and bounds
    center = coords[len(coords) // 2]
    m = folium.Map(location=center, zoom_start=13, control_scale=True, tiles=None)

    folium.TileLayer(tiles=tile_style, name=tile_style, opacity=0.3).add_to(m)

    # Segment coloring
    for i in range(1, len(coords)):
        segment = [coords[i - 1], coords[i]]
        color = get_color(df["plot_grade"].iloc[i]) if color_by_slope else "#999999"
        folium.PolyLine(segment, color=color, weight=4, opacity=1).add_to(m)

    # Start and end markers
    folium.Marker(
        coords[0], icon=folium.Icon(color="green", icon="play"), popup="Start"
    ).add_to(m)
    folium.Marker(
        coords[-1], icon=folium.Icon(color="red", icon="stop"), popup="End"
    ).add_to(m)

    # Climb markers
    if climbs_df is not None and not climbs_df.empty:
        for idx, row in climbs_df.iterrows():
            mid_idx = (row["start_idx"] + row["end_idx"]) // 2
            lat, lon = df.loc[mid_idx, ["lat", "lon"]]
            folium.Marker(
                location=[lat, lon],
                popup=f"Climb {idx + 1}: {int(row['elev_gain'])}m ↑",
                icon=folium.DivIcon(
                    html=f"<div style='font-size: 12px; color: red;'>{idx + 1}</div>"
                ),
            ).add_to(m)

    # Descent markers
    if descents_df is not None and not descents_df.empty:
        for idx, row in descents_df.iterrows():
            mid_idx = (row["start_idx"] + row["end_idx"]) // 2
            lat, lon = df.loc[mid_idx, ["lat", "lon"]]
            folium.Marker(
                location=[lat, lon],
                popup=f"Descent {idx + 1}: {int(row['elev_loss'])}m ↓",
                icon=folium.DivIcon(
                    html=f"<div style='font-size: 12px; color: blue;'>{idx + 1}</div>"
                ),
            ).add_to(m)

    folium.LayerControl().add_to(m)

    # Fit to bounds
    sw = df[["lat", "lon"]].min().values.tolist()
    ne = df[["lat", "lon"]].max().values.tolist()
    m.fit_bounds([sw, ne])

    try:
        st_folium(
            m,
            width=800,
            height=500,
            use_container_width=True,
            key="main_map",
            return_last_map=False,
        )
    except TypeError:
        st_folium(m, width=800, height=500, key="main_map")
