import firebase_admin
from firebase_admin import credentials, firestore
from datetime import date, time, datetime, timedelta

import json
import os
import pandas as pd
import plotly.graph_objs as go
import streamlit as st

# --- Streamlit Config ---
st.set_page_config(layout="wide")

# --- Firebase Init ---
if not firebase_admin._apps:
    cert = json.loads(st.secrets["Certificate"]["data"])  # Ensure secrets.toml is properly configured
    cred = credentials.Certificate(cert)
    firebase_admin.initialize_app(cred)

db = firestore.client()

# --- Image Helper ---
def get_base64_image(image_path):
    import base64
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return None

# --- Fetch CTD Data ---
@st.cache_data(max_entries=10, persist=True, show_spinner=False)
def fetch_ctd_data(start_date: date, end_date: date):
    start_ts = int(datetime.combine(start_date, time.min).timestamp() * 1000)
    end_ts = int(datetime.combine(end_date + timedelta(days=1), time.min).timestamp() * 1000)

    docs = db.collection("CTD_Data").order_by("date").get()

    data = []
    for doc in docs:
        d = doc.to_dict()
        try:
            ts = d.get("date", {}).get("$date")
            if ts is None:
                continue
            record = {
                "datetime": datetime.fromtimestamp(ts / 1000),
                "instrument": d.get("instrument"),
                "lat": d.get("lat"),
                "lon": d.get("lon"),
                "depth1": d.get("depth1"),
                "oxygen": d.get("oxygen"),
                "conductivity": float(d.get("conductivity", "nan")),
                "par": float(d.get("par", "nan")),
                "pressure": float(d.get("pressure", "nan")),
                "salinity": float(d.get("salinity", "nan")),
                "temperature": float(d.get("temperature", "nan")),
                "turbidity": float(d.get("turbidity", "nan")),
            }
            data.append(record)
        except Exception as e:
            print(f"Error processing document: {e}")
            continue

    return pd.DataFrame(data) if data else None

# --- Sidebar Date Selection ---
st.sidebar.header("Select Date Range")
default_start = datetime.fromtimestamp(1745545207000 / 1000).date()
default_end = datetime.fromtimestamp(1746781807000 / 1000).date()
start = st.sidebar.date_input("Start Date", default_start)
end = st.sidebar.date_input("End Date", default_end)

# --- Main Title with Logos ---
logo_path = "images/OceanTech Logo-PURPLE.png"
base64_logo = get_base64_image(logo_path)
logo_html = f"<img src='data:image/png;base64,{base64_logo}' style='width:150px; height:auto;'>" if base64_logo else "⚠️ Logo Not Found"
st.markdown(
    f"""
    <div style="display: flex; align-items: center; justify-content: center; gap: 20px;">
        {logo_html}
        <h1 style='text-align: center; font-family:Georgia, serif; margin:0;'>UW ERIS CTD DATA</h1>
        {logo_html}
    </div>
    """,
    unsafe_allow_html=True
)

# --- Fetch & Filter Data --
data = fetch_ctd_data(start, end)
if data is None or data.empty:
    st.warning("No CTD data found for the selected date range.")
else:
    #filtered_data = data[(data["datetime"] >= pd.Timestamp(start)) & (data["datetime"] <= pd.Timestamp(end))]


    #CODE TO LINK GRAPH TO RAW DATA
    start_dt = pd.Timestamp(start)
    end_dt = pd.Timestamp(end) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
    filtered_data = data[(data["datetime"] >= start_dt) & (data["datetime"] <= end_dt)]


    # --- Graph ---
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=filtered_data["datetime"], y=filtered_data["temperature"], mode='lines', name='Temperature', line=dict(color='blue')))
    fig.add_trace(go.Scatter(x=filtered_data["datetime"], y=filtered_data["salinity"], mode='lines', name='Salinity', line=dict(color='orange')))
    fig.add_trace(go.Scatter(x=filtered_data["datetime"], y=filtered_data["par"], mode='lines', name='PAR', line=dict(color='green')))
    fig.add_trace(go.Scatter(x=filtered_data["datetime"], y=filtered_data["conductivity"], mode='lines', name='Conductivity', line=dict(color='purple')))
    fig.add_trace(go.Scatter(x=filtered_data["datetime"], y=filtered_data["oxygen"], mode='lines', name='Oxygen', line=dict(color='gold')))
    fig.add_trace(go.Scatter(x=filtered_data["datetime"], y=filtered_data["turbidity"], mode='lines', name='Turbidity', line=dict(color='red')))
    fig.add_trace(go.Scatter(x=filtered_data["datetime"], y=filtered_data["pressure"], mode='lines', name='Pressure', line=dict(color='black')))

    # --- Layout Styling ---
    fig.update_layout(
        xaxis_title="Time",
        yaxis_title="Values",
        width=800,
        height=450,
        xaxis=dict(
            rangeslider=dict(visible=True),
            type="date",
            rangeselector=dict(
                buttons=[
                    dict(count=1, label="1d", step="day", stepmode="backward"),
                    dict(count=7, label="1w", step="day", stepmode="backward"),
                    dict(count=1, label="1m", step="month", stepmode="backward"),
                    dict(count=6, label="6m", step="month", stepmode="backward"),
                    dict(step="all")
                ],
                x=0.5, y=1.15, xanchor='center', yanchor='bottom'
            )
        ),
        yaxis=dict(showgrid=True, gridcolor='lightgrey'),
        plot_bgcolor="white",
        paper_bgcolor="lightblue",
        font=dict(family="Georgia, serif", size=12, color="black"),
        legend=dict(
            x=1.05, y=0.5, xanchor='left', yanchor='middle',
            bgcolor='rgba(255, 255, 255, 0.5)'
        ),
        margin=dict(l=80, r=80, t=50, b=80),
        autosize=False
    )

    # --- Graph Display & Download ---
    center, = st.columns([1])  

    with center:  # Put all your content in the center column
        #st.markdown("<h2 style='text-align: center; font-family: Georgia, serif;'>ERIS CTD</h2>", unsafe_allow_html=True)
        st.plotly_chart(fig, use_container_width=True)

        # --- Download Button ---
        csv_data = filtered_data.to_csv(index=False)
        st.download_button("Download CTD Data", csv_data, "ctd_data.csv")

        # --- Data Table ---
        st.dataframe(filtered_data, use_container_width=True)

