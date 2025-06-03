import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1.base_query import FieldFilter

import json
import os
from datetime import date, time, datetime, timedelta

import pandas as pd
import plotly.graph_objs as go
import folium

import streamlit as st
from streamlit_folium import st_folium


# --- Streamlit Config ---
st.set_page_config(layout="wide")

# --- Title ---
st.markdown("<h1 style='text-align: center; font-family:Georgia, serif;'>UW ERIS CTD & WEATHER STATION DATA</h1>", unsafe_allow_html=True)

# --- Firebase Init ---
if not firebase_admin._apps:
    cert = json.loads(st.secrets["Certificate"]["data"])
    cred = credentials.Certificate(cert)
    firebase_admin.initialize_app(cred)

db = firestore.client()

#--- Image Helper ---
def get_base64_image(image_path):
    import base64
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return None

# --- Function to Fetch CTD Data ---
@st.cache_data(max_entries=10, persist=True)
def fetch_ctd_data(start_date: date, end_date: date):
    if not isinstance(start_date, date) or not isinstance(end_date, date):
        return None

    # Convert dates to milliseconds (to match Firestore timestamp format)
    start_ts = int(datetime.combine(start_date, time.min).timestamp() * 1000)
    end_ts = int(datetime.combine(end_date + timedelta(days=1), time.min).timestamp() * 1000)

    # Fetch all documents (Firestore doesn't support querying nested fields directly)
    docs = db.collection("CTD_Data")#.stream()
    query = docs.order_by("date")
    results = query.get()
    

    data = []
    for doc in results:
        d = doc.to_dict()
        try:
            ts = d.get("date", {}).get("$date")  # Firestore stores timestamp in milliseconds
            if ts is None:# or not (start_ts <= ts < end_ts):
                continue

            record = {
                "datetime": datetime.fromtimestamp(ts / 1000),  # convert ms to datetime
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

# --- UI: Date Range Selection ---
st.sidebar.header("Select Date Range")

# Default to your target range (from provided ms timestamps)
default_start = datetime.fromtimestamp(1745545207000/ 1000).date()  # July 25, 2025
default_end = datetime.fromtimestamp(1746781807000/1000).date()
start = st.sidebar.date_input("Start Date", default_start)
end = st.sidebar.date_input("End Date", default_end)
# --- Fetch and Display Data ---
data = fetch_ctd_data(start, end)

if data is None or data.empty:
    st.warning("No CTD data found for the selected date range.")
else:
    # # --- Line Chart ---
    # st.subheader("Temperature Over Time")
    # fig = go.Figure()
    # fig.add_trace(go.Scatter(
    #     x=data["datetime"], y=data["temperature"],
    #     mode='lines+markers',
    #     name='Temperature (°C)'
    # ))
    # fig.update_layout(
    #     xaxis_title='Date',
    #     yaxis_title='Temperature (°C)',
    #     template='plotly_white'
    # )
    # st.plotly_chart(fig, use_container_width=True)

    st.subheader("ERIS CTD Measurements")
    fig = go.Figure()

    
    #temp
    fig.add_trace(go.Scatter(
        x =data["datetime"],
        y=data["temperature"],
        mode='lines+markers',
        name ='Temperature (C)',
        yaxis = 'y1'
    ))

    #Salinity
    fig.add_trace(go.Scatter(
        x=data["datetime"],
        y=data["salintiy"],
        mode='lines+markers',
        name='Salinity (PSU)',
        yaxis='y2'
    ))

    #Dual y-axis
    fig.update_layout(
        xaxis_title='Date',
        yaxis=dict(
            title="Temerature (C)",
            titlefont=dict(color='red'),
            tickfont=dict(color='red')
        ),
        yaxis2=dict(
            title="Salinity (PSU)",
            titlefont=dict(color="blue"),
            tickfont=dict(color='green'),
            overlaying='y',
            side='right'
        ),
        legend=dict(x=0, y=1),
        template = 'plotly_white'
    )

    st.plotly_chart(fig, use_container_width=True)

    # --- Map ---
    st.subheader("Instrument Locations")
    m = folium.Map(location=[data["lat"].mean(), data["lon"].mean()], zoom_start=10)
    for _, row in data.iterrows():
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=5,
            popup=f"{row['instrument']}<br>{row['datetime'].strftime('%Y-%m-%d %H:%M:%S')}",
            color='blue',
            fill=True
        ).add_to(m)
    st_folium(m, width=700, height=500)

    # --- Raw Data Table ---
    st.subheader("Raw Data")
    st.dataframe(data)
