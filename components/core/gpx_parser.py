import gpxpy
import numpy as np
import pandas as pd
from geopy.distance import geodesic

from .stats import compute_gpx_stats


def parse_gpx(gpx_content, max_points_per_km=20):
    gpx = gpxpy.parse(gpx_content)
    data = []

    for track in gpx.tracks:
        for segment in track.segments:
            for point in segment.points:
                data.append(
                    {
                        "lat": point.latitude,
                        "lon": point.longitude,
                        "ele": point.elevation,
                        "time": point.time,
                    }
                )

    df = pd.DataFrame(data)
    if len(df) < 2:
        raise ValueError("GPX file too short")

    coords = df[["lat", "lon"]].to_numpy()
    distances = np.array(
        [
            geodesic(coords[i - 1], coords[i]).meters if i > 0 else 0
            for i in range(len(coords))
        ]
    )
    df["distance"] = np.cumsum(distances)

    df = reduce_points_by_density(df, max_points_per_km)

    coords = df[["lat", "lon"]].to_numpy()
    distances = np.array(
        [
            geodesic(coords[i - 1], coords[i]).meters if i > 0 else 0
            for i in range(len(coords))
        ]
    )
    df["distance"] = np.cumsum(distances)

    elev_diff = np.diff(df["ele"], prepend=df["ele"].iloc[0])
    with np.errstate(divide="ignore", invalid="ignore"):
        df["grade"] = np.where(distances > 0, (elev_diff / distances) * 100, 0)

    time_deltas = pd.to_datetime(df["time"]).diff().dt.total_seconds().fillna(0)
    df["duration_sec"] = np.where(time_deltas < 3600, time_deltas, 0)  # filtra outliers

    stats = compute_gpx_stats(df)
    return df, stats


def reduce_points_by_density(df, max_points_per_km):
    total_km = df["distance"].iloc[-1] / 1000
    max_points = int(total_km * max_points_per_km)
    if len(df) <= max_points:
        return df
    step = max(1, len(df) // max_points)
    return df.iloc[::step].reset_index(drop=True)
