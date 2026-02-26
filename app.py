import streamlit as st
import pandas as pd
import tempfile
import os
import hashlib
from datetime import date
from collections import Counter
from PIL import Image

from utils.change_detection import detect_deforestation
from utils.yolo_detect import detect_intrusion
from utils.satellite_fetch import get_satellite_image


# =====================================================
# SESSION STATE (CLOUD SAFE)
# =====================================================
if "intrusion" not in st.session_state:
    st.session_state.intrusion = False

if "person_count" not in st.session_state:
    st.session_state.person_count = 0

if "last_intrusion_image" not in st.session_state:
    st.session_state.last_intrusion_image = None

if "alert_active" not in st.session_state:
    st.session_state.alert_active = False


# =====================================================
# PAGE CONFIG
# =====================================================
st.set_page_config(page_title="ForestGuard AI", layout="wide")
st.markdown("""
<style>
.block-container {
    padding-top: 1rem;
}
</style>
""", unsafe_allow_html=True)
st.title("🌳 ForestGuard AI – Intelligent Forest Threat Monitoring")


# =====================================================
# GLOBAL ALERT POPUP
# =====================================================
if st.session_state.alert_active:
    st.markdown("""
    <style>
    .alert-overlay {
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        background-color: rgba(0, 0, 0, 0.85);
        z-index: 99999;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-direction: column;
        color: white;
        text-align: center;
    }

    .alert-box {
        background-color: red;
        padding: 40px;
        border-radius: 20px;
        font-size: 32px;
        font-weight: bold;
        box-shadow: 0px 0px 40px red;
        animation: pulse 1s infinite;
    }

    @keyframes pulse {
        50% { transform: scale(1.05); }
    }
    </style>

    <div class="alert-overlay">
        <div class="alert-box">
            🚨 CRITICAL FOREST THREAT DETECTED 🚨
            <br><br>
            Immediate Action Required
        </div>
    </div>
    """, unsafe_allow_html=True)
    


# =====================================================
# FOREST LOCATIONS
# =====================================================
forest_coords = {
    "Sathyamangalam Tiger Reserve": [77.0, 11.4, 77.5, 11.9],
    "Mudumalai Tiger Reserve": [76.3, 11.5, 76.7, 11.7],
    "Anamalai Tiger Reserve": [76.8, 10.2, 77.2, 10.5],
    "KMTR": [77.1, 8.4, 77.5, 8.8]
}

location = st.selectbox("📍 Select Forest Region", list(forest_coords.keys()))


# =====================================================
# DATE RANGE
# =====================================================
col1, col2 = st.columns(2)
start_date = col1.date_input("Start Date", date(2024, 1, 1))
end_date = col2.date_input("End Date", date.today())


# =====================================================
# DASHBOARD METRICS
# =====================================================
colA, colB, colC = st.columns(3)
colA.metric("Region", location)
colB.metric("Intrusions", st.session_state.person_count)
colC.metric("Monitoring Window", f"{(end_date - start_date).days} days")


# =====================================================
# MAP
# =====================================================
map_data = pd.DataFrame({
    "lat": [forest_coords[location][1]],
    "lon": [forest_coords[location][0]]
})
st.map(map_data, zoom=8)


# =====================================================
# SATELLITE DEFORESTATION
# =====================================================
st.subheader("🛰 Satellite Forest Change Detection")

if st.button("Analyze Forest Change"):

    before_img = get_satellite_image(forest_coords[location], str(start_date), str(start_date))
    after_img = get_satellite_image(forest_coords[location], str(end_date), str(end_date))

    col1, col2 = st.columns(2)
    col1.image(before_img, caption="Start")
    col2.image(after_img, caption="End")

    tmp_before = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    tmp_after = tempfile.NamedTemporaryFile(delete=False, suffix=".png")

    Image.fromarray(before_img).save(tmp_before.name)
    Image.fromarray(after_img).save(tmp_after.name)

    result, percent = detect_deforestation(tmp_before.name, tmp_after.name)

    st.image(result, use_column_width=True)
    st.metric("Forest Loss", f"{percent:.2f}%")

    risk_score = percent

    if st.session_state.intrusion:
        risk_score += 30

    st.metric("Threat Score", f"{risk_score:.2f}%")

    if risk_score >= 50:
        st.session_state.alert_active = True

    os.remove(tmp_before.name)
    os.remove(tmp_after.name)


# =====================================================
# CAMERA TRAP – INTRUSION DETECTION
# =====================================================
st.subheader("🚨 Camera Trap Monitoring")

img = st.file_uploader("Upload Camera Trap Image", type=["jpg", "png", "jpeg"])

if img:

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
    tmp.write(img.getbuffer())
    tmp.close()

    image_bytes = img.getvalue()
    image_hash = hashlib.md5(image_bytes).hexdigest()

    result, intrusion, detected_classes = detect_intrusion(tmp.name)

    st.image(result, use_column_width=True)

    # store globally
    st.session_state.intrusion = intrusion

    # -------- CLASS SUMMARY --------
    class_counts = Counter(detected_classes)

    st.write("### Detection Summary")

    for cls, count in class_counts.items():
        st.write(f"**{cls.capitalize()} × {count}**")

    # -------- INTRUSION LOGIC --------
    if intrusion:

        if st.session_state.last_intrusion_image != image_hash:
            st.session_state.person_count += class_counts.get("person", 0)
            st.session_state.last_intrusion_image = image_hash

        st.error("🚨 Human detected – Possible poaching activity")
        st.session_state.alert_active = True

    else:
        st.success("🟢 Wildlife detected – No intrusion")

    os.remove(tmp.name)


# =====================================================
# RESET BUTTON
# =====================================================
if st.button("🔄 Reset Alerts"):
    st.session_state.alert_active = False
