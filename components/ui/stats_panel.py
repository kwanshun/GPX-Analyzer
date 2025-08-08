import streamlit as st


def show_stats(stats) -> None:
    st.markdown(
        f"""
    **Total Distance:** {stats["total_distance_km"]:.2f} km  
    **Elevation Gain:** {stats["elevation_gain"]:.1f} m  
    **Elevation Loss:** {stats["elevation_loss"]:.1f} m  
    **Min Elevation:** {stats["min_elevation"]:.1f} m  
    **Max Elevation:** {stats["max_elevation"]:.1f} m  
    **Average Grade:** {stats["average_grade"]:.2f} %  
    **Max Grade:** {stats["max_grade"]:.2f} %  
    **Moving Time:** {stats["moving_time_min"]:.1f} min  
    **Total Time:** {stats["total_time_min"]:.1f} min  
    **Number of Points:** {stats["num_points"]}  
    **Point Density:** {stats["point_density_km"]:.1f} pts/km  
    **Precision Score:** {stats["precision_score"]:.1f} %
    """
    )
