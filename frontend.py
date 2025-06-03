# import firebase_admin
# from firebase_admin import credentials, firestore
# from google.cloud.firestore_v1.base_query import FieldFilter

# import json
# import os
# from datetime import date, time, datetime, timedelta

# import pandas as pd
# import plotly.graph_objs as go
# import folium

# import streamlit as st
# from streamlit_folium import st_folium


# # --- Streamlit Config ---
# st.set_page_config(layout="wide")

# # --- Title ---
# st.markdown("<h1 style='text-align: center; font-family:Georgia, serif;'>UW ERIS CTD & WEATHER STATION DATA</h1>", unsafe_allow_html=True)

# # --- Firebase Init ---
# if not firebase_admin._apps:
#     cert = json.loads(st.secrets["Certificate"]["data"])
#     cred = credentials.Certificate(cert)
#     firebase_admin.initialize_app(cred)

# db = firestore.client()

# #--- Image Helper ---
# def get_base64_image(image_path):
#     import base64
#     if os.path.exists(image_path):
#         with open(image_path, "rb") as img_file:
#             return base64.b64encode(img_file.read()).decode()
#     return None

# # --- Function to Fetch CTD Data ---
# @st.cache_data(max_entries=10, persist=True)
# def fetch_ctd_data(start_date: date, end_date: date):
#     if not isinstance(start_date, date) or not isinstance(end_date, date):
#         return None

#     # Convert dates to milliseconds (to match Firestore timestamp format)
#     start_ts = int(datetime.combine(start_date, time.min).timestamp() * 1000)
#     end_ts = int(datetime.combine(end_date + timedelta(days=1), time.min).timestamp() * 1000)

#     # Fetch all documents (Firestore doesn't support querying nested fields directly)
#     docs = db.collection("CTD_Data")#.stream()
#     query = docs.order_by("date")
#     results = query.get()
    

#     data = []
#     for doc in results:
#         d = doc.to_dict()
#         try:
#             ts = d.get("date", {}).get("$date")  # Firestore stores timestamp in milliseconds
#             if ts is None:# or not (start_ts <= ts < end_ts):
#                 continue

#             record = {
#                 "datetime": datetime.fromtimestamp(ts / 1000),  # convert ms to datetime
#                 "instrument": d.get("instrument"),
#                 "lat": d.get("lat"),
#                 "lon": d.get("lon"),
#                 "depth1": d.get("depth1"),
#                 "oxygen": d.get("oxygen"),
#                 "conductivity": float(d.get("conductivity", "nan")),
#                 "par": float(d.get("par", "nan")),
#                 "pressure": float(d.get("pressure", "nan")),
#                 "salinity": float(d.get("salinity", "nan")),
#                 "temperature": float(d.get("temperature", "nan")),
#                 "turbidity": float(d.get("turbidity", "nan")),
#             }
#             data.append(record)
#         except Exception as e:
#             print(f"Error processing document: {e}")
#             continue

#     return pd.DataFrame(data) if data else None

# # --- UI: Date Range Selection ---
# st.sidebar.header("Select Date Range")

# # Default to your target range (from provided ms timestamps)
# default_start = datetime.fromtimestamp(1745545207000/ 1000).date()  # July 25, 2025
# default_end = datetime.fromtimestamp(1746781807000/1000).date()
# start = st.sidebar.date_input("Start Date", default_start)
# end = st.sidebar.date_input("End Date", default_end)
# # --- Fetch and Display Data ---
# data = fetch_ctd_data(start, end)

# if data is None or data.empty:
#     st.warning("No CTD data found for the selected date range.")
# else:
#     # --- Line Chart ---
#     st.subheader("Temperature Over Time")
#     fig = go.Figure()
#     fig.add_trace(go.Scatter(
#         x=data["datetime"], y=data["temperature"],
#         mode='lines+markers',
#         name='Temperature (°C)'
#     ))
#     fig.add_trace(go.Scatter(
#         x=data["datetime"], y=data["salinity"],
#         mode='lines+markers',
#         name='Salinity (PSU))'
#     ))
#     fig.add_trace(go.Scatter(
#         x=data["datetime"], y=data["par"],
#         mode='lines+markers',
#         name='PAR'
#     ))
#     fig.add_trace(go.Scatter(
#         x=data["datetime"], y=data["conductivity"],
#         mode='lines+markers',
#         name='Conductivity'
#     ))
#     fig.add_trace(go.Scatter(
#         x=data["datetime"], y=data["oxygen"],
#         mode='lines+markers',
#         name='Oxygen'
#     ))
#     fig.add_trace(go.Scatter(
#         x=data["datetime"], y=data["turbidity"],
#         mode='lines+markers',
#         name='turbidity'
#     ))
#     fig.add_trace(go.Scatter(
#         x=data["datetime"], y=data["pressure"],
#         mode='lines+markers',
#         name='Pressure'
#     ))
#     fig.update_layout(
#         xaxis_title='Date',
#         yaxis_title='Values',
#         template='plotly_white'
#     )
#     st.plotly_chart(fig, use_container_width=True)

#     # --- Map ---
#     st.subheader("Instrument Locations")
#     m = folium.Map(location=[data["lat"].mean(), data["lon"].mean()], zoom_start=10)
#     for _, row in data.iterrows():
#         folium.CircleMarker(
#             location=[row["lat"], row["lon"]],
#             radius=5,
#             popup=f"{row['instrument']}<br>{row['datetime'].strftime('%Y-%m-%d %H:%M:%S')}",
#             color='blue',
#             fill=True
#         ).add_to(m)
#     st_folium(m, width=700, height=500)

#     # --- Raw Data Table ---
#     st.subheader("Raw Data")
#     st.dataframe(data)

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

# --- Firebase Init ---
if not firebase_admin._apps:
    cert = json.loads(st.secrets["Certificate"]["data"])
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

# --- Logo + Title ---
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
        <h1 style='text-align: center; font-family:Georgia, serif; margin:0;'>UW ERIS CTD & WEATHER STATION DATA</h1>
        {logo_html}
    </div>
    """,
    unsafe_allow_html=True
)

# --- Function to Fetch CTD Data ---
@st.cache_data(max_entries=10, persist=True)
def fetch_ctd_data(start_date: date, end_date: date):
    if not isinstance(start_date, date) or not isinstance(end_date, date):
        return None

    start_ts = int(datetime.combine(start_date, time.min).timestamp() * 1000)
    end_ts = int(datetime.combine(end_date + timedelta(days=1), time.min).timestamp() * 1000)

    docs = db.collection("CTD_Data")
    query = docs.order_by("date")
    results = query.get()

    data = []
    for doc in results:
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

# --- Sidebar: Date Range ---
st.sidebar.header("Select Date Range")
default_start = datetime.fromtimestamp(1745545207000 / 1000).date()  # July 25, 2025
default_end = datetime.fromtimestamp(1746781807000 / 1000).date()
start = st.sidebar.date_input("Start Date", default_start)
end = st.sidebar.date_input("End Date", default_end)

# --- Fetch and Display Data ---
data = fetch_ctd_data(start, end)

if data is None or data.empty:
    st.warning("No CTD data found for the selected date range.")
else:
    # --- Section Header ---
    st.markdown("<h2 style='text-align: center; font-family: Georgia, serif;'>ERIS CTD</h2>", unsafe_allow_html=True)

    # --- Line Chart ---
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=data["datetime"], y=data["temperature"], mode='lines+markers', name='Temperature (°C)'))
    fig.add_trace(go.Scatter(x=data["datetime"], y=data["salinity"], mode='lines+markers', name='Salinity (PSU)'))
    fig.add_trace(go.Scatter(x=data["datetime"], y=data["par"], mode='lines+markers', name='PAR'))
    fig.add_trace(go.Scatter(x=data["datetime"], y=data["conductivity"], mode='lines+markers', name='Conductivity'))
    fig.add_trace(go.Scatter(x=data["datetime"], y=data["oxygen"], mode='lines+markers', name='Oxygen'))
    fig.add_trace(go.Scatter(x=data["datetime"], y=data["turbidity"], mode='lines+markers', name='Turbidity'))
    fig.add_trace(go.Scatter(x=data["datetime"], y=data["pressure"], mode='lines+markers', name='Pressure'))

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

    st.plotly_chart(fig, use_container_width=True)

    # --- Download + Table ---
    csv = data.to_csv(index=False)
    st.download_button("Download CTD Data", csv, "ctd_data.csv")
    st.dataframe(data, use_container_width=True)
