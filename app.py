import json
from datetime import date, time, datetime, timedelta

import pandas as pd
import plotly.graph_objs as go
import folium

import streamlit as st
from streamlit_folium import st_folium

import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1.base_query import FieldFilter, Or, And


# testing github comment for tutorial 

st.set_page_config(layout="wide")

st.markdown("<h1 style='text-align: center; font-family:Georgia, serif;'>UW ERIS CTD & WEATHER STATION DATA</h1>", unsafe_allow_html=True)

if not firebase_admin._apps:
    cert = json.loads(st.secrets.CTD_data.data)
    cred = credentials.CTD_data(cert)
    app = firebase_admin.initialize_app(cred)

db = firestore.client()

@st.cache_data(max_entries=10, persist=True) # 1 week
def fetch_ctd_data(start_date: date, end_date: date):

    if not isinstance(start_date, date): return None
    if not isinstance(end_date, date): return None

    start_dt = datetime.combine(start_date, time(0, 0, 0)).timestamp()
    end_dt = datetime.combine(end_date + timedelta(days=1), time(0, 0, 0)).timestamp()

    ctd_ref = db.collection("CTD_data")
    docs = ctd_ref.where(
        filter=FieldFilter("date.$date", ">=", start_dt)
    ).where(
        filter=FieldFilter("date.$date", "<", end_dt),
    ).stream()

    out = []
    for x in docs:
        out.append(x.to_dict())

    return out


def live_weather_data(start_date: date | None  = None):

    if start_date is None: start_date = date.today()
    if not isinstance(start_date, date): return None
    start_dt = datetime.combine(start_date, time(0, 0, 0))

    weather_ref = db.collection("weather_data")
    docs = weather_ref.where(
        filter=FieldFilter("datetime", ">=", start_dt)
    )

    out = []
    for x in docs:
        out.append(x.to_dict())

    return out


# Load CSV data for each graph
ctd_csv_file_path = 'data/ctddata.csv'  # Replace with the actual path of the CTD CSV
#weather_csv_file_path = 'data/new_weather_data.csv'  # Use the uploaded weather CSV file

#ctd_data = pd.read_csv(ctd_csv_file_path)
#weather_data = pd.read_csv(weather_csv_file_path, skiprows=3, names=[
#    'Date', 'Time', 'Out', 'Temp', 'Temp.1', 'Hum', 'Pt.',
#    'Speed', 'Dir', 'Run', 'Speed.1', 'Dir.1', 'Chill', 'Index',
#    'Index.1', 'Bar', 'Rain', 'Rate', 'D-D', 'D-D.1', 'Temp.2', 'Hum.1',
#    'Dew', 'Heat', 'EMC', 'Density', 'Samp', 'Tx', 'Recept', 'Int.'
#])

weather_data_raw = fetch_ctd_data(date(2024, 1, 1), date.today())
weather_data = pd.DataFrame.from_records(weather_data_raw)

#st.write("Weather Data Columns:", weather_data.columns.tolist())

# Assign column names to weather_data and confirm them
#weather_data['DateTime'] = pd.to_datetime(
#    weather_data['Date'] + ' ' + weather_data['Time'] + "m", format="%m/%d/%Y %I:%M%p", errors='coerce'
#)
weather_data = weather_data.dropna(subset=['datetime'])  # Drop rows with NaT in DateTime
weather_data['datetime'] = weather_data['datetime'].dt.tz_localize(None)

# Convert ctd_data 'time' column to datetime
ctd_data['time'] = pd.to_datetime(ctd_data['time'], errors='coerce')
ctd_data = ctd_data.dropna(subset=['time'])  # Drop rows with NaT in time

# Step 5: Date range selection for filtering data
st.write("### Date Range Selection")
min_date = min(ctd_data['time'].min(), weather_data['datetime'].min())
max_date = max(ctd_data['time'].max(), weather_data['datetime'].max())

start_date = st.date_input("Start Date", value=min_date.date())
end_date = st.date_input("End Date", value=max_date.date())

# Filter the data based on the selected date range for both datasets
filtered_ctd_data = ctd_data[(ctd_data['time'] >= pd.Timestamp(start_date)) & (ctd_data['time'] <= pd.Timestamp(end_date))]
filtered_weather_data = weather_data[(weather_data['datetime'] >= pd.Timestamp(start_date)) & (weather_data['datetime'] <= pd.Timestamp(end_date))]

# Create filtered figures for both graphs
fig1 = go.Figure()
fig2 = go.Figure()

# Add each y-column as a separate trace for the first graph using filtered data
fig1.add_trace(go.Scatter(x=filtered_ctd_data['time'], y=filtered_ctd_data['temperature'], mode='lines', name='Temperature', line=dict(color='blue')))
fig1.add_trace(go.Scatter(x=filtered_ctd_data['time'], y=filtered_ctd_data['conductivity'], mode='lines', name='Conductivity', line=dict(color='purple')))
fig1.add_trace(go.Scatter(x=filtered_ctd_data['time'], y=filtered_ctd_data['par'], mode='lines', name='PAR', line=dict(color='green')))
fig1.add_trace(go.Scatter(x=filtered_ctd_data['time'], y=filtered_ctd_data['turbidity'], mode='lines', name='Turbidity', line=dict(color='red')))
fig1.add_trace(go.Scatter(x=filtered_ctd_data['time'], y=filtered_ctd_data['salinity'], mode='lines', name='Salinity', line=dict(color='orange')))
fig1.add_trace(go.Scatter(x=filtered_ctd_data['time'], y=filtered_ctd_data['pressure'], mode='lines', name='Pressure', line=dict(color='black')))
fig1.add_trace(go.Scatter(x=filtered_ctd_data['time'], y=filtered_ctd_data['oxygen'], mode='lines', name='Oxygen', line=dict(color='gold')))

# Add each y-column as a separate trace for the second graph using filtered weather data
fig2.add_trace(go.Scatter(x=filtered_weather_data['datetime'], y=filtered_weather_data['temp_out'], mode='lines', name='Temperature', line=dict(color='blue')))
fig2.add_trace(go.Scatter(x=filtered_weather_data['datetime'], y=filtered_weather_data['wind_speed'], mode='lines', name='Wind Speed', line=dict(color='purple')))
fig2.add_trace(go.Scatter(x=filtered_weather_data['datetime'], y=filtered_weather_data['dew_pt'], mode='lines', name='Dew', line=dict(color='green')))
fig2.add_trace(go.Scatter(x=filtered_weather_data['datetime'], y=filtered_weather_data['humidity'], mode='lines', name='Humidity', line=dict(color='orange')))

# Function to update the layout for figure 1
def update_layout_fig1(fig1, title):
    fig1.update_layout(
        title={
            'text': title,
            'x': 0.5,
            'y': 0.95,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': {'family': "Georgia, serif", 'size': 20, 'color': "black", 'weight': 'bold'}
        },
        xaxis_title="Time",
        yaxis_title="Values",
        width=700,
        height=400,
        xaxis=dict(rangeslider=dict(visible=True), type="date", rangeselector=dict(
            buttons=[dict(count=1, label="1d", step="day", stepmode="backward"),
                        dict(count=7, label="1w", step="day", stepmode="backward"),
                        dict(count=1, label="1m", step="month", stepmode="backward"),
                        dict(count=6, label="6m", step="month", stepmode="backward"),
                        dict(step="all")],
            x=0.5, y=1.15, xanchor = 'center')),
        yaxis=dict(showgrid=True, gridcolor='lightgrey'),
        plot_bgcolor="white",
        paper_bgcolor="lightblue",
        font=dict(family="Georgia, serif", size=12, color="black"),
        legend=dict(
            x=1.05, 
            y=0.5, 
            xanchor = 'left',
            yanchor = 'middle',
            traceorder="normal", 
            bgcolor='rgba(255, 255, 255, 0.5)'),
        margin=dict(l=50, r=120, t=120, b=50),
        autosize=False
    )

# Function to update the layout for figure 2
def update_layout_fig2(fig2, title):
    fig2.update_layout(
        title={
            'text': title,
            'x': 0.5,
            'y': 0.95,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': {'family': "Georgia, serif", 'size': 20, 'color': "black", 'weight': 'bold'}
        },
        xaxis_title="Time",
        yaxis_title="Values",
        width=700,
        height=400,
        xaxis=dict(rangeslider=dict(visible=True), type="date", rangeselector=dict(
            buttons=[dict(count=1, label="1d", step="day", stepmode="backward"),
                        dict(count=7, label="1w", step="day", stepmode="backward"),
                        dict(count=1, label="1m", step="month", stepmode="backward"),
                        dict(count=6, label="6m", step="month", stepmode="backward"),
                        dict(step="all")],
            x=0.5, y=1.15, xanchor = 'center')),
        yaxis=dict(showgrid=True, gridcolor='lightgrey'),
        plot_bgcolor="white",
        paper_bgcolor="lightblue",
        font=dict(family="Georgia, serif", size=12, color="black"),
        legend=dict(
            x=1.05, 
            y=0.5, 
            xanchor = 'left',
            yanchor = 'middle',
            traceorder="normal", 
            bgcolor='rgba(255, 255, 255, 0.5)'),
        margin=dict(l=50, r=120, t=120, b=50),
        autosize=False
    )

# Now apply the respective layout update functions to each figure
update_layout_fig1(fig1, "UW ERIS CTD MEASUREMENTS")
update_layout_fig2(fig2, "UW WEATHER STATION MEASUREMENTS")

# Create columns for displaying the two graphs side by side
col1, col2 = st.columns(2)

# Show the filtered plot in the first column
with col1:
    st.plotly_chart(fig1, use_container_width=True)
    csv1 = filtered_ctd_data.to_csv(index=False)
    st.download_button("Download CTD Data", csv1, "ctd_data.csv")
    st.dataframe(filtered_ctd_data)

# Show the filtered plot in the second column
with col2:
    st.plotly_chart(fig2, use_container_width=True)
    csv2 = filtered_weather_data.to_csv(index=False)
    st.download_button("Download Weather Data", csv2, "weather_data.csv")
    st.dataframe(filtered_weather_data)

#  import streamlit as st
# import pandas as pd
# import plotly.graph_objs as go
# import folium
# import firebase_admin
# import json
# import http.client
# import time
# import os

# from firebase_admin import credentials, firestore
# from streamlit_folium import st_folium
# from datetime import datetime, timedelta, timezone
# from pathlib import Path

# # Initializing the Firestore Database
# cert = json.loads(st.secrets.Certificate.data)
# if cert is None:
#     raise ValueError("ADMIN_KEY is not set. Please configure GitHub Secrets.")
# cred = credentials.Certificate(cert)
# app = firebase_admin.initialize_app(cred)
# db = firestore.client()


# current_time = round(time.time()*1000)

# # conntection = http.client.HTTPConnection('')

# # headers = {'Content-type': 'application/json'}

# values = {
#     "air_temp": 7.6,
#     "humidity": 80,
#     "wind_speed": 4.8,
#     "wind_direction": "ESE",
#     "date": {"$date": current_time}
# }

# _, doc_ref = db.collection("CTD_Data").add(values)
# print(f"Added document with ID: {doc_ref.id}")

# # json_values = json.dumps(values)

# # connection.request('POST', '/', json_values, headers)

# # response = connection.getresponse()

# # print(response.read().decode())

# # CSV -> JSON
# data_path = "output.json"  # Define output JSON file path


# weather_ref = db.collection("CTD_Data")
# docs = weather_ref.stream()
# for x in docs:
#     print(x.to_dict())

'''
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
'''