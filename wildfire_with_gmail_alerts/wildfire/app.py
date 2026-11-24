"""
app.py — Streamlit Wildfire Risk Dashboard
Includes automatic Gmail alert using YAML credentials.
"""

import os
import base64
from datetime import datetime
import joblib
import numpy as np
import pandas as pd
import streamlit as st
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from sklearn.neighbors import KDTree
from math import radians
import folium
from streamlit_folium import st_folium
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import yaml
from folium.plugins import MarkerCluster, HeatMap  # Import HeatMap

# ------------------ GMAIL CONFIG ------------------
try:
    CONFIG_PATH = r"C:\Users\tanvi\OneDrive\Desktop\final prj\wildfire_with_gmail_alerts\wildfire\config.yaml"
    with open(CONFIG_PATH, "r") as f:
        config = yaml.safe_load(f)

    GMAIL_SENDER = config.get("gmail", {}).get("from_email", "placeholder@gmail.com")
    GMAIL_PASSWORD = config.get("gmail", {}).get("app_password", "placeholder_password")
    ALERT_THRESHOLD = config.get("alerts", {}).get("threshold", 0.7)

except FileNotFoundError:
    st.error(f"Error: config.yaml not found at {CONFIG_PATH}. Using placeholder credentials.")
    GMAIL_SENDER = "placeholder@gmail.com"
    GMAIL_PASSWORD = "placeholder_password"
    ALERT_THRESHOLD = 0.7
except Exception as e:
    st.error(f"Error loading config.yaml: {e}. Using placeholder credentials.")
    GMAIL_SENDER = "placeholder@gmail.com"
    GMAIL_PASSWORD = "placeholder_password"
    ALERT_THRESHOLD = 0.7

DEFAULT_ALERT_EMAILS = config.get("alerts", {}).get("recipients", {}).get("email", [])

# ------------------ STREAMLIT CONFIG ------------------
st.set_page_config(page_title="Wildfire Risk Dashboard", page_icon="🔥", layout="wide")
DATA_PATH = r"C:\Users\tanvi\OneDrive\Desktop\final prj\wildfire_with_gmail_alerts\wildfire\b8aeb030-140d-43d2-aa29-1a80862e3d62.csv"
MODEL_PATH = r"C:\Users\tanvi\OneDrive\Desktop\final prj\backend_model\wildfire_model.pkl"
HISTORY_FILE = "history.csv"

# ------------------ STYLES ------------------
st.markdown("""
<style>
.stButton > button { padding: 8px 16px; font-weight:600; }
.title-panel { background: rgba(0,0,0,0.55); padding:12px; border-radius:10px; color:#fff; text-align:center;}
.content-panel { background: rgba(0,0,0,0.45); padding:20px; border-radius:10px; color:#fff;}
.alert-high { background: rgba(255,0,0,0.85); color:white; padding:14px; border-radius:8px; text-align:center; font-weight:700;}
</style>
""", unsafe_allow_html=True)

# ------------------ EMAIL ALERT FUNCTION ------------------
def send_email_alert(to_emails, location_name, lat, lon, probability):
    sender_email = GMAIL_SENDER
    sender_password = GMAIL_PASSWORD
    if not to_emails:
        print("❌ Cannot send email: No recipients defined.")
        return False

    if isinstance(to_emails, list):
        to_str = ", ".join(to_emails)
    else:
        to_str = to_emails 

    subject = "🚨 Wildfire Risk Alert!"
    body = f"""
    <h3>⚠️ Wildfire Risk Alert</h3>
    <p><b>Location:</b> {location_name}</p>
    <p><b>Coordinates:</b> {lat:.4f}, {lon:.4f}</p>
    <p><b>Predicted Risk Probability:</b> {probability:.2f}</p>
    <p>Please stay alert and follow local safety advisories.</p>
    """

    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = to_str
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "html"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, to_emails if isinstance(to_emails, list) else [to_emails], msg.as_string())
        print(f"✅ Email alert sent to: {to_str}")
        return True
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        return False

# ------------------ GEOLOCATOR ------------------
if "page" not in st.session_state:
    st.session_state.page = "home"
if "lat" not in st.session_state:
    st.session_state["lat"] = 37.0
if "lon" not in st.session_state:
    st.session_state["lon"] = -120.0
    
geolocator = Nominatim(user_agent="wildfire_dashboard_app")
geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)
reverse = RateLimiter(geolocator.reverse, min_delay_seconds=1)

def get_location_name(lat, lon):
    try:
        loc = reverse((lat, lon), language="en", exactly_one=True, addressdetails=True)
        if loc and loc.raw.get("address"):
            addr = loc.raw["address"]
            city = addr.get("city") or addr.get("town") or addr.get("village") or addr.get("county")
            state = addr.get("state")
            country = addr.get("country")
            name = ", ".join([p for p in [city, state, country] if p])
            return name if name else loc.address
    except Exception:
        pass
    return "Unknown location"

# ------------------ HISTORY ------------------
def save_history(lat, lon, temp, hum, wind, veg, probability, risk_label):
    entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "location": get_location_name(lat, lon),   # ✅ FIXED
        "latitude": lat,
        "longitude": lon,
        "temperature": temp,
        "humidity": hum,
        "wind_speed": wind,
        "vegetation_index": veg,
        "probability": round(float(probability), 3),
        "risk_label": risk_label
    }

    df = pd.read_csv(HISTORY_FILE) if os.path.exists(HISTORY_FILE) else pd.DataFrame()
    df = pd.concat([df, pd.DataFrame([entry])], ignore_index=True)
    df.to_csv(HISTORY_FILE, index=False)

def load_history():
    return pd.read_csv(HISTORY_FILE) if os.path.exists(HISTORY_FILE) else pd.DataFrame()

# ------------------ BACKGROUND ------------------
def set_bg(image_file):
    if not os.path.exists(image_file):
        st.markdown(f"""<style>.stApp {{background: #0E1117;}}</style>""", unsafe_allow_html=True)
        return
    with open(image_file, "rb") as f:
        encoded = base64.b64encode(f.read()).decode()
    st.markdown(f"""
        <style>
        .stApp {{
          background-image: url("data:image/png;base64,{encoded}");
          background-size: cover;
          background-attachment: fixed;
        }}
        </style>
    """, unsafe_allow_html=True)

# ------------------ MODEL LOAD ------------------
@st.cache_resource
def load_artifact(path=MODEL_PATH):
    if not os.path.exists(path):
        return None
    try:
        return joblib.load(path)
    except Exception as e:
        st.error(f"Failed to load model artifact: {e}")
        return None

artifact = load_artifact()
spatial_tree = None
spatial_points = None
rf_model = None
rf_feature_cols = None

if artifact and isinstance(artifact, dict):
    if artifact.get("type") == "spatial":
        pts = np.asarray(artifact.get("points"))
        if pts.shape[0] > 0:
            spatial_points = pts
            spatial_tree = KDTree(np.radians(pts), metric='euclidean') 
    elif artifact.get("type") == "rf":
        rf_model = artifact.get("model")
        rf_feature_cols = artifact.get("feature_cols", None)

def haversine_distance_km(lat1, lon1, lat2, lon2):
    R = 6371.0088
    phi1, phi2 = radians(lat1), radians(lat2)
    dphi = radians(lat2 - lat1)
    dlambda = radians(lon2 - lon1)
    from math import sin, cos, atan2, sqrt
    a = sin(dphi/2)**2 + cos(phi1)*cos(phi2)*sin(dlambda/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    return R * c

def distance_to_nearest_history(lat, lon):
    if spatial_tree is None or spatial_points is None:
        return np.inf
    dist_rad, _ = spatial_tree.query(np.radians([[lat, lon]]), k=1)
    R = 6371.0088
    return float(dist_rad[0][0] * R)

def distance_based_probability(dist_km, scale_km=10.0):
    if np.isinf(dist_km):
        return 0.05
    prob = np.exp(-dist_km / scale_km)
    prob = 0.05 + (0.94 * prob) 
    return float(np.clip(prob, 0.0, 0.99))

def predict_probability(lat, lon, temp=None, hum=None, wind=None, veg=None):
    if rf_model is not None and rf_feature_cols is not None:
        row = {}
        for f in rf_feature_cols:
            key = f.lower()
            if "temp" in key:
                row[f] = temp if temp is not None else 30.0
            elif "humid" in key:
                row[f] = hum if hum is not None else 30.0
            elif "wind" in key:
                row[f] = wind if wind is not None else 5.0
            elif "veg" in key:
                row[f] = veg if veg is not None else 0.5
            elif key in ("latitude","lat"):
                row[f] = lat
            elif key in ("longitude","lon","lng","long"):
                row[f] = lon
            else:
                row[f] = 0.0
        X = pd.DataFrame([row])[rf_feature_cols]
        try:
            prob = float(rf_model.predict_proba(X)[0][1])
            dkm = distance_to_nearest_history(lat, lon)
            if dkm < 10:
                prob = max(prob, distance_based_probability(dkm, 6.0))
            return float(np.clip(prob, 0.0, 0.999))
        except Exception as e:
            dkm = distance_to_nearest_history(lat, lon)
            return distance_based_probability(dkm)
    else:
        dkm = distance_to_nearest_history(lat, lon)
        return distance_based_probability(dkm)

# ------------------ SIDEBAR ------------------
st.sidebar.markdown("## 🔥 Wildfire Dashboard")
def sidebar_button(label, key, page_name):
    if st.sidebar.button(label, key=key, use_container_width=True):
        st.session_state.page = page_name

sidebar_button("🏠 Home", "home", "home")
sidebar_button("🌍 Predict Risk", "predict", "predict")
sidebar_button("🗺 Risk Map", "map", "map")
sidebar_button("📈 History", "history", "history")

# ------------------ PAGES ------------------
if st.session_state.page == "home":
    set_bg("background1.png")
    st.markdown("<div class='title-panel'><h1>🔥 Wildfire Risk Prediction Dashboard</h1></div>", unsafe_allow_html=True)
    st.markdown("""
        <div class="content-panel">
        <p>This dashboard uses a trained model and past wildfire data to predict risk.</p>
        <ul>
            <li>Predict Risk — Enter coordinates and get prediction.</li>
            <li>Risk Map — Visualize high-risk areas.</li>
            <li>History — View and download past predictions.</li>
        </ul>
        </div>
    """, unsafe_allow_html=True)

elif st.session_state.page == "predict":
    st.markdown("## 🌍 Predict Wildfire Risk")

    # --- NEW: Use clicked coordinates as default, otherwise use previous session values ---
    default_lat = st.session_state.get("clicked_lat", st.session_state.get("lat", 37.0))
    default_lon = st.session_state.get("clicked_lon", st.session_state.get("lon", -120.0))
    
    lat = st.number_input("Latitude", -90.0, 90.0, default_lat, format="%.6f", key="input_lat")
    lon = st.number_input("Longitude", -180.0, 180.0, default_lon, format="%.6f", key="input_lon")
    
    if "clicked_lat" in st.session_state:
        del st.session_state["clicked_lat"]
    if "clicked_lon" in st.session_state:
        del st.session_state["clicked_lon"]

    temp = st.number_input("Temperature (°C)", -50.0, 60.0, 30.0)
    hum = st.number_input("Humidity (%)", 0.0, 100.0, 30.0)
    wind = st.number_input("Wind Speed (km/h)", 0.0, 200.0, 5.0)
    veg = st.number_input("Vegetation Index (0–1)", 0.0, 1.0, 0.5)

    loc_name = get_location_name(lat, lon)
    st.markdown(f"**📍 Location name:** {loc_name}")

    if st.button("🔮 Predict Risk"):
        
        st.session_state["lat"] = lat
        st.session_state["lon"] = lon
        
        prob = predict_probability(lat, lon, temp, hum, wind, veg)
        risk_label = "🔥 HIGH RISK" if prob >= ALERT_THRESHOLD else "🟢 LOW / MODERATE RISK"
        st.success(f"Prediction: {risk_label} | Probability: {prob:.2f}")

        if prob >= ALERT_THRESHOLD:
            st.markdown("<div class='alert-high'>🚨 ALERT: High Wildfire Risk Detected!</div>", unsafe_allow_html=True)
            alert_sent = send_email_alert(DEFAULT_ALERT_EMAILS, loc_name, lat, lon, prob)
            if alert_sent:
                st.info(f"📩 Email alert sent to: {', '.join(DEFAULT_ALERT_EMAILS)}")
            else:
                st.warning("⚠️ Failed to send email alert. Check console for details.")

        save_history(lat, lon, temp, hum, wind, veg, prob, risk_label)

# ------------------ MAP ------------------
elif st.session_state.page == "map":
    st.markdown("## 🗺 Risk Map")

    lat0 = st.session_state.get("lat", 37.0)
    lon0 = st.session_state.get("lon", -120.0)

    place_query = st.text_input("🔎 Search location (city, landmark, address)")

    if st.button("Search") and place_query.strip():
        try:
            searched = geocode(place_query)
            if searched:
                lat0, lon0 = searched.latitude, searched.longitude
                st.session_state["lat"] = lat0
                st.session_state["lon"] = lon0
                st.success(f"✅ Found: {searched.address}")
            else:
                st.error("Location not found.")
        except Exception as e:
            st.error(f"Geocoding error: {e}")

    loc_name = get_location_name(lat0, lon0)

    wildfire_map = folium.Map(location=[lat0, lon0], zoom_start=9)

    MAX_DISTANCE_KM = 200
    if spatial_points is not None and len(spatial_points) > 0:
        filtered_points = []
        for r_lat, r_lon in spatial_points:
            dist = haversine_distance_km(lat0, lon0, r_lat, r_lon)
            if dist <= MAX_DISTANCE_KM:
                filtered_points.append((r_lat, r_lon))

        heat_data = [[p[0], p[1], 1.0] for p in filtered_points]

        if heat_data:
            HeatMap(heat_data, radius=15).add_to(wildfire_map)

    prob_center = predict_probability(lat0, lon0)
    marker_color = "red" if prob_center >= ALERT_THRESHOLD else "blue"
    popup_text = (f"<b>{loc_name}</b><br>"
                  f"Lat: {lat0:.6f}, Lon: {lon0:.6f}<br>"
                  f"Predicted risk: {prob_center:.2f}")

    folium.Marker(
        location=[lat0, lon0],
        popup=popup_text,
        icon=folium.Icon(color=marker_color, icon="star", prefix='fa')
    ).add_to(wildfire_map)

    map_data = st_folium(wildfire_map, width=900, height=550)

    if map_data and map_data.get("last_clicked"):
        clicked = map_data["last_clicked"]
        clat, clon = clicked["lat"], clicked["lng"]

        st.session_state["lat"] = clat
        st.session_state["lon"] = clon
        st.session_state["clicked_lat"] = clat
        st.session_state["clicked_lon"] = clon

        st.info(f"📍 Clicked → {clat:.6f}, {clon:.6f}")

# ------------------ HISTORY ------------------
elif st.session_state.page == "history":
    st.markdown("## 📈 Prediction History")
    history = load_history()

    if not history.empty:
        # ✅ ENSURE location column exists
        if "location" not in history.columns:
            history["location"] = "Unknown"

        # ✅ Reorder preferred columns
        preferred_cols = [
            "timestamp", "location", "latitude", "longitude",
            "temperature", "humidity", "wind_speed",
            "vegetation_index", "probability", "risk_label"
        ]
        cols_present = [c for c in preferred_cols if c in history.columns]
        history = history[cols_present]

        st.dataframe(history.sort_values(by="timestamp", ascending=False))

        @st.cache_data
        def convert_df_to_csv(df):
            return df.to_csv(index=False).encode('utf-8')

        csv = convert_df_to_csv(history)
        st.download_button(
            "📥 Download History CSV", 
            csv, 
            "wildfire_history.csv", 
            "text/csv", 
            key='download-csv'
        )
    else:
        st.info("⚠️ No predictions yet.")

# ------------------ FOOTER ------------------
if artifact is None:
    st.sidebar.warning("No backend model artifact found. Run train_model.py to create one.")
else:
    mtype = artifact.get("type") if isinstance(artifact, dict) else "unknown"
    st.sidebar.markdown(f"**Model artifact:** {mtype}")
