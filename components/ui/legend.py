# components/ui/legend.py
from streamlit.components.v1 import html

def display_legend():
    legend_html = """
    <div style='padding:10px; background-color:rgba(255,255,255,0.8); border-radius:8px; 
                border: 1px solid #E0E0E0; font-size:14px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.12); width: fit-content;'>
        <b>Slope Legend (%)</b><br>
        <div style="display: flex; align-items: center; margin-top: 4px;">
            <span style='background:#8B0000; width:20px; height: 18px; display:inline-block;'></span>
            <span style="margin-left: 8px;">≥ 16%</span>
        </div>
        <div style="display: flex; align-items: center; margin-top: 4px;">
            <span style='background:#B22222; width:20px; height: 18px; display:inline-block;'></span>
            <span style="margin-left: 8px;">12% to 16%</span>
        </div>
        <div style="display: flex; align-items: center; margin-top: 4px;">
            <span style='background:#FF4500; width:20px; height: 18px; display:inline-block;'></span>
            <span style="margin-left: 8px;">8% to 12%</span>
        </div>
        <div style="display: flex; align-items: center; margin-top: 4px;">
            <span style='background:#FFA500; width:20px; height: 18px; display:inline-block;'></span>
            <span style="margin-left: 8px;">4% to 8%</span>
        </div>
        <div style="display: flex; align-items: center; margin-top: 4px;">
            <span style='background:#FFFF00; width:20px; height: 18px; display:inline-block;'></span>
            <span style="margin-left: 8px;">1% to 4%</span>
        </div>
        <div style="display: flex; align-items: center; margin-top: 4px;">
            <span style='background:#E0E0E0; width:20px; height: 18px; display:inline-block;'></span>
            <span style="margin-left: 8px;">-1% to 1% (Flat)</span>
        </div>
        <div style="display: flex; align-items: center; margin-top: 4px;">
            <span style='background:#ADD8E6; width:20px; height: 18px; display:inline-block;'></span>
            <span style="margin-left: 8px;">-6% to 0%</span>
        </div>
        <div style="display: flex; align-items: center; margin-top: 4px;">
            <span style='background:#0000FF; width:20px; height: 18px; display:inline-block;'></span>
            <span style="margin-left: 8px;">-12% to -6%</span>
        </div>
        <div style="display: flex; align-items: center; margin-top: 4px;">
            <span style='background:#0d0887; width:20px; height: 18px; display:inline-block;'></span>
            <span style="margin-left: 8px;">≤ -12%</span>
        </div>
    </div>
    """
    html(legend_html, height=310)