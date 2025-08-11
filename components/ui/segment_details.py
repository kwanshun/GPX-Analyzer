import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import LineCollection

def show_segment_summary_and_details(df, full_df, kind="climb"):
    """Display detailed segment (climb/descent) summaries with slope distribution and elevation profile."""
    
    # Required columns check
    required_cols = [
        "start_km", "end_km", "length_m", "avg_slope",
        "min_slope", "max_slope", "category", "start_idx", "end_idx"
    ]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        st.error(f"Missing columns in {kind} DataFrame: {', '.join(missing)}")
        return
    
    if df.empty:
        st.info(f"No {kind}s detected.")
        return

    for idx, row in df.reset_index(drop=True).iterrows():
        elev_change = row.get("elev_gain", row.get("elev_loss", 0))
        title = f"{kind.capitalize()} {idx+1} • {row['length_m']:.0f} m, {elev_change:.0f} m"

        summary = (
            f"📍 **Start:** {row['start_km']:.2f} km\n"
            f"🏁 **End:** {row['end_km']:.2f} km\n"
            f"📏 **Length:** {row['length_m']:.0f} m\n"
            f"⛰️ **Gain/Loss:** {elev_change:.1f} m\n"
            f"📐 **Average Slope:** {row['avg_slope']:.1f} %\n"
            f"📉 **Min Slope:** {row['min_slope']:.1f} %\n"
            f"📈 **Max Slope:** {row['max_slope']:.1f} %\n"
            f"🏷️ **Category:** {row['category']}"
        )

        with st.expander(f"🔽 {title}"):
            st.markdown(summary)
            
            if "plot_grade" in full_df.columns:
                # Extract segment data
                segment_df = full_df.iloc[int(row["start_idx"]):int(row["end_idx"]) + 1]
                st.write(segment_df.columns)
                st.write("Segment DataFrame columns:", list(segment_df.columns))
                # Create two plots side-by-side, slightly taller to fit colorbar
                fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))

                # Left: slope histogram
                ax1.hist(segment_df["plot_grade"], bins=15, color="gray", edgecolor="black")
                ax1.set_xlabel("Slope (%)")
                ax1.set_ylabel("Frequency")
                ax1.set_title("Slope Distribution")
                ax1.grid(True, linestyle='--', alpha=0.6)

                # Right: elevation profile, colored by slope
                # <<< CAMBIO: Se busca la columna 'ele' en lugar de 'elevation'
                if "ele" in segment_df.columns and not segment_df.empty: 
                    x = (segment_df["distance_km"] - segment_df["distance_km"].iloc[0]).values
                    # <<< CAMBIO: Se usan los datos de la columna 'ele'
                    y = segment_df["ele"].values 
                    slope = segment_df["plot_grade"].values

                    # Create a series of line segments for coloring
                    points = np.array([x, y]).T.reshape(-1, 1, 2)
                    segments = np.concatenate([points[:-1], points[1:]], axis=1)
                    
                    # Use the average slope of each segment for its color
                    segment_slopes = (slope[:-1] + slope[1:]) / 2

                    # Choose a colormap based on whether it's a climb or descent
                    if kind == "climb":
                        cmap = plt.get_cmap('Reds')
                        # Normalize colors based on typical climb slopes, ignoring extreme outliers
                        norm = plt.Normalize(vmin=0, vmax=max(10, np.percentile(segment_slopes, 98)))
                    else: # descent
                        cmap = plt.get_cmap('Greens_r')
                        # Normalize colors based on typical descent slopes
                        norm = plt.Normalize(vmin=min(-10, np.percentile(segment_slopes, 2)), vmax=0)

                    # Create the colored line collection
                    lc = LineCollection(segments, cmap=cmap, norm=norm, linewidth=3)
                    lc.set_array(segment_slopes)
                    line = ax2.add_collection(lc)

                    # Add a shaded area underneath the profile
                    ax2.fill_between(x, y, y.min(), color='gray', alpha=0.15)
                    
                    # Set axis limits and labels
                    ax2.set_xlim(x.min(), x.max())
                    ax2.set_ylim(y.min() - 5, y.max() + 5) # Add padding
                    ax2.set_xlabel("Distance (km)")
                    ax2.set_ylabel("Elevation (m)")
                    ax2.set_title("Elevation Profile")
                    ax2.grid(True, linestyle='--', alpha=0.6)

                    # Add a colorbar to explain the line colors
                    cbar = fig.colorbar(line, ax=ax2)
                    cbar.set_label('Slope (%)')

                else:
                    st.write(segment_df.columns)
                    ax2.text(0.5, 0.5, "No elevation data", ha="center", va="center", fontsize=10)
                    ax2.set_axis_off()

                plt.tight_layout()
                st.pyplot(fig)
            else:
                st.warning("No 'plot_grade' column found in full_df.")