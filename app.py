import streamlit as st
import tempfile
import os
import pandas as pd
import hashlib
from collections import Counter
from datetime import date
from PIL import Image
from utils.change_detection import detect_deforestation
from utils.yolo_detect import detect_intrusion
from utils.satellite_fetch import get_satellite_image


# ---------------- SESSION STATE INIT ----------------
if "intrusion_detected" not in st.session_state:
    st.session_state.intrusion_detected = False

if "alert_active" not in st.session_state:
    st.session_state.alert_active = False
    
if "person_count" not in st.session_state:
    st.session_state.person_count = 0
    
if "last_intrusion_image" not in st.session_state:
    st.session_state.last_intrusion_image = None

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="ForestGuard AI", layout="wide")

st.title("🌳 ForestGuard AI – Intelligent Forest Threat Monitoring")

if st.session_state.alert_active:
    st.markdown(
        """
        <style>
        @keyframes blink {
            50% {opacity: 0;}
        }
        .alert-box {
            position: fixed;
            top: 20px;
            right: 20px;
            background-color: red;
            color: white;
            padding: 20px;
            font-size: 22px;
            font-weight: bold;
            border-radius: 12px;
            animation: blink 1s infinite;
            z-index: 9999;
        }
        </style>
        <div class="alert-box">
        🚨 CRITICAL FOREST THREAT DETECTED
        </div>
        """,
        unsafe_allow_html=True
    )

    st.audio("https://actions.google.com/sounds/v1/alarms/alarm_clock.ogg")

st.success("🟢 System Status: Monitoring Active | Satellite Sync Enabled")

st.markdown("""
AI-powered forest monitoring using  
🛰 Sentinel-2 satellite imagery + 🎥 AI intrusion detection  
📍 Tamil Nadu Forest Monitoring Dashboard
""")


# ---------------- FOREST LOCATIONS ----------------
forest_coords = {
    "Sathyamangalam Tiger Reserve": [77.0, 11.4, 77.5, 11.9],
    "Mudumalai Tiger Reserve": [76.3, 11.5, 76.7, 11.7],
    "Anamalai Tiger Reserve": [76.8, 10.2, 77.2, 10.5],
    "Kalakkad Mundanthurai Tiger Reserve (KMTR)": [77.1, 8.4, 77.5, 8.8]
}

location = st.selectbox("📍 Select Forest Region", list(forest_coords.keys()))


# ---------------- DATE RANGE (DAYS-BASED MONITORING) ----------------
st.markdown("## 📅 Monitoring Time Window")

col1, col2 = st.columns(2)

start_date = col1.date_input(
    "Start Date",
    value=date(2024, 1, 1)
)

end_date = col2.date_input(
    "End Date",
    value=date.today()
)

if start_date >= end_date:
    st.error("End date must be after start date.")


# ---------------- DASHBOARD METRICS ----------------
colA, colB, colC = st.columns(3)
colA.metric("Monitored Region", location)
colB.metric("Satellite Source", "Sentinel-2 L2A")
colC.metric("Monitoring Window", f"{(end_date - start_date).days} days")


# ---------------- MAP ----------------
map_data = pd.DataFrame({
    "lat": [forest_coords[location][1]],
    "lon": [forest_coords[location][0]]
})

st.map(map_data, zoom=8)


# =====================================================
# 🛰 SATELLITE MONITORING MODE
# =====================================================
st.markdown("## 🛰 Automated Satellite Monitoring")

if st.button("Analyze Forest Change (Satellite)"):

    with st.spinner("Fetching satellite imagery for selected timeline..."):

        before_img = get_satellite_image(
            forest_coords[location],
            str(start_date),
            str(start_date)
        )

        after_img = get_satellite_image(
            forest_coords[location],
            str(end_date),
            str(end_date)
        )

    st.subheader("Satellite Images")

    col1, col2 = st.columns(2)
    col1.image(before_img, caption="Start Date Image", use_column_width=True)
    col2.image(after_img, caption="End Date Image", use_column_width=True)

    # Save temp for change detection
    tmp_before = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    tmp_after = tempfile.NamedTemporaryFile(delete=False, suffix=".png")

    Image.fromarray(before_img).save(tmp_before.name)
    Image.fromarray(after_img).save(tmp_after.name)

    tmp_before.close()
    tmp_after.close()

    result, percent = detect_deforestation(tmp_before.name, tmp_after.name)

    st.subheader("🌲 Forest Change Detection")
    st.image(result, use_column_width=True)

    st.metric("Forest Loss Detected", f"{percent:.2f}%")

    risk_score = percent

    if st.session_state.intrusion_detected:
        risk_score += 30

    st.metric("🚨 Forest Threat Level", f"{risk_score:.2f}%")
    
    ALERT_THRESHOLD = 50

    if risk_score >= ALERT_THRESHOLD:
        st.session_state.alert_active = True
    else:
        st.session_state.alert_active = False

    if risk_score > 50:
        st.error("🔴 HIGH RISK: Immediate patrol deployment recommended")
    elif risk_score > 20:
        st.warning("🟠 MODERATE RISK: Increase surveillance")
    else:
        st.success("🟢 LOW RISK: Routine monitoring sufficient")

    os.remove(tmp_before.name)
    os.remove(tmp_after.name)


# =====================================================
# 🎥 INTRUSION DETECTION
# =====================================================
st.markdown("## 🚨 Camera Trap Intrusion Monitoring")

img = st.file_uploader("Upload Camera Trap Image", type=["png", "jpg", "jpeg"])

if img:

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
    tmp.write(img.getbuffer())
    tmp.close()

    # create unique ID for the uploaded image
    image_bytes = img.getvalue()
    image_hash = hashlib.md5(image_bytes).hexdigest()

    result, intrusion, detected_classes = detect_intrusion(tmp.name)

    st.image(result, use_column_width=True)
    
    class_counts = Counter(detected_classes)

    st.write("### Detection Summary")

    for cls, count in class_counts.items():
        st.write(f"**{cls.capitalize()} × {count}**")

if intrusion:

    st.session_state.alert_active = True
    # only count if this is a NEW image
    if st.session_state.last_intrusion_image != image_hash:
        st.session_state.person_count += detected_classes.count("person")
        st.session_state.last_intrusion_image = image_hash

    st.error("🚨 Human / Vehicle detected – Possible poaching activity")

else:
    st.success("🟢 Wildlife detected – No intrusion")

    os.remove(tmp.name)


# =====================================================
# 🌱 IMPACT SECTION
# =====================================================
st.markdown("---")
st.markdown("### 🌱 System Impact")

st.write("""
- Near-real-time forest monitoring  
- Date-based operational analysis (days, not years)  
- Integrated satellite + ground surveillance  
- Scalable across all protected forest reserves  
""")
