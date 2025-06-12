import streamlit as st
import pandas as pd
import plotly.graph_objs as go
import folium
from streamlit_folium import st_folium
import time
import os
import base64

import pandas as pd
import plotly.graph_objs as go
import folium

import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1.base_query import FieldFilter, Or, And

from streamlit_folium import st_folium, folium_static
import threading
import random
import json
from datetime import date, time, datetime, timedelta

import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1.base_query import FieldFilter, Or, And


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
page = st.sidebar.selectbox("Select Page", ["Main Page", "Live CTD Data (2025 to Present)", "CTD Data (2015 to 2024)", "What is our Instrument?", "Meet the Team", "Gallery"])

# --- Firebase Init ---
if not firebase_admin._apps:
    cert = json.loads(st.secrets["Certificate"]["data"])
    cred = credentials.Certificate(cert)
    firebase_admin.initialize_app(cred)

db = firestore.client()

# --- Function to fetch CTD data from Firebase ---
@st.cache_data(ttl=60)
def fetch_ctd_data():
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

# Load CSV data for each graph
ctd_csv_file_path = 'ERIS_data_2015-2024.csv'

if page == "Main Page":
    st.markdown("<h1 style='text-align: center; font-family:Georgia, serif;'>Welcome to ERIS</h1>", unsafe_allow_html=True)

    main_image_path = "images/grads.jpg"
    caption = "2024 Graduating Marine Technicians"
    left_logo_path = "images/OceanTech Logo-PURPLE.png"
    right_logo_path = "images/OceanTech Logo-PURPLE.png"

    if os.path.exists(main_image_path):
        base64_image = get_base64_image(main_image_path)
        left_logo = get_base64_image(left_logo_path) if os.path.exists(left_logo_path) else None
        right_logo = get_base64_image(right_logo_path) if os.path.exists(right_logo_path) else None

        st.markdown(
            f"""
            <style>
            .static-image-container {{
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
            .main-image {{
                max-width: 60%;
                height: auto;
                max-height: 500px;
                border-radius: 15px;
                box-shadow: 0 4px 8px rgba(0,0,0,0.2);
            }}
            .caption {{
                text-align: center;
                font-size: 18px;
                font-weight: bold;
                margin-top: 10px;
            }}
            </style>
            <div class="static-image-container">
                {'<img src="data:image/png;base64,' + left_logo + '" class="logo">' if left_logo else ''}
                <img src="data:image/jpeg;base64,{base64_image}" class="main-image">
                {'<img src="data:image/png;base64,' + right_logo + '" class="logo">' if right_logo else ''}
            </div>
            <p class="caption">{caption}</p>
            """,
            unsafe_allow_html=True
        )
    else:
        st.error("⚠️ Static image not found. Please check the file path.")

    # 📹 Navigation Tutorial Button
    st.markdown(
        """
        <style>
            .full-width-link {
                display: block;
                width: 100%;
                background-color: #74bcf7;
                color: black !important;
                text-align: center;
                padding: 15px;
                font-size: 20px;
                font-weight: bold;
                text-decoration: none;
                border-radius: 5px;
            }
            .full-width-link:hover {
                background-color: #5A0C9D;
                color: white !important;
            }
        </style>
        <a href="https://youtu.be/zQ8caaUxIvY?si=NlzA_W-o2h0XHfeM" class="full-width-link" target="_blank">Navigation Tutorial</a>
        """,
        unsafe_allow_html=True
    )


    #🔬 Educational Content
    st.write("### What is ERIS?")
    st.write("ERIS (Exploration and Remote Instrumentation by Students) is a student designed and built cabled observatory that serves as an underwater learning facility at the [University of Washington (UW)](https://www.washington.edu/). Students work with ERIS through Ocean 462. ERIS, with its educational mission, enables undergraduate students to design, build, operate, and maintain a cabled underwater observatory that emulates the NSF Ocean Observatories Initiatives (OOI) Regional Cabled Array, by providing for a continuous data-stream for analysis, interpretation, and communication by students. From inspiration through implementation, this program is focused on the creation and operation of an underwater science sensor network that is physically located off the dock of the School of Oceanography at UW Seattle Campus.")

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

elif page == "Live CTD Data (2025 to Present)":
    def instrument_data_page():
        logo_path = "images/OceanTech Logo-PURPLE.png"
        base64_logo = get_base64_image(logo_path)
        logo_html = f"<img src='data:image/png;base64,{base64_logo}' style='width:150px; height:auto;'>" if base64_logo else "⚠️ Logo Not Found"

        st.markdown(f"""
            <div style="display: flex; align-items: center; justify-content: center; gap: 20px;">
                {logo_html}
                <h1 style='text-align: center; font-family:Georgia, serif; margin:0;'>UW ERIS CTD DATA</h1>
                {logo_html}
            </div>
        """, unsafe_allow_html=True)

        with st.spinner("Loading CTD data..."):
            data = fetch_ctd_data()

        if data is None or data.empty:
            st.warning("No CTD data found.")
            return

        st.caption(f"Last updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")

        st.subheader("Date Range Selection")
        start = st.date_input("Start Date", datetime(2025, 5, 1).date())
        end = st.date_input("End Date", date.today(), min_value=start)

        if end < start:
            st.error("End Date must be on or after Start Date.")
            return

        start_dt = pd.Timestamp(start)
        end_dt = pd.Timestamp(end) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
        filtered_data = data[(data["datetime"] >= start_dt) & (data["datetime"] <= end_dt)]

        if filtered_data.empty:
            st.warning("No CTD data for the selected date range.")
            return

        def add_lines_with_gaps(fig, df, y_col, name, color):
            nan_indices = df[y_col].isna()
            segments = []
            current_segment = []
            for i, is_nan in enumerate(nan_indices):
                if not is_nan:
                    current_segment.append(i)
                else:
                    if current_segment:
                        segments.append(current_segment)
                        current_segment = []
            if current_segment:
                segments.append(current_segment)

            for seg in segments:
                seg_df = df.iloc[seg]
                fig.add_trace(go.Scatter(
                    x=seg_df["datetime"],
                    y=seg_df[y_col],
                    mode='lines',
                    name=name,
                    line=dict(color=color),
                    showlegend=seg == segments[0]
                ))

        fig = go.Figure()
        add_lines_with_gaps(fig, filtered_data, "temperature", "Temperature", "blue")
        add_lines_with_gaps(fig, filtered_data, "salinity", "Salinity", "orange")
        add_lines_with_gaps(fig, filtered_data, "par", "PAR", "green")
        add_lines_with_gaps(fig, filtered_data, "conductivity", "Conductivity", "purple")
        add_lines_with_gaps(fig, filtered_data, "oxygen", "Oxygen", "gold")
        add_lines_with_gaps(fig, filtered_data, "turbidity", "Turbidity", "red")
        add_lines_with_gaps(fig, filtered_data, "pressure", "Pressure", "black")

        fig.update_layout(
            xaxis_title="Time",
            yaxis_title="Values",
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
                    x=0.5, y=1.15, xanchor='center', yanchor='bottom', bgcolor ="#444", font=dict(color="#FFF"), activecolor="#74bcf7"
                )
            ),
            yaxis=dict(showgrid=True, gridcolor='lightgrey'),
            plot_bgcolor="white",
            paper_bgcolor="lightblue",
            font=dict(family="Georgia, serif", size=12, color="black"),
            legend=dict(x=1.05, y=0.5, xanchor='left', yanchor='middle', bgcolor='rgba(255, 255, 255, 0.5)'),
            margin=dict(l=80, r=80, t=50, b=80),
        )

        st.plotly_chart(fig, use_container_width=True)

        # ======= CHANGED SECTION START =======
        # Prepare CSV data once before the columns
        csv_data = filtered_data.to_csv(index=False)

        st.download_button("Download CTD Data", csv_data, "ctd_data.csv")

        st.dataframe(filtered_data, use_container_width=True)

        st.write("### Instrument Location")
        map_center = [47.64935, -122.3127]
        m = folium.Map(location=map_center, zoom_start=15, width='100%', height='600px')

        folium.Marker(
            location=map_center,
            tooltip="CTD: 47.64935, -122.3127",
            icon=folium.Icon(icon='star', prefix='fa', color='orange')
        ).add_to(m)

        folium_static(m, width=1500, height=500)

    instrument_data_page()


# elif page == "Live CTD Data (2025 to Present)":
#     def instrument_data_page():
#         logo_path = "images/OceanTech Logo-PURPLE.png"
#         base64_logo = get_base64_image(logo_path)
#         logo_html = f"<img src='data:image/png;base64,{base64_logo}' style='width:150px; height:auto;'>" if base64_logo else "⚠️ Logo Not Found"

#         st.markdown(f"""
#             <div style="display: flex; align-items: center; justify-content: center; gap: 20px;">
#                 {logo_html}
#                 <h1 style='text-align: center; font-family:Georgia, serif; margin:0;'>UW ERIS CTD DATA</h1>
#                 {logo_html}
#             </div>
#         """, unsafe_allow_html=True)

#         if st.button("🔄 Refresh Data Now"):
#             fetch_ctd_data.clear()

#         with st.spinner("Loading CTD data..."):
#             data = fetch_ctd_data()

#         if data is None or data.empty:
#             st.warning("No CTD data found.")
#             return

#         st.caption(f"Last updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")

#         st.subheader("Date Range Selection")
#         start = st.date_input("Start Date", datetime(2025, 5, 1).date())
#         end = st.date_input("End Date", date.today(), min_value=start)

#         if end < start:
#             st.error("End Date must be on or after Start Date.")
#             return

#         start_dt = pd.Timestamp(start)
#         end_dt = pd.Timestamp(end) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
#         filtered_data = data[(data["datetime"] >= start_dt) & (data["datetime"] <= end_dt)]

#         if filtered_data.empty:
#             st.warning("No CTD data for the selected date range.")
#             return

#         def add_lines_with_gaps(fig, df, y_col, name, color):
#             nan_indices = df[y_col].isna()
#             segments = []
#             current_segment = []
#             for i, is_nan in enumerate(nan_indices):
#                 if not is_nan:
#                     current_segment.append(i)
#                 else:
#                     if current_segment:
#                         segments.append(current_segment)
#                         current_segment = []
#             if current_segment:
#                 segments.append(current_segment)

#             for seg in segments:
#                 seg_df = df.iloc[seg]
#                 fig.add_trace(go.Scatter(
#                     x=seg_df["datetime"],
#                     y=seg_df[y_col],
#                     mode='lines',
#                     name=name,
#                     line=dict(color=color),
#                     showlegend=seg == segments[0]
#                 ))

#         fig = go.Figure()
#         add_lines_with_gaps(fig, filtered_data, "temperature", "Temperature", "blue")
#         add_lines_with_gaps(fig, filtered_data, "salinity", "Salinity", "orange")
#         add_lines_with_gaps(fig, filtered_data, "par", "PAR", "green")
#         add_lines_with_gaps(fig, filtered_data, "conductivity", "Conductivity", "purple")
#         add_lines_with_gaps(fig, filtered_data, "oxygen", "Oxygen", "gold")
#         add_lines_with_gaps(fig, filtered_data, "turbidity", "Turbidity", "red")
#         add_lines_with_gaps(fig, filtered_data, "pressure", "Pressure", "black")

#         fig.update_layout(
#             xaxis_title="Time",
#             yaxis_title="Values",
#             height=450,
#             xaxis=dict(
#                 rangeslider=dict(visible=True),
#                 type="date",
#                 rangeselector=dict(
#                     buttons=[
#                         dict(count=1, label="1d", step="day", stepmode="backward"),
#                         dict(count=7, label="1w", step="day", stepmode="backward"),
#                         dict(count=1, label="1m", step="month", stepmode="backward"),
#                         dict(count=6, label="6m", step="month", stepmode="backward"),
#                         dict(step="all")
#                     ],
#                     x=0.5, y=1.15, xanchor='center', yanchor='bottom', bgcolor ="#444", font=dict(color="#FFF"), activecolor="#74bcf7"
#                 )
#             ),
#             yaxis=dict(showgrid=True, gridcolor='lightgrey'),
#             plot_bgcolor="white",
#             paper_bgcolor="lightblue",
#             font=dict(family="Georgia, serif", size=12, color="black"),
#             legend=dict(x=1.05, y=0.5, xanchor='left', yanchor='middle', bgcolor='rgba(255, 255, 255, 0.5)'),
#             margin=dict(l=80, r=80, t=50, b=80),
#         )

#         st.plotly_chart(fig, use_container_width=True)

#         csv_data = filtered_data.to_csv(index=False)
#         # st.download_button("Download CTD Data", csv_data, "ctd_data.csv")
#         with col1:
#             if st.button("🔁 Refresh Page"):
#                 st.experimental_rerun()

#         with col2:
#             csv_data = filtered_data.to_csv(index=False)
#             st.download_button("⬇️ Download CTD Data", csv_data, "ctd_data.csv")

#         st.dataframe(filtered_data, use_container_width=True)

#         st.write("### Instrument Location")
#         map_center = [47.64935, -122.3127]
#         m = folium.Map(location=map_center, zoom_start=15, width='100%', height='600px')

#         folium.Marker(
#             location=map_center,
#             tooltip="CTD: 47.64935, -122.3127",
#             icon=folium.Icon(icon='star', prefix='fa', color='orange')
#         ).add_to(m)

#         folium_static(m, width=1500, height=500)

#     instrument_data_page()

elif page == "CTD Data (2015 to 2024)":
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
    try:
        ctd_data = pd.read_csv(ctd_csv_file_path)
    except Exception as e:
        st.error(f"Failed to load CTD data: {e}")
        st.stop()

    # Convert to datetime and clean
    ctd_data['date'] = pd.to_datetime(ctd_data['date'], errors='coerce')
    ctd_data = ctd_data.dropna(subset=['date'])
    ctd_data.rename(columns={'date': 'time'}, inplace=True)

    # ✅ Clean numeric columns
    for col in ['temperature', 'conductivity', 'par', 'turbidity', 'salinity', 'pressure', 'oxygen']:
        if col in ctd_data.columns:
            ctd_data[col] = pd.to_numeric(ctd_data[col], errors='coerce')
            ctd_data.loc[(ctd_data[col] < -1000) | (ctd_data[col] > 1000), col] = pd.NA

    # ✅ Date range filtering UI
    st.write("### Date Range Selection")
    fixed_start = pd.to_datetime("2015-12-22 19:38:34+00:00")

    # Ensure timezone-aware
    start_date = st.date_input("Start Date", value=fixed_start.date())
    start_date = pd.to_datetime(start_date).tz_localize('UTC')

    end_date = st.date_input("End Date", value=ctd_data['time'].max().date())
    end_date = pd.to_datetime(end_date).tz_localize('UTC')

    # ✅ Filter data within date range
    filtered_ctd_data = ctd_data[
        (ctd_data['time'] >= start_date) & 
        (ctd_data['time'] <= end_date)
    ].sort_values('time')

    # ✅ Plotting
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=filtered_ctd_data['time'], y=filtered_ctd_data['temperature'], mode='lines', name='Temperature', line=dict(color='blue')))
    fig1.add_trace(go.Scatter(x=filtered_ctd_data['time'], y=filtered_ctd_data['conductivity'], mode='lines', name='Conductivity', line=dict(color='purple')))
    fig1.add_trace(go.Scatter(x=filtered_ctd_data['time'], y=filtered_ctd_data['par'], mode='lines', name='PAR', line=dict(color='green')))
    fig1.add_trace(go.Scatter(x=filtered_ctd_data['time'], y=filtered_ctd_data['turbidity'], mode='lines', name='Turbidity', line=dict(color='red')))
    fig1.add_trace(go.Scatter(x=filtered_ctd_data['time'], y=filtered_ctd_data['salinity'], mode='lines', name='Salinity', line=dict(color='orange')))
    fig1.add_trace(go.Scatter(x=filtered_ctd_data['time'], y=filtered_ctd_data['pressure'], mode='lines', name='Pressure', line=dict(color='black')))
    fig1.add_trace(go.Scatter(x=filtered_ctd_data['time'], y=filtered_ctd_data['oxygen'], mode='lines', name='Oxygen', line=dict(color='gold')))

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
                x=0.5, y=1.15, xanchor='center', yanchor='bottom',
                bgcolor="#444",
                font=dict(color="#FFF"),
                activecolor="#74bcf7"
            )
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='lightgrey'
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

# 📌 **Instrument Descriptions Page**
elif page == "What is our Instrument?":
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
    st.write("### Our Seabird CTD (SBE 16plus V2 SeaCAT)")
    
    st.write("#### Overview")
    st.write("The SBE 16plus V2 SeaCAT is a high-precision conductivity and temperature recorder, optionally equipped with a pressure sensor, designed for long-term moored deployments in oceanographic research. Its robust design and versatile sensor integration make it ideal for collecting high-quality oceanographic data over extended periods")
    st.write("Our SBE 16plus V2 SeaCAT, 'Albi' is engineered for long-duration, fixed-site deployments, providing accurate measurements of conductivity, temperature, and optional pressure. It supports integration with various auxiliary sensors, including dissolved oxygen, pH, turbidity, fluorescence, oil-in-water, and Photosynthetically Active Radiation (PAR), enhancing its capability to monitor diverse oceanographic parameters")
    
    st.write("#### How it Works")
    st.write("The instrument operates by recording data at user-programmable intervals ranging from 10 seconds to 4 hours. We have 'Albi' set to a 30 minute interval. Data is stored in internal memory and can also be output in real-time in engineering units or raw hexadecimal format. The SBE 16plus V2 is powered by nine alkaline D-cell batteries, providing sufficient energy for approximately 355,000 samples of conductivity and temperature")
    st.write("To mitigate biofouling, the device includes expendable anti-foulant devices and offers an optional pump for enhanced protection. Its durable construction allows for deployments at depths up to 10,500 meters, making it suitable for a wide range of oceanographic studies")
    
    st.write("#### Our Data Attributes")
    st.write("- Conductivity")
    st.write("- Pressure")
    st.write("- Temperature")
    st.write("- Salinity")
    st.write("- Oxygen")
    st.write("- PAR")
    st.write("- Turbidity")

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

    # Gallery Images, Captions & Subtitles
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
    gallery_subtitles = [
        "Software Engineer/Web Developer",
        "Software Engineer/Web Developer",
        "Software Engineer/Web Developer"
    ]

    # Display in columns
    cols = st.columns(len(gallery_photos))

    for i, col in enumerate(cols):
        with col:
            image_base64 = get_base64_image(gallery_photos[i])
            if image_base64:
                st.markdown(
                    f"""
                    <div style="text-align: center;">
                        <img src="data:image/jpg;base64,{image_base64}"
                             style="width: 250px; height: 250px; object-fit: cover; border-radius: 8px;" />
                        <p style="font-weight: bold; margin-bottom: 4px;">{gallery_captions[i]}</p>
                        <p style="font-size: 0.9em; color: gray; margin-top: 0;">{gallery_subtitles[i]}</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            else:
                st.warning(f"Image not found: {gallery_photos[i]}")

elif page == "Gallery":

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
            <h1 style='text-align: center; font-family:Georgia, serif; margin:0;'>Gallery</h1>
            {logo_html}
        </div>
        """,
        unsafe_allow_html=True
    )

    # Gallery image paths and captions
    gallery_photos = [
        "images/tub.jpg",
        "images/group.jpg",
        "images/grads.jpg",
        "images/ctd.jpg",
        "images/ctdmaintenence.jpg",
        "images/rasppitable.jpg",
        "images/ctdmainetence.jpg",
        "images/ctdrecovery.jpg",
        "images/websiteteam.jpg",
    ]
    gallery_captions = [
        "CTD Calibrations",
        "Deployment Day Spring 2024",
        "2024 Graduating Marine Technicians",
        "Seabird 16plus CTD",
        "CTD Maintenance",
        "Raspberry Pi Setup",
        "CTD Maintenance Team",
        "CTD Recovery",
        "Website Development Team",
    ]

    # ✅ Filter valid gallery images
    valid_gallery = [
        (photo, caption) for photo, caption in zip(gallery_photos, gallery_captions)
        if os.path.exists(photo)
    ]

    if not valid_gallery:
        st.error("⚠️ No valid images found for the gallery. Check file paths.")
    else:
        col1, col2, col3 = st.columns(3)
        columns = [col1, col2, col3]

        for i, (photo, caption) in enumerate(valid_gallery):
            base64_img = get_base64_image(photo)
            if base64_img:
                # ✅ Uniform square image container with consistent formatting
                img_html = f"""
                    <div style="text-align:center; margin-bottom:20px;">
                        <img src="data:image/jpeg;base64,{base64_img}" style="width:100%; border-radius:15px;">
                        <p style="font-size:16px; font-weight:bold; margin-top:10px;">{caption}</p>
                    </div>
                    """


                with columns[i % 3]:  # Distribute images evenly
                    st.markdown(img_html, unsafe_allow_html=True)