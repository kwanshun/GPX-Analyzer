# components/core/climb_detector.py
import pandas as pd

def detect_significant_segments(
    df,
    kind="climb",
    # --- Nuevos parámetros para el control del usuario ---
    start_threshold_slope=2.0,  # Pendiente mínima para empezar a considerar una subida
    end_threshold_slope=1.0,    # Si la pendiente baja de esto, entramos en "pausa"
    max_pause_length_m=200,     # Si el descansillo dura más de esto, se acaba la subida
    max_pause_descent_m=10,     # Si perdemos más de esta elevación, se acaba la subida
):
    segments = []
    state = "SEARCHING"
    
    # Signo para diferenciar entre subidas (1) y bajadas (-1)
    slope_sign = 1 if kind == "climb" else -1
    
    start_idx = 0
    current_segment_points = []

    for i in range(1, len(df)):
        point_data = df.iloc[i]
        slope = point_data["plot_grade"] * slope_sign
        elev_diff = (df["ele"].iloc[i] - df["ele"].iloc[i - 1]) * slope_sign
        dist_diff = point_data["distance"] - df["distance"].iloc[i - 1]

        # ---- MÁQUINA DE ESTADOS ----
        if state == "SEARCHING":
            if slope >= start_threshold_slope:
                state = "IN_CLIMB"
                start_idx = i - 1
                current_segment_points = [df.iloc[i-1].to_dict(), point_data.to_dict()] # Empezamos con 2 puntos
        
        elif state == "IN_CLIMB":
            if slope >= end_threshold_slope:
                # La subida continúa, añadimos el punto
                current_segment_points.append(point_data.to_dict())
            else:
                # La pendiente ha bajado, iniciamos una posible pausa
                state = "EVALUATING_PAUSE"
                pause_start_idx = i -1
                pause_length = 0
                pause_descent = 0
                current_segment_points.append(point_data.to_dict())

        elif state == "EVALUATING_PAUSE":
            current_segment_points.append(point_data.to_dict())
            pause_length += dist_diff
            if elev_diff < 0: # Solo contamos el desnivel negativo
                pause_descent += abs(elev_diff)

            # Criterio 1: La pendiente vuelve a subir, la pausa termina y la subida continúa
            if slope >= end_threshold_slope:
                state = "IN_CLIMB"

            # Criterio 2 y 3: La pausa es demasiado larga o hemos bajado demasiado
            elif pause_length > max_pause_length_m or pause_descent > max_pause_descent_m:
                # Fin de la subida. Guardamos el segmento ANTES de la pausa
                final_segment_df = pd.DataFrame(current_segment_points[:-(i - pause_start_idx)])
                # Aquí validaríamos y guardaríamos el segmento si cumple los requisitos (longitud, desnivel...)
                _validate_and_append_segment(segments, final_segment_df, kind, start_idx)

                # Volvemos a buscar una nueva subida
                state = "SEARCHING"
                current_segment_points = []

    # Al final del bucle, comprobar si estábamos en medio de una subida
    if state in ["IN_CLIMB", "EVALUATING_PAUSE"] and current_segment_points:
         _validate_and_append_segment(segments, pd.DataFrame(current_segment_points), kind, start_idx)

    return pd.DataFrame(segments)


def _validate_and_append_segment(segments_list, segment_df, kind, start_idx, min_gain=20, min_length=300):
    """Función auxiliar para no repetir código de validación."""
    if segment_df.empty or len(segment_df) < 2:
        return
        
    length = segment_df["distance"].iloc[-1] - segment_df["distance"].iloc[0]
    
    if kind == 'climb':
        gain = segment_df[segment_df['ele'].diff() > 0]['ele'].diff().sum()
    else: # descent
        gain = abs(segment_df[segment_df['ele'].diff() < 0]['ele'].diff().sum())

    if length > min_length and gain > min_gain:
        avg_slope = (gain / length) * 100 if length > 0 else 0
        end_idx = start_idx + len(segment_df) -1
        
        segments_list.append({
            "type": kind,
            "start_km": segment_df["distance"].iloc[0] / 1000,
            "end_km": segment_df["distance"].iloc[-1] / 1000,
            "elev_gain" if kind == "climb" else "elev_loss": gain,
            "length_m": length,
            "avg_slope": avg_slope if kind == 'climb' else -avg_slope,
            "start_idx": start_idx,
            "end_idx": end_idx,
        })