import streamlit as st
import pandas as pd
import plotly.graph_objs as go
import folium
import firebase_admin
import json

from firebase_admin import credentials
from streamlit_folium import st_folium
from google.cloud import firestore
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Initializing the Firestore Database

cred = credentials.Certificate("eris-db-firebase-adminsdk-fbsvc-0e9054933b.json")
firebase_admin.initialize_app(cred)

# Authenticate to Firestore with the JSON account key.
db = firestore.Client.from_service_account_json("eris-db-firebase-adminsdk-fbsvc-0e9054933b.json")

# CSV -> JSON
data_path = "output.json"  # Define output JSON file path

# Read CSV
# df = pd.read_csv("ctddata.csv")  # Ensure you provide the correct CSV file

# # Convert to JSON and save
# df.to_json(data_path, orient="records")  

# Read the JSON file back into a Python object
#with open(data_path, "r") as infile:
   # eris = json.load(infile)

new_collection = []
for record in data_path: ## change eris to be the name of the converted json file
    
    try:
        date = datetime.fromisoformat(record["date"])
    except:
        continue

    if date - datetime.fromisoformat('2024-01-01T00:00:00Z') < timedelta(0):
        continue

    # my json file needs some preprocessing
    # your mileage may vary
    new_rec = {}
    new_rec['temperature'] = float(record.get('temperature', np.nan))
    new_rec['conductivity'] = float(record.get('conductivity', np.nan))
    new_rec['pressure'] = float(record.get('pressure', np.nan))
    new_rec['oxygen'] = float(record.get('oxygen', np.nan))
    new_rec['par'] = float(record.get('par', np.nan))
    new_rec['turbidity'] = float(record.get('turbidity', np.nan))
    new_rec['salinity'] = float(record.get('salinity', np.nan))
    new_rec['instrument'] = record.get('instrument', "")
    ##new_rec['depth1'] = record.get('depth1', np.nan)
    ##new_rec['lat'] = record.get('lat', np.nan)
    ##new_rec['lon'] = record.get('lon', np.nan)
    ##new_rec['date'] = date

    new_collection.append(new_rec)

new_collection.sort(key=lambda x: x["date"])

len(new_collection)

# select the collection to write to
CTD_ref = db.collection("CTD_Data")

# write records one by one
for rec in new_collection:
    CTD_ref.document().set(rec)

# Set wide layout for the Streamlit page
st.set_page_config(layout="wide")

# Title for the entire page
st.markdown("<h1 style='text-align: center; font-family:Georgia, serif;'>UW ERIS CTD & WEATHER STATION DATA</h1>", unsafe_allow_html=True)

# Sidebar for navigation
st.sidebar.title("Navigation")
page = st.sidebar.selectbox("Go to", ["Main Page", "Plot Your Own Data", "Instrument Descriptions", "Meet the Team", "Gallery"])

# Load CSV data for each graph
ctd_csv_file_path = 'ctddata.csv'  # Replace with actual path
weather_csv_file_path = 'weatherdata.csv'  # Replace with actual path

# Main Page
if page == "Main Page":
    st.write("## Welcome to the Main Page")
    
    ctd_data = pd.read_csv(ctd_csv_file_path)
    weather_data = pd.read_csv(weather_csv_file_path, skiprows=1)
    
    weather_data.columns = [
        'Date', 'Time', 'Temp_Out', 'Hi_Temp', 'Low_Temp', 'Out_Hum', 'Dew_Pt',
        'Wind_Speed', 'Wind_Dir', 'Wind_Run', 'col10', 'col11', 'col12', 'col13',
        'col14', 'col15', 'col16', 'col17', 'col18', 'col19', 'col20', 'col21',
        'col22', 'col23', 'col24', 'col25', 'col26', 'col27', 'col28', 'col29',
        'col30', 'col31', 'col32', 'Wind_Samp', 'Wind_Tx', 'ISS_Recept', 'Arc_Int', 'col38'
    ]
    
    weather_data['DateTime'] = pd.to_datetime(weather_data['Date'] + ' ' + weather_data['Time'],
                                               format="%m/%d/%Y %I:%M %p", errors='coerce')
    weather_data = weather_data.dropna(subset=['DateTime'])
    ctd_data['time'] = pd.to_datetime(ctd_data['time'])
    
    st.write("### Date Range Selection")
    min_date = min(ctd_data['time'].min().date(), weather_data['DateTime'].min().date())
    max_date = max(ctd_data['time'].max().date(), weather_data['DateTime'].max().date())
    
    start_date = st.date_input("Start Date", value=min_date)
    end_date = st.date_input("End Date", value=max_date)
    
    filtered_ctd_data = ctd_data[(ctd_data['time'] >= pd.Timestamp(start_date)) & (ctd_data['time'] <= pd.Timestamp(end_date))]
    filtered_weather_data = weather_data[(weather_data['DateTime'] >= pd.Timestamp(start_date)) & (weather_data['DateTime'] <= pd.Timestamp(end_date))]
    
    fig1 = go.Figure()
    fig2 = go.Figure()
    
    fig1.add_trace(go.Scatter(x=filtered_ctd_data['time'], y=filtered_ctd_data['temperature'], mode='lines', name='Temperature', line=dict(color='blue')))
    fig1.add_trace(go.Scatter(x=filtered_ctd_data['time'], y=filtered_ctd_data['conductivity'], mode='lines', name='Conductivity', line=dict(color='purple')))
    
    fig2.add_trace(go.Scatter(x=filtered_weather_data['DateTime'], y=filtered_weather_data['Temp_Out'], mode='lines', name='Temperature', line=dict(color='blue')))
    fig2.add_trace(go.Scatter(x=filtered_weather_data['DateTime'], y=filtered_weather_data['Dew_Pt'], mode='lines', name='Dew Point', line=dict(color='purple')))
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.plotly_chart(fig1, use_container_width=True)
        csv1 = filtered_ctd_data.to_csv(index=False)
        st.download_button("Download CTD Data", csv1, "ctd_data.csv")
    
    with col2:
        st.plotly_chart(fig2, use_container_width=True)
        csv2 = filtered_weather_data.to_csv(index=False)
        st.download_button("Download Weather Data", csv2, "weather_data.csv")
    
    st.write("### Instrument Locations")
    map_center = [47.649414, -122.312534]
    m = folium.Map(location=map_center, zoom_start=15)
    folium.CircleMarker(location=[47.649414, -122.312534], radius=4, color='red', fill=True, fill_opacity=0.7, tooltip="CTD").add_to(m)
    folium.CircleMarker(location=[47.649572, -122.312467], radius=4, color='blue', fill=True, fill_opacity=0.7, tooltip="Weather Station").add_to(m)
    st_folium(m, width=1500, height=500)

# Plot Your Own Data Page
elif page == "Plot Your Own Data":
    st.write("## Upload Your CSV")
    user_file = st.file_uploader("Upload a CSV file", type=["csv"])
    if user_file:
        try:
            user_data = pd.read_csv(user_file)
            st.dataframe(user_data)
            if 'time' in user_data.columns:
                user_data['time'] = pd.to_datetime(user_data['time'])
                fig_user = go.Figure()
                for col in user_data.columns:
                    if col != 'time':
                        fig_user.add_trace(go.Scatter(x=user_data['time'], y=user_data[col], mode='lines', name=col))
                st.plotly_chart(fig_user)
        except Exception as e:
            st.error(f"Error processing file: {e}")

# Instrument Descriptions Page
elif page == "Instrument Descriptions":
    st.write("## Description of the Instruments")
    st.write("### Seabird CTD")
    st.write("Our Seabird SBE 16plus Conductivity-Temperature-Depth (CTD) sensor is a compact, durable oceanographic instrument.")
    st.write("### Weather Station")
    
# Meet the Team Page
elif page == "Meet the Team":
    st.write("## Team Members")
    
# Gallery Page
elif page == "Gallery":
    photos = ["images/group.jpg", "images/grads.jpg", "images/tub.jpg"]
    captions = ["Deployment Day Spring 2024", "CTD Calibrations", "2024 Graduating Marine Technicians"]
    columns = 3
    for i in range(0, len(photos), columns):
        cols = st.columns(columns)
        for j, col in enumerate(cols):
            if i + j < len(photos):
                col.image(photos[i + j], use_column_width=True, caption=captions[i + j])
