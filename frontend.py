import json
import os
from datetime import date, time, datetime, timedelta

import pandas as pd
import plotly.graph_objs as go
import folium

import streamlit as st
from streamlit_folium import st_folium

import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1.base_query import FieldFilter

# --- Streamlit Config ---
st.set_page_config(layout="wide")

# --- Title ---
st.markdown("<h1 style='text-align: center; font-family:Georgia, serif;'>UW ERIS CTD & WEATHER STATION DATA</h1>", unsafe_allow_html=True)

# --- Firebase Init ---
if not firebase_admin._apps:
    cert = json.loads(st.secrets.Certificate.data)
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

# --- Firebase Query Caching ---
@st.cache_data(max_entries=10, persist=True)
def fetch_ctd_data(start_date: date, end_date: date):
    if not isinstance(start_date, date) or not isinstance(end_date, date):
        return None

    start_dt = datetime.combine(start_date, time(0, 0, 0)).timestamp()
    end_dt = datetime.combine(end_date + timedelta(days=1), time(0, 0, 0)).timestamp()

    ctd_ref = db.collection("CTD_data")
    docs = ctd_ref.where(
        filter=FieldFilter("date.$date", ">=", start_dt)
    ).where(
        filter=FieldFilter("date.$date", "<", end_dt),
    ).stream()

    return [x.to_dict() for x in docs]

# --- Load CSV Paths ---
ctd_csv_file_path = "path_to_ctd_file.csv"  # Change to your path
weather_csv_file_path = "path_to_weather_file.csv"  # Change to your path

# --- Logo Header ---
logo_path = "images/OceanTech Logo-PURPLE.png"
base64_logo = get_base64_image(logo_path)

if base64_logo:
    logo_html = f"<img src='data:image/png;base64,{base64_logo}' style='width:150px; height:auto;'>"
else:
    logo_html = "⚠️ Logo Not Found"

st.markdown(
    f"""
    <div style="display: flex; align-items: center; justify-content: center; gap: 20px;">
        {logo_html}
        <h1 style='text-align: center; font-family:Georgia, serif; margin:0;'>UW ERIS CTD & Weather Station Data</h1>
        {logo_html}
    </div>
    """,
    unsafe_allow_html=True
)

# --- Load and Preprocess Data ---
ctd_data = pd.read_csv('data/ctddata.csv')
weather_data = pd.read_csv('new_weather_data.csv', skiprows=3, names=[
    'Date', 'Time', 'Out', 'Temp', 'Temp.1', 'Hum', 'Pt.',
    'Speed', 'Dir', 'Run', 'Speed.1', 'Dir.1', 'Chill', 'Index',
    'Index.1', 'Bar', 'Rain', 'Rate', 'D-D', 'D-D.1', 'Temp.2', 'Hum.1',
    'Dew', 'Heat', 'EMC', 'Density', 'Samp', 'Tx', 'Recept', 'Int.'
])
weather_data['DateTime'] = pd.to_datetime(
    weather_data['Date'] + ' ' + weather_data['Time'] + "m",
    format="%m/%d/%Y %I:%M%p", errors='coerce'
)
weather_data = weather_data.dropna(subset=['DateTime'])

ctd_data['time'] = pd.to_datetime(ctd_data['time'], errors='coerce')
ctd_data = ctd_data.dropna(subset=['time'])

# --- Date Filtering ---
st.write("### Date Range Selection")
min_date = min(ctd_data['time'].min(), weather_data['DateTime'].min())
max_date = max(ctd_data['time'].max(), weather_data['DateTime'].max())

start_date = st.date_input("Start Date", value=min_date.date())
end_date = st.date_input("End Date", value=max_date.date())

filtered_ctd_data = ctd_data[(ctd_data['time'] >= pd.Timestamp(start_date)) & (ctd_data['time'] <= pd.Timestamp(end_date))]
filtered_weather_data = weather_data[(weather_data['DateTime'] >= pd.Timestamp(start_date)) & (weather_data['DateTime'] <= pd.Timestamp(end_date))]

# --- Plot CTD Data ---
fig1 = go.Figure()
fig1.add_trace(go.Scatter(x=filtered_ctd_data['time'], y=filtered_ctd_data['temperature'], mode='lines', name='Temperature', line=dict(color='blue')))
fig1.add_trace(go.Scatter(x=filtered_ctd_data['time'], y=filtered_ctd_data['conductivity'], mode='lines', name='Conductivity', line=dict(color='purple')))
fig1.add_trace(go.Scatter(x=filtered_ctd_data['time'], y=filtered_ctd_data['par'], mode='lines', name='PAR', line=dict(color='green')))
fig1.add_trace(go.Scatter(x=filtered_ctd_data['time'], y=filtered_ctd_data['turbidity'], mode='lines', name='Turbidity', line=dict(color='red')))
fig1.add_trace(go.Scatter(x=filtered_ctd_data['time'], y=filtered_ctd_data['salinity'], mode='lines', name='Salinity', line=dict(color='orange')))
fig1.add_trace(go.Scatter(x=filtered_ctd_data['time'], y=filtered_ctd_data['pressure'], mode='lines', name='Pressure', line=dict(color='black')))
fig1.add_trace(go.Scatter(x=filtered_ctd_data['time'], y=filtered_ctd_data['oxygen'], mode='lines', name='Oxygen', line=dict(color='gold')))

fig1.update_layout(title="CTD Measurements", xaxis_title="Time", yaxis_title="Values")

# --- Plot Weather Data ---
fig2 = go.Figure()
fig2.add_trace(go.Scatter(x=filtered_weather_data['DateTime'], y=filtered_weather_data['Temp'], mode='lines', name='Temperature', line=dict(color='red')))
fig2.add_trace(go.Scatter(x=filtered_weather_data['DateTime'], y=filtered_weather_data['Speed'], mode='lines', name='Wind Speed', line=dict(color='purple')))
fig2.add_trace(go.Scatter(x=filtered_weather_data['DateTime'], y=filtered_weather_data['Hum'], mode='lines', name='Humidity', line=dict(color='green')))
fig2.add_trace(go.Scatter(x=filtered_weather_data['DateTime'], y=filtered_weather_data['Dew'], mode='lines', name='Dew', line=dict(color='blue')))
fig2.add_trace(go.Scatter(x=filtered_weather_data['DateTime'], y=filtered_weather_data['Density'], mode='lines', name='Density', line=dict(color='black')))

fig2.update_layout(title="Weather Station Measurements", xaxis_title="Time", yaxis_title="Values")

# --- Layout for Plots ---
col1, col2 = st.columns(2)

with col1:
    st.markdown("<h2 style='text-align: center;'>CTD Data</h2>", unsafe_allow_html=True)
    st.plotly_chart(fig1, use_container_width=True)
    st.download_button("Download CTD CSV", filtered_ctd_data.to_csv(index=False), "ctd_data.csv")
    st.dataframe(filtered_ctd_data)

with col2:
    st.markdown("<h2 style='text-align: center;'>Weather Data</h2>", unsafe_allow_html=True)
    st.plotly_chart(fig2, use_container_width=True)
    st.download_button("Download Weather CSV", filtered_weather_data.to_csv(index=False), "weather_data.csv")
    st.dataframe(filtered_weather_data)

# --- Folium Map ---
st.write("### Instrument Locations")
m = folium.Map(location=[47.649414, -122.312534], zoom_start=15)
folium.CircleMarker(location=[47.649414, -122.312534], radius=4, color='red', fill=True, tooltip="CTD").add_to(m)
folium.CircleMarker(location=[47.649572, -122.312467], radius=4, color='blue', fill=True, tooltip="Weather Station").add_to(m)
st_folium(m, width=1500, height=500)
