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

st.set_page_config(layout="wide")

st.markdown("<h1 style='text-align: center; font-family:Georgia, serif;'>UW ERIS CTD & WEATHER STATION DATA</h1>", unsafe_allow_html=True)

if not firebase_admin._apps:
    cert = json.loads(st.secrets.Certificate.data)
    cred = credentials.Certificate(cert)
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

st.set_page_config(layout="wide")

logo_path = "images/OceanTech Logo-PURPLE.png"
base64_logo = get_base64_image(logo_path)

if base64_logo:
        # Set logo size to match the specified CSS size
        logo_html = f"<img src='data:image/png;base64,{base64_logo}' style='width:150px; height:auto;'>"
    else:
        logo_html = "⚠️ Logo Not Found"

    # Title with Logos on Both Sides
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
    ctd_data = pd.read_csv(ctd_csv_file_path)
    #weather_data = pd.read_csv(weather_csv_file_path, skiprows=1)
    
    weather_data = pd.read_csv(weather_csv_file_path, skiprows=3, names=[
        'Date', 'Time', 'Out', 'Temp', 'Temp.1', 'Hum', 'Pt.',
        'Speed', 'Dir', 'Run', 'Speed.1', 'Dir.1', 'Chill', 'Index',
        'Index.1', 'Bar', 'Rain', 'Rate', 'D-D', 'D-D.1', 'Temp.2', 'Hum.1',
        'Dew', 'Heat', 'EMC', 'Density', 'Samp', 'Tx', 'Recept', 'Int.'
    ])

    # Combine Date and Time into DateTime for weather data
    weather_data['DateTime'] = pd.to_datetime(
    weather_data['Date'] + ' ' + weather_data['Time'] + "m", format="%m/%d/%Y %I:%M%p", errors='coerce'
    )
    weather_data = weather_data.dropna(subset=['DateTime'])  # Drop rows with NaT in DateTime
    
    # Convert ctd_data 'time' column to datetime
    ctd_data['time'] = pd.to_datetime(ctd_data['time'], errors='coerce')
    ctd_data = ctd_data.dropna(subset=['time'])  # Drop rows with NaT in time

    # Step 5: Date range selection for filtering data
    st.write("### Date Range Selection")
    min_date = min(ctd_data['time'].min(), weather_data['DateTime'].min())
    max_date = max(ctd_data['time'].max(), weather_data['DateTime'].max())

    start_date = st.date_input("Start Date", value=min_date.date())
    end_date = st.date_input("End Date", value=max_date.date())

    # Filter the data based on the selected date range for both datasets
    filtered_ctd_data = ctd_data[(ctd_data['time'] >= pd.Timestamp(start_date)) & (ctd_data['time'] <= pd.Timestamp(end_date))]
    filtered_weather_data = weather_data[(weather_data['DateTime'] >= pd.Timestamp(start_date)) & (weather_data['DateTime'] <= pd.Timestamp(end_date))]

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
    fig2.add_trace(go.Scatter(x=filtered_weather_data['DateTime'], y=filtered_weather_data['Temp'], mode='lines', name='Temperature', line=dict(color='red')))
    fig2.add_trace(go.Scatter(x=filtered_weather_data['DateTime'], y=filtered_weather_data['Speed'], mode='lines', name='Wind Speed', line=dict(color='purple')))
    fig2.add_trace(go.Scatter(x=filtered_weather_data['DateTime'], y=filtered_weather_data['Hum'], mode='lines', name='Humidity', line=dict(color='green')))
    fig2.add_trace(go.Scatter(x=filtered_weather_data['DateTime'], y=filtered_weather_data['Dew'], mode='lines', name='Dew', line=dict(color='blue')))
    fig2.add_trace(go.Scatter(x=filtered_weather_data['DateTime'], y=filtered_weather_data['Density'], mode='lines', name='Density', line=dict(color='black')))

    # Function to update the layout for figure 1
    def update_layout_fig1(fig1, title):
        fig1.update_layout(
            xaxis_title="Time",
            yaxis_title="Values",
            width=800,
            height=450,
            xaxis=dict(rangeslider=dict(visible=True), type="date", rangeselector=dict(
                buttons=[dict(count=1, label="1d", step="day", stepmode="backward"),
                         dict(count=7, label="1w", step="day", stepmode="backward"),
                         dict(count=1, label="1m", step="month", stepmode="backward"),
                         dict(count=6, label="6m", step="month", stepmode="backward"),
                         dict(step="all")],
                x=0.5, y=1.15, xanchor = 'center', yanchor = 'bottom')),
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
            margin=dict(l=80, r=80, t=50, b=80),
            autosize=False
        )

    # Function to update the layout for figure 2
    def update_layout_fig2(fig2, title):
        fig2.update_layout(
            xaxis_title="Time",
            yaxis_title="Values",
            width=800,
            height=450,
            xaxis=dict(rangeslider=dict(visible=True), type="date", rangeselector=dict(
                buttons=[dict(count=1, label="1d", step="day", stepmode="backward"),
                         dict(count=7, label="1w", step="day", stepmode="backward"),
                         dict(count=1, label="1m", step="month", stepmode="backward"),
                         dict(count=6, label="6m", step="month", stepmode="backward"),
                         dict(step="all")],
                x=0.5, y=1.15, xanchor = 'center', yanchor = 'bottom')),
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
            margin=dict(l=80, r=80, t=50, b=80),
            autosize=False
        )

    # Now apply the respective layout update functions to each figure
    update_layout_fig1(fig1, "UW ERIS CTD MEASUREMENTS")
    update_layout_fig2(fig2, "UW WEATHER STATION MEASUREMENTS")

    # Create columns for displaying the two graphs side by side
    col1, col2 = st.columns(2)

    # Show the filtered plot in the first column
    with col1:
        st.markdown("<h2 style='text-align: center; font-family: Georgia, serif;'>UW WEATHER STATION MEASUREMENTS</h2>", unsafe_allow_html=True)
        st.plotly_chart(fig1, use_container_width=True)
        csv1 = filtered_ctd_data.to_csv(index=False)
        st.download_button("Download CTD Data", csv1, "ctd_data.csv")
        st.dataframe(filtered_ctd_data)
    
    # Show the filtered plot in the second column
    with col2:
        st.markdown("<h2 style='text-align: center; font-family: Georgia, serif;'>UW WEATHER STATION MEASUREMENTS</h2>", unsafe_allow_html=True)
        st.plotly_chart(fig2, use_container_width=True)
        csv2 = filtered_weather_data.to_csv(index=False)
        st.download_button("Download Weather Data", csv2, "weather_data.csv")
        st.dataframe(filtered_weather_data)

    # Display the Folium map of instrument locations
    # Add a map of instrument locations
    st.write("### Instrument Locations")
    map_center = [47.649414, -122.312534]
    m = folium.Map(location=map_center, zoom_start=15, width='100%', height='600px')
    # Add a circle marker for the first location
    folium.CircleMarker(
        location=[47.649414, -122.312534],
        radius=4,
        color='red',
        fill=True,
        fill_color='red',
        fill_opacity=0.7,
        tooltip="CTD: 47.649414, -122.312534"
    ).add_to(m)

    # Add a circle marker for the second location
    folium.CircleMarker(
        location=[47.649572, -122.312467],
        radius=4,
        color='blue',
        fill=True,
        fill_color='blue',
        fill_opacity=0.7,
        tooltip="WEATHER STATION: 47.649572, -122.312467"
    ).add_to(m)

    # Display the map in full width
    st_folium(m, width=1500, height=500)

    st.set_page_config(layout="wide")

# 📌 **Instrument Descriptions Page**
elif page == "Instrument Descriptions":
    # Convert logo to Base64
    logo_path = "images/OceanTech Logo-PURPLE.png"
    base64_logo = get_base64_image(logo_path)

    if base64_logo:
        # Set logo size to match the specified CSS size
        logo_html = f"<img src='data:image/png;base64,{base64_logo}' style='width:150px; height:auto;'>"
    else:
        logo_html = "⚠️ Logo Not Found"

    st.markdown(
        f"""
        <div style="display: flex; align-items: center; justify-content: center; gap: 20px;">
            {logo_html}
            <h1 style='text-align: center; font-family:Georgia, serif; margin:0;'>Instrument Descriptions</h1>
            {logo_html}
        </div>
        """,
        unsafe_allow_html=True
    )
    # Seabird CTD Section
    st.write("### Seabird CTD")
    st.write("Working on it")
    # Weather Station Section
    st.write("### Weather Station")
    st.write("Working on it")

# Meet the Team Page
elif page == "Meet the Team":
    # Convert logo to Base64
    logo_path = "images/OceanTech Logo-PURPLE.png"
    base64_logo = get_base64_image(logo_path)

    if base64_logo:
        # Set logo size to match the specified CSS size
        logo_html = f"<img src='data:image/png;base64,{base64_logo}' style='width:150px; height:auto;'>"
    else:
        logo_html = "⚠️ Logo Not Found"

    # Title with Logos on Both Sides
    st.markdown(
        f"""
        <div style="display: flex; align-items: center; justify-content: center; gap: 20px;">
            {logo_html}
            <h1 style='text-align: center; font-family:Georgia, serif; margin:0;'>Meet the Team</h1>
            {logo_html}
        </div>
        """,
        unsafe_allow_html=True
    )

    # Gallery Images & Captions
    gallery_photos = [
        "images/IMG_6540.jpg",
        "images/IMG_4499.jpg",
        "images/IMG_9981.jpg"
    ]
    gallery_captions = [
        "Austin Karpf",
        "Kelly Horak",
        "Sophia Mangrubang"
    ]

    # Validate image existence
    valid_gallery = [(photo, caption) for photo, caption in zip(gallery_photos, gallery_captions) if os.path.exists(photo)]

    if not valid_gallery:
        st.error("⚠️ No valid images found for the gallery. Check file paths.")
    else:
        col1, col2, col3 = st.columns(3)
        columns = [col1, col2, col3]

        for i, (photo, caption) in enumerate(valid_gallery):
            base64_img = get_base64_image(photo)
            if base64_img:
                img_html = f"""
                <div style="text-align:center;">
                    <img src="data:image/jpeg;base64,{base64_img}" style="width:325px; height:325px; object-fit:cover; border-radius:10px;">
                    <p style="font-size:16px; font-weight:bold;">{caption}</p>
                </div>
                """
                with columns[i % 3]:  # Distribute images evenly among columns
                    st.markdown(img_html, unsafe_allow_html=True)
