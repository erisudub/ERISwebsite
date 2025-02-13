import streamlit as st
import pandas as pd
import plotly.graph_objs as go
import folium
from streamlit_folium import st_folium
import time
import os
import base64
import threading


# Function to encode images to base64
def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except FileNotFoundError:
        return None  # Return None if image doesn't exist

# Set wide layout for the Streamlit page
st.set_page_config(layout="wide")

# Title for the entire page
st.markdown("<h1 style='text-align: center; font-family:Georgia, serif;'>UW ERIS CTD & WEATHER STATION DATA</h1>", unsafe_allow_html=True)

# Sidebar for navigation
st.sidebar.title("Navigation")
page = st.sidebar.selectbox("Go to", ["Main Page", "Instrument Descriptions", "Meet the Team", "Gallery"])

# Load CSV data for each graph
ctd_csv_file_path = 'ctddata.csv'  # Replace with the actual path of the CTD CSV
weather_csv_file_path = 'weatherdata.csv'  # Use the uploaded weather CSV file

# Main Page
if page == "Main Page":
    ctd_data = pd.read_csv(ctd_csv_file_path)
    weather_data = pd.read_csv(weather_csv_file_path, skiprows=1)
    
    # Assign column names to weather_data and confirm them
    weather_data.columns = [
        'Date', 'Time', 'Temp_Out', 'Hi_Temp', 'Low_Temp', 'Out_Hum', 'Dew_Pt',
       'Wind_Speed', 'Wind_Dir', 'Wind_Run', 'col10', 'col11', 'col12', 'col13',
       'col14', 'col15', 'col16', 'col17', 'col18', 'col19', 'col20', 'col21',
       'col22', 'col23', 'col24', 'col25', 'col26', 'col27', 'col28', 'col29',
       'col30', 'col31', 'col32', 'Wind_Samp', 'Wind_Tx', 'ISS_Recept', 'Arc_Int', 'col38'
    ]

    # Combine Date and Time into DateTime for weather data
    weather_data['DateTime'] = pd.to_datetime(weather_data['Date'] + ' ' + weather_data['Time'],
                                               format="%m/%d/%Y %I:%M %p", errors='coerce')
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
    fig2.add_trace(go.Scatter(x=filtered_weather_data['DateTime'], y=filtered_weather_data['Temp_Out'], mode='lines', name='Temperature', line=dict(color='blue')))
    fig2.add_trace(go.Scatter(x=filtered_weather_data['DateTime'], y=filtered_weather_data['Dew_Pt'], mode='lines', name='Dew Point', line=dict(color='purple')))
    fig2.add_trace(go.Scatter(x=filtered_weather_data['DateTime'], y=filtered_weather_data['Out_Hum'], mode='lines', name='Humidity', line=dict(color='green')))

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

# 📌 **Instrument Descriptions Page**
elif page == "Instrument Descriptions":
    st.write("## Description of the Instruments")
    
    # Seabird CTD Section
    st.write("### Seabird CTD")
    st.write("Our Seabird SBE 16plus Conductivity-Temperature-Depth (CTD) sensor is a compact, durable oceanographic instrument. This robust and versatile sensor suite provides accurate measurements of key water quality parameters, making it an essential tool for marine research, environmental monitoring, and climate studies. Our CTD is equipped with sensors to provide data on conductivity (salinity), temperature, and pressure (depth).")

    # Weather Station Section
    st.write("### Weather Station")
    st.write("Our weather station provides real-time atmospheric data, including temperature, humidity, wind speed, and barometric pressure, aiding in climate monitoring and marine research.")

# Meet the Team Page
elif page == "Meet the Team":
    st.write("## Team Members")

# 📌 **Gallery Page**
elif page == "Gallery":

    # List of photos and captions
    photos = [
        "images/tub.jpg",
        "images/group.jpg",
        "images/grads.jpg"
    ]
    captions = [
        "CTD Calibrations",
        "Deployment Day Spring 2024",
        "2024 Graduating Marine Technicians"
    ]

    # Initialize session state variables
    if "current_index" not in st.session_state:
        st.session_state.current_index = 0
    if "auto_switch" not in st.session_state:
        st.session_state.auto_switch = True  # Auto-switch enabled by default

    # Function to update the image index
    def change_image(direction):
        st.session_state.current_index = (st.session_state.current_index + direction) % len(photos)

    # Centered image display
    col1, col2, col3 = st.columns([1, 2, 1])  # Center image
    with col2:
        st.image(
            photos[st.session_state.current_index],
            caption=captions[st.session_state.current_index],
            width=600  # Adjust width as needed
        )

    # **⬅️➡️ Centered Navigation Buttons**
    col1, col2, col3 = st.columns([9, 18, 3])

    with col1:
        if st.button("Backward", key="prev"):
            change_image(-1)
            st.session_state.auto_switch = False  # Stop auto-switching when manually clicked
            st.rerun()

    with col2:
        st.write("")  # Spacer

    with col3:
        if st.button("Forward", key="next"):
            change_image(1)
            st.session_state.auto_switch = False
            st.rerun()

    # Toggle Auto-Slideshow
    # st.session_state.auto_switch = st.toggle("Auto-Slideshow", value=st.session_state.auto_switch)

    # Auto-switch logic without blocking the app
    if st.session_state.auto_switch:
        time.sleep(10)  # Wait 10 seconds
        change_image(1)  # Move to next image
        st.rerun()  # Refresh app

