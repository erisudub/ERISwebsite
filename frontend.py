import os
import json
from datetime import date, time, datetime, timedelta

import pandas as pd
import plotly.graph_objs as go
import folium

import streamlit as st
from streamlit_folium import st_folium

import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1.base_query import FieldFilter

from base64 import b64encode

def get_base64_image(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as f:
            return b64encode(f.read()).decode()
    return None

st.set_page_config(layout="wide")
st.markdown("<h1 style='text-align: center; font-family:Georgia, serif;'>UW ERIS CTD & WEATHER STATION DATA</h1>", unsafe_allow_html=True)

if not firebase_admin._apps:
    cert = json.loads(st.secrets.Certificate.data)
    cred = credentials.Certificate(cert)
    firebase_admin.initialize_app(cred)

db = firestore.client()

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
        filter=FieldFilter("date.$date", "<", end_dt)
    ).stream()

    return [x.to_dict() for x in docs]

logo_path = "images/OceanTech Logo-PURPLE.png"
base64_logo = get_base64_image(logo_path)

logo_html = f"<img src='data:image/png;base64,{base64_logo}' style='width:150px; height:auto;'>" if base64_logo else "⚠️ Logo Not Found"

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

# Placeholder paths to CSVs
ctd_csv_file_path = "data/ctd.csv"
weather_csv_file_path = "data/weather.csv"

ctd_data = pd.read_csv(ctd_csv_file_path)
weather_data = pd.read_csv(weather_csv_file_path, skiprows=3, names=[
    'Date', 'Time', 'Out', 'Temp', 'Temp.1', 'Hum', 'Pt.', 'Speed', 'Dir', 'Run', 'Speed.1', 'Dir.1', 'Chill', 'Index',
    'Index.1', 'Bar', 'Rain', 'Rate', 'D-D', 'D-D.1', 'Temp.2', 'Hum.1', 'Dew', 'Heat', 'EMC', 'Density', 'Samp', 'Tx', 'Recept', 'Int.'
])

weather_data['DateTime'] = pd.to_datetime(weather_data['Date'] + ' ' + weather_data['Time'] + "m", format="%m/%d/%Y %I:%M%p", errors='coerce')
weather_data = weather_data.dropna(subset=['DateTime'])

ctd_data['time'] = pd.to_datetime(ctd_data['time'], errors='coerce')
ctd_data = ctd_data.dropna(subset=['time'])

st.write("### Date Range Selection")
min_date = min(ctd_data['time'].min(), weather_data['DateTime'].min())
max_date = max(ctd_data['time'].max(), weather_data['DateTime'].max())

start_date = st.date_input("Start Date", value=min_date.date())
end_date = st.date_input("End Date", value=max_date.date())

filtered_ctd_data = ctd_data[(ctd_data['time'] >= pd.Timestamp(start_date)) & (ctd_data['time'] <= pd.Timestamp(end_date))]
filtered_weather_data = weather_data[(weather_data['DateTime'] >= pd.Timestamp(start_date)) & (weather_data['DateTime'] <= pd.Timestamp(end_date))]

fig1 = go.Figure()
fig2 = go.Figure()

fig1_traces = [
    ('temperature', 'Temperature', 'blue'),
    ('conductivity', 'Conductivity', 'purple'),
    ('par', 'PAR', 'green'),
    ('turbidity', 'Turbidity', 'red'),
    ('salinity', 'Salinity', 'orange'),
    ('pressure', 'Pressure', 'black'),
    ('oxygen', 'Oxygen', 'gold')
]
for col, label, color in fig1_traces:
    if col in filtered_ctd_data:
        fig1.add_trace(go.Scatter(x=filtered_ctd_data['time'], y=filtered_ctd_data[col], mode='lines', name=label, line=dict(color=color)))

fig2_traces = [
    ('Temp', 'Temperature', 'red'),
    ('Speed', 'Wind Speed', 'purple'),
    ('Hum', 'Humidity', 'green'),
    ('Dew', 'Dew', 'blue'),
    ('Density', 'Density', 'black')
]
for col, label, color in fig2_traces:
    if col in filtered_weather_data:
        fig2.add_trace(go.Scatter(x=filtered_weather_data['DateTime'], y=filtered_weather_data[col], mode='lines', name=label, line=dict(color=color)))

layout_params = dict(
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
            x=0.5, y=1.15, xanchor='center', yanchor='bottom')
    ),
    yaxis=dict(showgrid=True, gridcolor='lightgrey'),
    plot_bgcolor="white",
    paper_bgcolor="lightblue",
    font=dict(family="Georgia, serif", size=12, color="black"),
    legend=dict(x=1.05, y=0.5, xanchor='left', yanchor='middle', traceorder="normal", bgcolor='rgba(255, 255, 255, 0.5)'),
    margin=dict(l=80, r=80, t=50, b=80),
    autosize=False
)

fig1.update_layout(**layout_params)
fig2.update_layout(**layout_params)

col1, col2 = st.columns(2)

with col1:
    st.markdown("<h2 style='text-align: center; font-family: Georgia, serif;'>UW CTD MEASUREMENTS</h2>", unsafe_allow_html=True)
    st.plotly_chart(fig1, use_container_width=True)
    st.download_button("Download CTD Data", filtered_ctd_data.to_csv(index=False), "ctd_data.csv")
    st.dataframe(filtered_ctd_data)

with col2:
    st.markdown("<h2 style='text-align: center; font-family: Georgia, serif;'>UW WEATHER STATION MEASUREMENTS</h2>", unsafe_allow_html=True)
    st.plotly_chart(fig2, use_container_width=True)
    st.download_button("Download Weather Data", filtered_weather_data.to_csv(index=False), "weather_data.csv")
    st.dataframe(filtered_weather_data)

st.write("### Instrument Locations")
map_center = [47.649414, -122.312534]
m = folium.Map(location=map_center, zoom_start=15, width='100%', height='600px')

folium.CircleMarker(
    location=[47.649414, -122.312534],
    radius=4,
    color='red',
    fill=True,
    fill_color='red',
    fill_opacity=0.7,
    tooltip="CTD: 47.649414, -122.312534"
).add_to(m)

folium.CircleMarker(
    location=[47.649572, -122.312467],
    radius=4,
    color='blue',
    fill=True,
    fill_color='blue',
    fill_opacity=0.7,
    tooltip="WEATHER STATION: 47.649572, -122.312467"
).add_to(m)

st_folium(m, width=1500, height=500)
