import streamlit as st
import pandas as pd
import plotly.graph_objs as go
import folium
from streamlit_folium import folium_static
import json
from datetime import datetime, date
import base64
import firebase_admin
from firebase_admin import credentials, firestore

# --- Firebase Initialization ---
if not firebase_admin._apps:
    cert = json.loads(st.secrets["Certificate"]["data"])
    cred = credentials.Certificate(cert)
    firebase_admin.initialize_app(cred)
db = firestore.client()

# --- Helper function to get base64 image for logos ---
def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except FileNotFoundError:
        return None

# --- Function to fetch CTD data from Firebase ---
@st.cache_data(ttl=600)
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

# --- Function to load CSV data and preprocess ---
@st.cache_data(ttl=600)
def load_ctd_csv_data(csv_path):
    df = pd.read_csv(csv_path)

    if 'date' in df.columns:
        df['datetime'] = pd.to_datetime(df['date'], utc=True, errors='coerce')
        st.write(f"CSV data date range: {df['datetime'].min()} to {df['datetime'].max()}")
        df.drop(columns=['date'], inplace=True)
    else:
        df['datetime'] = pd.NaT

    for col in ['temperature', 'conductivity', 'par', 'turbidity', 'salinity', 'pressure', 'oxygen']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            df = df[(df[col] > -1000) & (df[col] < 1000)]
            st.write(f"{col}: {df[col].notna().sum()} non-empty values")

    return df

# --- Streamlit page layout ---
st.set_page_config(layout="wide")

# --- Sidebar and Navigation ---
st.sidebar.title("Navigation")
page = st.sidebar.selectbox("Select Page", ["Main Page", "Instrument Data"])

if page == "Instrument Data":
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

    with st.spinner("Loading CTD data from Firebase..."):
        firebase_data = fetch_ctd_data()

    with st.spinner("Loading CTD data from CSV..."):
        ctd_csv_file_path = 'ERIS_data_2015-2024.csv'
        csv_data = load_ctd_csv_data(ctd_csv_file_path)

    if firebase_data is None and csv_data is None:
        st.warning("No CTD data available from Firebase or CSV.")
        st.stop()

    firebase_data['source'] = 'Firebase'
    csv_data['source'] = 'CSV'

    common_cols = list(set(firebase_data.columns).intersection(set(csv_data.columns)))
    firebase_data = firebase_data[common_cols]
    csv_data = csv_data[common_cols]

    combined_df = pd.concat([firebase_data, csv_data], ignore_index=True)
    combined_df['datetime'] = pd.to_datetime(combined_df['datetime'], errors='coerce')
    combined_df = combined_df.dropna(subset=['datetime'])
    combined_df = combined_df.sort_values('datetime')

    st.write("Combined columns:", combined_df.columns)

    st.subheader("Date Range Selection")
    min_date = combined_df['datetime'].min().date()
    max_date = combined_df['datetime'].max().date()

    start_date = st.date_input("Start Date", min_value=min_date, max_value=max_date, value=min_date)
    end_date = st.date_input("End Date", min_value=start_date, max_value=max_date, value=max_date)

    if end_date < start_date:
        st.error("End Date must be on or after Start Date.")
        st.stop()

    start_dt = pd.Timestamp(start_date)
    end_dt = pd.Timestamp(end_date) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)

    filtered_data = combined_df[(combined_df['datetime'] >= start_dt) & (combined_df['datetime'] <= end_dt)]

    if filtered_data.empty:
        st.warning("No CTD data for the selected date range.")
        st.stop()

    def add_lines_with_gaps(fig, df, y_col, name, color, yaxis='y'):
        nan_indices = df[y_col].isna() if y_col in df.columns else []
        if len(nan_indices) == 0:
            return
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

        for idx, seg in enumerate(segments):
            seg_df = df.iloc[seg]
            fig.add_trace(go.Scatter(
                x=seg_df['datetime'],
                y=seg_df[y_col],
                mode='lines',
                name=f"{name} ({seg_df['source'].iloc[0]})" if 'source' in seg_df.columns else name,
                line=dict(color=color),
                yaxis=yaxis,
                showlegend=idx == 0
            ))

    fig = go.Figure()
    parameters = [
        ("temperature", "Temperature", "blue", 'y'),
        ("salinity", "Salinity", "orange", 'y'),
        ("par", "PAR", "green", 'y'),
        ("conductivity", "Conductivity", "purple", 'y'),
        ("oxygen", "Oxygen", "gold", 'y'),
        ("turbidity", "Turbidity", "red", 'y'),
        ("pressure", "Pressure", "black", 'y'),
    ]

    for col, label, color, yaxis in parameters:
        if col in filtered_data.columns:
            add_lines_with_gaps(fig, filtered_data, col, label, color, yaxis)

    fig.update_layout(
        xaxis_title="Time",
        yaxis_title="Values",
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
        yaxis=dict(showgrid=True, gridcolor='lightgrey', title="Values"),
        plot_bgcolor="white",
        paper_bgcolor="lightblue",
        font=dict(family="Georgia, serif", size=12, color="black"),
        legend=dict(x=1.05, y=0.5, xanchor='left', yanchor='middle', bgcolor='rgba(255, 255, 255, 0.5)'),
        margin=dict(l=80, r=80, t=50, b=80),
    )

    st.plotly_chart(fig, use_container_width=True)

    display_cols = ['datetime', 'instrument', 'lat', 'lon', 'depth1', 'oxygen', 'conductivity', 'par', 'pressure', 'salinity', 'temperature', 'turbidity']
    filtered_display = filtered_data[display_cols].copy()

    st.download_button("Download Combined CTD Data", filtered_display.to_csv(index=False), "combined_ctd_data.csv")
    st.dataframe(filtered_display, use_container_width=True)



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

