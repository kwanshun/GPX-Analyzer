import gpxpy
import numpy as np
import pandas as pd
from haversine import haversine_vector, Unit  # <-- Cambio clave: importamos haversine

from .stats import compute_gpx_stats

# --- NUEVA FUNCIÓN AUXILIAR PARA EVITAR REPETIR CÓDIGO ---
def _add_distance_and_grade(df):
    """
    Calcula de forma vectorizada la distancia, distancia acumulada y pendiente.
    Modifica el DataFrame de entrada añadiendo estas columnas.
    """
    coords = df[["lat", "lon"]].to_numpy()

    # 1. Cálculo de distancia VECTORIZADO (mucho más rápido)
    distances_segment = np.zeros(len(df))
    # Calcula todas las distancias entre puntos consecutivos de una sola vez
    distances_segment[1:] = haversine_vector(coords[:-1], coords[1:], unit=Unit.METERS)

    # 2. Suma acumulada para distancia total
    df["distance"] = np.cumsum(distances_segment)

    # 3. Cálculo de pendiente
    elev_diff = np.diff(df["ele"], prepend=df["ele"].iloc[0])
    with np.errstate(divide="ignore", invalid="ignore"):
        df["grade"] = np.where(distances_segment > 0, (elev_diff / distances_segment) * 100, 0)
    
    return df
# --- FIN DE LA FUNCIÓN AUXILIAR ---


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

    # --- FLUJO DE PROCESADO SIMPLIFICADO ---
    # 1. Primer cálculo (rápido) para poder reducir puntos
    df = _add_distance_and_grade(df)

    # 2. Reducción de puntos (la función es la misma)
    df = reduce_points_by_density(df, max_points_per_km)

    # 3. Recálculo final (rápido) sobre los datos ya reducidos
    df = _add_distance_and_grade(df)
    # --- FIN DEL FLUJO SIMPLIFICADO ---

    time_deltas = pd.to_datetime(df["time"]).diff().dt.total_seconds().fillna(0)
    df["duration_sec"] = np.where(time_deltas < 3600, time_deltas, 0)

    stats = compute_gpx_stats(df)
    return df, stats


def reduce_points_by_density(df, max_points_per_km):
    # Esta función ya era eficiente y no necesita cambios.
    total_km = df["distance"].iloc[-1] / 1000
    if total_km == 0:  # Evitar división por cero si la distancia es nula
        return df

    max_points = int(total_km * max_points_per_km)
    if len(df) <= max_points or max_points == 0:
        return df
        
    step = max(1, len(df) // max_points)
    return df.iloc[::step].reset_index(drop=True)