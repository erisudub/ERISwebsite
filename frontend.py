import streamlit as st
import pandas as pd
import plotly.graph_objs as go
from firebase_admin import credentials, firestore, initialize_app
from datetime import datetime

# Initialize Firebase
@st.cache_resource
def init_firebase():
    cred = credentials.Certificate("eris-db-firebase-adminsdk.json")  # Replace with actual path
    initialize_app(cred)
    return firestore.client()

db = init_firebase()

# Fetch Firebase CTD data
@st.cache_data
def fetch_ctd_data():
    collection_ref = db.collection("ctd_data")
    docs = collection_ref.stream()

    data = []
    for doc in docs:
        entry = doc.to_dict()
        try:
            entry['datetime'] = pd.to_datetime(entry['datetime'])
        except:
            entry['datetime'] = pd.NaT
        data.append(entry)

    df = pd.DataFrame(data)
    return df

firebase_data = fetch_ctd_data()

# Load CSV data
@st.cache_data
def load_csv_data():
    df = pd.read_csv("ERIS_data_2015-2024.csv")
    df['datetime'] = pd.to_datetime(df['date'], errors='coerce')
    return df

csv_data = load_csv_data()

# Set up Streamlit interface
st.title("CTD Data Visualization and Comparison")

# Combined unique station list
stations = sorted(set(firebase_data['station'].dropna().unique()) | set(csv_data['station'].dropna().unique()))
selected_station = st.selectbox("Select Station", stations)

# Filter by station
firebase_station = firebase_data[firebase_data['station'] == selected_station]
csv_station = csv_data[csv_data['station'] == selected_station]

# Available columns for plotting
numeric_cols = ['temperature', 'salinity', 'pressure', 'depth']  # adjust as needed
available_cols = [col for col in numeric_cols if col in firebase_station.columns and col in csv_station.columns]
selected_col = st.selectbox("Select Variable to Plot", available_cols)

# Date range filter
min_date = min(firebase_station['datetime'].min(), csv_station['datetime'].min())
max_date = max(firebase_station['datetime'].max(), csv_station['datetime'].max())

start_date = st.date_input("Start Date", min_value=min_date.date(), max_value=max_date.date(), value=min_date.date())
end_date = st.date_input("End Date", min_value=start_date, max_value=max_date.date(), value=max_date.date())

start_dt = pd.to_datetime(start_date)
end_dt = pd.to_datetime(end_date) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)

firebase_filtered = firebase_station[(firebase_station['datetime'] >= start_dt) & (firebase_station['datetime'] <= end_dt)]
csv_filtered = csv_station[(csv_station['datetime'] >= start_dt) & (csv_station['datetime'] <= end_dt)]

# Plotting
fig = go.Figure()

# CSV trace
fig.add_trace(go.Scatter(
    x=csv_filtered['datetime'],
    y=csv_filtered[selected_col],
    mode='lines+markers',
    name=f'CSV - {selected_col}',
    line=dict(color='blue')
))

# Firebase trace
fig.add_trace(go.Scatter(
    x=firebase_filtered['datetime'],
    y=firebase_filtered[selected_col],
    mode='lines+markers',
    name=f'Firebase - {selected_col}',
    line=dict(color='red', dash='dot')
))

fig.update_layout(
    title=f"{selected_col.capitalize()} at {selected_station}",
    xaxis_title="Datetime",
    yaxis_title=selected_col.capitalize(),
    height=600,
    plot_bgcolor="white",
    paper_bgcolor="lightgray",
    font=dict(family="Arial", size=12),
    xaxis=dict(rangeslider=dict(visible=True), type="date"),
    legend=dict(x=1, y=1),
)

st.plotly_chart(fig, use_container_width=True)

# Optional: show raw data
with st.expander("Show Raw Data"):
    st.subheader("Firebase Data")
    st.dataframe(firebase_filtered)
    st.subheader("CSV Data")
    st.dataframe(csv_filtered)


# import streamlit as st
# import pandas as pd
# import plotly.graph_objs as go
# import folium
# from streamlit_folium import folium_static
# import json
# from datetime import datetime, date
# import base64
# import firebase_admin
# from firebase_admin import credentials, firestore

# # --- Firebase Initialization ---
# if not firebase_admin._apps:
#     # Load Firebase service account credentials from secrets
#     cert = json.loads(st.secrets["Certificate"]["data"])
#     cred = credentials.Certificate(cert)
#     firebase_admin.initialize_app(cred)
# db = firestore.client()

# # --- Helper function to get base64 image for logos ---
# def get_base64_image(image_path):
#     try:
#         with open(image_path, "rb") as img_file:
#             return base64.b64encode(img_file.read()).decode()
#     except FileNotFoundError:
#         return None

# # --- Function to fetch CTD data from Firebase ---
# @st.cache_data(ttl=600)
# def fetch_ctd_data():
#     docs = db.collection("CTD_Data").order_by("date").get()
#     data = []
#     for doc in docs:
#         d = doc.to_dict()
#         try:
#             ts = d.get("date", {}).get("$date")
#             if ts is None:
#                 continue
#             record = {
#                 "datetime": datetime.fromtimestamp(ts / 1000),
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

# # --- Streamlit page layout ---
# st.set_page_config(layout="wide")

# # --- Instrument Data Page ---
# def instrument_data_page():
#     logo_path = "images/OceanTech Logo-PURPLE.png"
#     base64_logo = get_base64_image(logo_path)
#     logo_html = f"<img src='data:image/png;base64,{base64_logo}' style='width:150px; height:auto;'>" if base64_logo else "⚠️ Logo Not Found"
#     st.markdown(f"""
#         <div style="display: flex; align-items: center; justify-content: center; gap: 20px;">
#             {logo_html}
#             <h1 style='text-align: center; font-family:Georgia, serif; margin:0;'>UW ERIS CTD DATA</h1>
#             {logo_html}
#         </div>
#     """, unsafe_allow_html=True)

#     with st.spinner("Loading CTD data..."):
#         data = fetch_ctd_data()

#     if data is None or data.empty:
#         st.warning("No CTD data found.")
#         return

#     st.subheader("Date Range Selection")
#     start = st.date_input("Start Date", datetime(2025, 5, 1).date())
#     end = st.date_input("End Date", date.today(), min_value=start)

#     if end < start:
#         st.error("End Date must be on or after Start Date.")
#         return

#     start_dt = pd.Timestamp(start)
#     end_dt = pd.Timestamp(end) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
#     filtered_data = data[(data["datetime"] >= start_dt) & (data["datetime"] <= end_dt)]

#     if filtered_data.empty:
#         st.warning("No CTD data for the selected date range.")
#         return

#     # --- NEW CODE START ---
#     def add_lines_with_gaps(fig, df, y_col, name, color):
#         nan_indices = df[y_col].isna()
#         segments = []
#         current_segment = []
#         for i, is_nan in enumerate(nan_indices):
#             if not is_nan:
#                 current_segment.append(i)
#             else:
#                 if current_segment:
#                     segments.append(current_segment)
#                     current_segment = []
#         if current_segment:
#             segments.append(current_segment)

#         for seg in segments:
#             seg_df = df.iloc[seg]
#             fig.add_trace(go.Scatter(
#                 x=seg_df["datetime"],
#                 y=seg_df[y_col],
#                 mode='lines',
#                 name=name,
#                 line=dict(color=color),
#                 showlegend=seg == segments[0]
#             ))

#     fig = go.Figure()
#     add_lines_with_gaps(fig, filtered_data, "temperature", "Temperature", "blue")
#     add_lines_with_gaps(fig, filtered_data, "salinity", "Salinity", "orange")
#     add_lines_with_gaps(fig, filtered_data, "par", "PAR", "green")
#     add_lines_with_gaps(fig, filtered_data, "conductivity", "Conductivity", "purple")
#     add_lines_with_gaps(fig, filtered_data, "oxygen", "Oxygen", "gold")
#     add_lines_with_gaps(fig, filtered_data, "turbidity", "Turbidity", "red")
#     add_lines_with_gaps(fig, filtered_data, "pressure", "Pressure", "black")

#     fig.update_layout(
#         xaxis_title="Time",
#         yaxis_title="Values",
#         height=450,
#         xaxis=dict(
#             rangeslider=dict(visible=True),
#             type="date",
#             rangeselector=dict(
#                 buttons=[
#                     dict(count=1, label="1d", step="day", stepmode="backward"),
#                     dict(count=7, label="1w", step="day", stepmode="backward"),
#                     dict(count=1, label="1m", step="month", stepmode="backward"),
#                     dict(count=6, label="6m", step="month", stepmode="backward"),
#                     dict(step="all")
#                 ],
#                 x=0.5, y=1.15, xanchor='center', yanchor='bottom'
#             )
#         ),
#         yaxis=dict(showgrid=True, gridcolor='lightgrey'),
#         plot_bgcolor="white",
#         paper_bgcolor="lightblue",
#         font=dict(family="Georgia, serif", size=12, color="black"),
#         legend=dict(x=1.05, y=0.5, xanchor='left', yanchor='middle', bgcolor='rgba(255, 255, 255, 0.5)'),
#         margin=dict(l=80, r=80, t=50, b=80),
#     )

#     st.plotly_chart(fig, use_container_width=True)

#     csv_data = filtered_data.to_csv(index=False)
#     st.download_button("Download CTD Data", csv_data, "ctd_data.csv")

#     st.dataframe(filtered_data, use_container_width=True)
#     # --- NEW CODE END ---

#     st.write("### Instrument Location")
#     map_center = [47.64935, -122.3127]
#     m = folium.Map(location=map_center, zoom_start=15, width='100%', height='600px')

#     folium.Marker(
#         location=map_center,
#         tooltip="CTD: 47.64935, -122.3127",
#         icon=folium.Icon(icon='star', prefix='fa', color='orange')
#     ).add_to(m)

#     folium_static(m, width=1500, height=500)


# # --- Call the page function ---
# instrument_data_page()

