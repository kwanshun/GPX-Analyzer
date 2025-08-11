import numpy as np


def get_color(grade) -> str:
    if grade >= 18:
        return "#8B0000"  # Dark Red
    elif grade >= 10:
        return "#FF8C00"  # Dark Orange
    elif grade >= 2:
        return "#FFFF00"  # Yellow
    elif grade >= 0:
        return "#ADFF2F"  # GreenYellow
    elif grade >= -2:
        return "#ADD8E6"  # LightBlue
    elif grade >= -10:
        return "#0000FF"  # Blue
    else:
        return "#00008B"  # Dark Blue


def get_color_from_palette(grade):
    """
    Asigna un color desde una paleta divergente profesional basada en la pendiente.
    - Bajadas: Azul
    - Llano: Gris claro
    - Subidas: Amarillo -> Naranja -> Rojo oscuro
    """
    palette = [
        "#0d0887",  # Morado/Azul oscuro (Bajada > 12%)
        "#0000FF",  # Azul (Bajada 6-12%)
        "#ADD8E6",  # Azul claro (Bajada 0-6%)
        "#E0E0E0",  # Gris claro (Llano -1% a 1%)
        "#FFFF00",  # Amarillo (Subida 1-4%)
        "#FFA500",  # Naranja (Subida 4-8%)
        "#FF4500",  # Rojo-Naranja (Subida 8-12%)
        "#B22222",  # Ladrillo (Subida 12-16%)
        "#8B0000",  # Rojo Oscuro (Subida > 16%)
    ]
    grade_bins = np.array([-15, -8, -3, -1, 1, 4, 8, 12, 20])
    idx = np.interp(grade, grade_bins, range(len(palette)))

    color_idx = int(round(idx))

    return palette[color_idx]


def apply_slope_smoothing(df, target_meters: int = 300):
    meters_per_point = df["distance"].iloc[-1] / len(df)
    # Evitar una ventana demasiado grande o demasiado pequeña
    if meters_per_point == 0:
        return df  # No se puede calcular
    window = max(3, int(target_meters / meters_per_point))
    # Asegurarse de que la ventana sea un número impar para que el centro sea claro
    if window % 2 == 0:
        window += 1

    df["plot_grade"] = (
        df["grade"].rolling(window=window, center=True, min_periods=1).mean()
    )
    return df


def classify_climb_category(length_m, avg_slope) -> str:
    length_km = length_m / 1000
    if length_km >= 10 and avg_slope >= 6:
        return "Hors Catégorie"
    elif length_km >= 8 and avg_slope >= 5:
        return "Category 1"
    elif length_km >= 5 and avg_slope >= 4:
        return "Category 2"
    elif length_km >= 3 and avg_slope >= 3:
        return "Category 3"
    elif length_km >= 2 and avg_slope >= 3:
        return "Category 4"
    elif length_km >= 1 and avg_slope >= 2:
        return "Category 5"
    elif length_km >= 0.5 and avg_slope >= 1:
        return "Category 6"
    else:
        return "Uncategorized"


def classify_climb_category_strava(length_m, avg_slope) -> str:
    """
    Clasifica una subida usando un sistema de puntuación similar al de Strava.
    Puntuación = Longitud (metros) * Pendiente (%)
    """
    if length_m <= 0 or avg_slope < 3.0:
        return "Uncategorized"

    score = length_m * avg_slope

    if score >= 80000:
        return "HC (Hors Catégorie)"
    elif score >= 64000:
        return "Cat 1"
    elif score >= 32000:
        return "Cat 2"
    elif score >= 16000:
        return "Cat 3"
    elif score >= 8000:
        return "Cat 4"
    else:
        return "Uncategorized"
