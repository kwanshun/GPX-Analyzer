import matplotlib.pyplot as plt
import streamlit as st


def show_segment_summary_and_details(df, full_df, kind: str = "climb") -> None:
    if df.empty:
        st.info(f"No {kind}s detected.")
        return

    for i, row in df.iterrows():
        title = (
            f"{kind.capitalize()} {i+1} • {row['length_m']:.0f} m, "
            f"{row.get('elev_gain', row.get('elev_loss', 0)):.0f} m"
        )
        summary = (
            f"**Start:** {row['start_km']:.2f} km\n"
            f"**End:** {row['end_km']:.2f} km\n"
            f"**Length:** {row['length_m']:.0f} m\n"
            f"**Elevation Gain/Loss:** {row.get('elev_gain', row.get('elev_loss', 0)):.1f} m\n"
            f"**Average Slope:** {row['avg_slope']:.1f} %\n"
            f"**Minimum Slope:** {row['min_slope']:.1f} %\n"
            f"**Maximum Slope:** {row['max_slope']:.1f} %\n"
            f"**Category:** {row['category']}"
        )

        with st.expander(f"{title}"):
            st.markdown(summary)
            st.markdown("**Slope Distribution in Segment:**")

            grades = full_df["plot_grade"].iloc[row["start_idx"]:row["end_idx"]+1]
            distance = full_df["distance_km"].iloc[row["start_idx"]:row["end_idx"]+1]
            elevation = full_df["elevation_m"].iloc[row["start_idx"]:row["end_idx"]+1]

            col1, col2 = st.columns(2)

            with col1:
                fig1, ax1 = plt.subplots(figsize=(5, 2.5))
                ax1.hist(grades, bins=15, color="gray", edgecolor="black")
                ax1.set_xlabel("Slope (%)")
                ax1.set_ylabel("Frequency")
                ax1.set_title("Slope Histogram")
                st.pyplot(fig1)

            with col2:
                fig2, ax2 = plt.subplots(figsize=(5, 2.5))
                ax2.plot(distance, elevation, color="blue")
                ax2.set_xlabel("Distance (km)")
                ax2.set_ylabel("Elevation (m)")
                ax2.set_title("Profile Chart")
                st.pyplot(fig2)
