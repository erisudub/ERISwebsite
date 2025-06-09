import streamlit as st
import pandas as pd
import plotly.graph_objs as go
import folium
from streamlit_folium import st_folium
import time
import os
import base64
import threading
import random

# Function to encode images to base64
def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except FileNotFoundError:
        return None  # Return None if image doesn't exist

# Set wide layout for the Streamlit page
st.set_page_config(layout="wide")

# ✅ Change top navigation bar to light blue and fix sidebar spacing
st.markdown(
    """
    <style>
        /* Change very top bar color */
        header[data-testid="stHeader"] {
            background-color: #74bcf7 !important;  /* Light Blue */
        }
        /* Change top navigation bar color */
        section[data-testid="stHeader"] {
            background: #6A0DAD !important;  /* Dark Purple */
        }
        /* Change the outline of the sidebar select box */
        div[data-baseweb="select"] > div {
            border-color: purple !important;
        }
        /* Change hover and selected item color */
        div[data-baseweb="select"] > div:focus {
            border-color: purple !important;
            box-shadow: 0 0 5px blue !important;
        }
        /* Make sidebar logo full-width */
        [data-testid="stSidebar"] {
            padding-top: 0px !important;
        }
        .sidebar-logo-container img {
            width: 100% !important;
            display: block;
        }
        /* Remove margin below the sidebar title */
        div[data-testid="stSidebar"] h1 {
            margin-bottom: 0px !important;
        }
        /* Reduce space above the selectbox */
        div[data-testid="stSidebar"] > div:nth-child(2) {
            margin-top: -10px !important;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# ✅ Add a full-width logo to the top of the sidebar
st.sidebar.image("images/New Oceanography-logo-banner-BLUE.png", use_container_width=True)

# Sidebar for navigation
st.sidebar.title("Navigation")

# Sidebar navigation dropdown (No "Go to" label, fixed spacing)
page = st.sidebar.selectbox("Select Page", ["Main Page", "Instrument Data"])

# Load CSV data for each graph
ctd_csv_file_path = 'ERIS_data_2015-2024.csv'  # Replace with the actual path of the CTD CSV


# Main Page
if page == "Main Page":
    st.markdown("<h1 style='text-align: center; font-family:Georgia, serif;'>Welcome to ERIS</h1>", unsafe_allow_html=True)

    # 📌 **Main Image Slider**
    photos = [
        "images/tub.jpg",
        "images/group.jpg",
        "images/grads.jpg",
        "images/ctd.jpg",
        "images/ctdmaintenence.jpg",
        "images/rasppitable.jpg",
    ]
    captions = [
        "CTD Calibrations",
        "Deployment Day Spring 2024",
        "2024 Graduating Marine Technicians",
        "Seabird 16plus CTD",
        "CTD Maintenance",
        "Raspberry Pi Setup",
    ]

    # ✅ **Filter out non-existing images**
    valid_images = [(photo, captions[i]) for i, photo in enumerate(photos) if os.path.exists(photo)]

    if not valid_images:
        st.error("⚠️ No valid images found for the main gallery. Check file paths.")
        st.write("Debug: Expected paths →", photos)
        valid_photos, valid_captions = [], []
    else:
        valid_photos, valid_captions = zip(*valid_images)

    # ✅ **Initialize session state**
    if "current_index" not in st.session_state:
        st.session_state.current_index = 0
    if "auto_switch" not in st.session_state:
        st.session_state.auto_switch = True
    if "animation_key" not in st.session_state:
        st.session_state.animation_key = 0  

    # ✅ **Function to change the displayed image**
    def change_image(direction):
        if valid_photos:
            st.session_state.current_index = (st.session_state.current_index + direction) % len(valid_photos)
            st.session_state.animation_key += 1  
            st.rerun()

    # ✅ **Logo Paths**
    left_logo_path = "images/OceanTech Logo-PURPLE.png" 
    right_logo_path = "images/OceanTech Logo-PURPLE.png"  

    # ✅ **Convert images to base64**
    if valid_photos:
        base64_image = get_base64_image(valid_photos[st.session_state.current_index])
        left_logo = get_base64_image(left_logo_path)
        right_logo = get_base64_image(right_logo_path)

        st.markdown(
            f"""
            <style>
            .slider-container {{
                display: flex;
                justify-content: center;
                align-items: center;
                width: 100%;
            }}
            .logo {{
                width: 250px;
                height: auto;
                margin: 0 20px;
            }}
            .slide-image {{
                max-width: 60%;
                height: auto;
                max-height: 500px;
                animation: slideIn 0.7s ease-in-out;
            }}
            .caption {{
                text-align: center;
                font-size: 18px;
                font-weight: bold;
                margin-top: 10px;
            }}
            @keyframes slideIn {{
                from {{
                    transform: translateX(100%);
                    opacity: 0;
                }}
                to {{
                    transform: translateX(0);
                    opacity: 1;
                }}
            }}
            </style>
            <div class="slider-container">
                {'<img src="data:image/png;base64,' + left_logo + '" class="logo">' if left_logo else ''}
                <img src="data:image/jpeg;base64,{base64_image}" class="slide-image" key="{st.session_state.animation_key}">
                {'<img src="data:image/png;base64,' + right_logo + '" class="logo">' if right_logo else ''}
            </div>
            <p class="caption">{valid_captions[st.session_state.current_index]}</p>
            """,
            unsafe_allow_html=True
        )

    st.markdown(
        """
        <style>
            .full-width-link {
                display: block;
                width: 100%;
                background-color: #74bcf7;  /* Background color (Light Blue) */
                color: black;  /* Text color */
                text-align: center;
                padding: 15px;
                font-size: 20px;
                font-weight: bold;
                text-decoration: none;
                border-radius: 5px;
            }
            .full-width-link:hover {
                background-color: #5A0C9D; /* Darker shade on hover */
            }
        </style>

        <a href="https://youtu.be/zQ8caaUxIvY?si=NlzA_W-o2h0XHfeM" class="full-width-link" target="_blank">Navigation Tutorial</a>
        """,
        unsafe_allow_html=True
    )


    st.write("### What is ERIS?")
    st.write("ERIS (Exploration and Remote Instrumentation by Students) is a student designed and built cabled observatory that serves as an underwater learning facility at the University of Washington (UW). Students work with ERIS through Ocean 462. ERIS, with its educational mission, enables undergraduate students to design, build, operate, and maintain a cabled underwater observatory that emulates the NSF Ocean Observatories Initiatives (OOI) Regional Cabled Array, by providing for a continuous data-stream for analysis, interpretation, and communication by students. From inspiration through implementation, this program is focused on the creation and operation of an underwater science sensor network that is physically located off the dock of the School of Oceanography at UW Seattle Campus")
    st.write("### What is ERIS?")
    st.write("ERIS, which stands for Exploration and Remote Instrumentation by Students, is a student designed and built cabled observatory that serves as an underwater learning facility at the University of Washington (UW). Students work with ERIS through Ocean 462. ERIS, with its educational mission, enables undergraduate students to design, build, operate, and maintain a cabled underwater observatory that emulates the NSF")
    st.write("Ocean Observatories Initiatives (OOI) Regional Cabled Array, by providing for a continuous data-stream for analysis, interpretation, and communication by students. From inspiration through implementation, this program is focused on the creation and operation of an underwater science sensor network that is physically located off the dock of the School of Oceanography at UW Seattle Campus.")
    

    col1, col2 = st.columns([1, 1])

    with col1:
        st.write("### Key Science Questions")
        st.write("-  How do anthropogenic processes mediate natural processes in the marine environment?")
        st.write("-  What are the temporal and spatial scales over which anthropogenic activities occur?")
        st.write("-  How does the temperature, light, chemistry, and velocity of the marine environment change temporally and spatially?")
        st.write("-  What unique ecological systems are present?")
        st.write("-  What is the composition, configuration, and concentration of organisms in the different ecological systems?")
        st.write("-  How are these systems impacted by both natural and anthropogenic events?")
        st.write(" ")
        st.write("ERIS will also encourage students to explore a range of technical considerations.")

    with col2:
        st.image("images/tub.jpg", use_container_width = True)

    col3, col4 = st.columns([1, 1])

    with col3:
        st.markdown("<!-- This is an invisible comment -->", unsafe_allow_html=True)
        st.image("images/ctdmaintenence.jpg", use_container_width = True)

    with col4:
        st.write("### Technology Questions:")
        st.write("-  What sensor(s) design is required?")
        st.write("-  What sample rate and duty cycle is needed?")
        st.write("-  What measurement accuracy is need and what can be achieved?")
        st.write("-  How should remote observations be made?")
        st.write("-  How can sensors be deployed and serviced?")
        st.write("-  What are the power requirements?")
        st.write("-  How will data be delivered, stored, and accessed?")
        st.write("-  How will data be analyzed, interpreted, visualized, and communicated?")
        st.write(" ")
        st.write("As the observatory is being implemented, students focus on maintaining the components, as well as collecting, managing, and analyzing the continuous streams of data the observatory will produce. Integral to the ERIS program is the ability to distribute the collected data so that it may be interpreted by interested parties at the UW and worldwide.")

    st.write("### Course: OCEAN 462: Ocean Technology Studio")
    st.write("Hands-on experience to build technical, science, and management skills in ocean technology through small group projects. Projects may include instrument design and building, data analysis, and/or participation in an on-going ocean technology initiative. Offered: AWSp. Can be taken for 1-5 credits, with a max of 15.")
    st.write("For more information, visit [MyPlan](https://myplan.uw.edu/course/#/courses?states=N4Igwg9grgTgzgUwMoIIYwMYAsQC4TAA6IAZhDALYAiqALqsbkSBqhQA5RyPGJ20AbBMQA0xAJZwUGWuIgA7FOmyNaMKAjEhJASXlw1UGeSWYsjEqgGItARw0wAnkjXj5Acx4hRxACapHbjxmAEYLKxtiACZw601iAGZYyJAAFmT4kABWDK0ANgyAXy0DdFoAUXlfABVxCgQg3ABtAAYRAE48loBdLTcMAShfBAA5BQB5dgRFBBk5fVV1TP7B4YAlBtcZBF9pWQVGw2X5AaGEAAUYBCvbOA37cSvfRY0%2Bk9WEaoAjVD35w6WJSwEAA7uN5AJHOcMMhZvsFnhLHEgaDwZC9OdrnAFH8DkUUSCAEIwUGIXLELCoKRoMw7ckgXySAYQRAAQV8ADdUCcdqYVIiIghCiBCkA).")

    #     # ✅ **Auto-switch logic**
    # if st.session_state.auto_switch and valid_photos:
    #     time.sleep(5)  
    #     change_image(1)

# ✅ Instrument Data Page
if page == "Instrument Data":
    # Convert logo to Base64
    logo_path = "images/OceanTech Logo-PURPLE.png"
    base64_logo = get_base64_image(logo_path)

    if base64_logo:
        logo_html = f"<img src='data:image/png;base64,{base64_logo}' style='width:150px; height:auto;'>"
    else:
        logo_html = "⚠️ Logo Not Found"

    # Title with Logos on Both Sides
    st.markdown(
        f"""
        <div style="display: flex; align-items: center; justify-content: center; gap: 20px;">
            {logo_html}
            <h1 style='text-align: center; font-family:Georgia, serif; margin:0;'>UW ERIS CTD Data</h1>
            {logo_html}
        </div>
        """,
        unsafe_allow_html=True
    )

    # ✅ Load and prepare CTD data
    ctd_data = pd.read_csv(ctd_csv_file_path)

    # Convert to datetime and clean
    ctd_data['date'] = pd.to_datetime(ctd_data['date'], errors='coerce')
    ctd_data = ctd_data.dropna(subset=['date'])
    ctd_data.rename(columns={'date': 'time'}, inplace=True)

    # ✅ Clean numeric columns, but preserve rows
    for col in ['temperature', 'conductivity', 'par', 'turbidity', 'salinity', 'pressure', 'oxygen']:
        if col in ctd_data.columns:
            ctd_data[col] = pd.to_numeric(ctd_data[col], errors='coerce')
            ctd_data.loc[(ctd_data[col] < -1000) | (ctd_data[col] > 1000), col] = pd.NA

    # ✅ Date range filtering UI
    st.write("### Date Range Selection")
    fixed_start = pd.to_datetime("2015-12-22 19:38:34+00:00")

# Make sure start_date has timezone info
    start_date = st.date_input("Start Date", value=fixed_start.date())

# Convert to datetime with UTC timezone (timezone-aware)
    start_date = pd.to_datetime(start_date).tz_localize('UTC')

# Similarly for end_date (assuming you want timezone-aware)
    end_date = st.date_input("End Date", value=ctd_data['time'].max().date())
    end_date = pd.to_datetime(end_date).tz_localize('UTC')


    # ✅ Filter data within date range
    filtered_ctd_data = ctd_data[
        (ctd_data['time'] >= start_date) &
        (ctd_data['time'] <= end_date)
    ].sort_values('time')

    # ✅ OPTIONAL: Interpolate missing values (if desired)
    # filtered_ctd_data = filtered_ctd_data.interpolate(method="time")

    # ✅ Plotting
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=filtered_ctd_data['time'], y=filtered_ctd_data['temperature'], mode='lines', name='Temperature', line=dict(color='blue')))
    fig1.add_trace(go.Scatter(x=filtered_ctd_data['time'], y=filtered_ctd_data['conductivity'], mode='lines', name='Conductivity', line=dict(color='purple')))
    fig1.add_trace(go.Scatter(x=filtered_ctd_data['time'], y=filtered_ctd_data['par'], mode='lines', name='PAR', line=dict(color='green')))
    fig1.add_trace(go.Scatter(x=filtered_ctd_data['time'], y=filtered_ctd_data['turbidity'], mode='lines', name='Turbidity', line=dict(color='red')))
    fig1.add_trace(go.Scatter(x=filtered_ctd_data['time'], y=filtered_ctd_data['salinity'], mode='lines', name='Salinity', line=dict(color='orange')))
    fig1.add_trace(go.Scatter(x=filtered_ctd_data['time'], y=filtered_ctd_data['pressure'], mode='lines', name='Pressure', yaxis='y2', line=dict(color='black')))
    fig1.add_trace(go.Scatter(x=filtered_ctd_data['time'], y=filtered_ctd_data['oxygen'], mode='lines', name='Oxygen', line=dict(color='gold')))

    # ✅ Layout config
    fig1.update_layout(
        title="UW ERIS CTD MEASUREMENTS",
        xaxis_title="Time",
        yaxis_title="Values",
        width=1000,
        height=500,
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
        yaxis=dict(
            title="Temp, Cond., PAR, Turbidity, Salinity, Oxygen",
            showgrid=True,
            gridcolor='lightgrey'
        ),
        yaxis2=dict(
            title="Pressure",
            overlaying='y',
            side='right'
        ),
        plot_bgcolor="white",
        paper_bgcolor="lightblue",
        font=dict(family="Georgia, serif", size=12, color="black"),
        legend=dict(
            x=1.05,
            y=0.5,
            xanchor='left',
            yanchor='middle',
            traceorder="normal",
            bgcolor='rgba(255, 255, 255, 0.5)'
        ),
        margin=dict(l=80, r=80, t=50, b=80),
        autosize=False
    )

    st.plotly_chart(fig1, use_container_width=True)

    # ✅ Table & download
    columns_to_display = ['time', 'instrument', 'lat', 'lon', 'depth1', 'oxygen', 'conductivity', 'par', 'pressure', 'salinity', 'temperature', 'turbidity']
    filtered_display_data = filtered_ctd_data[columns_to_display]
    st.dataframe(filtered_display_data)
    st.download_button("Download CTD Data", filtered_display_data.to_csv(index=False), "ctd_data.csv")
