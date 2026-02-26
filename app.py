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
# PAGE CONFIG
# =====================================================
st.set_page_config(page_title="ForestGuard AI", layout="wide")

st.markdown("""
<style>
.block-container {padding-top: 1rem;}
</style>
""", unsafe_allow_html=True)


# =====================================================
# SESSION STATE
# =====================================================
for key, val in {
    "intrusion": False,
    "alert_active": False,
    "person_count": 0,
    "last_intrusion_image": None,
}.items():
    if key not in st.session_state:
        st.session_state[key] = val


# =====================================================
# TITLE
# =====================================================
st.title("🌳 ForestGuard AI – Intelligent Forest Threat Monitoring")

# GLOBAL ALERT PLACEHOLDER (TOP POSITION CONTROL)
global_alert = st.empty()


# =====================================================
# FULL SCREEN CRITICAL ALERT
# =====================================================
if st.session_state.alert_active:
    st.components.v1.html("""
    <div style="
        position:fixed;
        top:0;
        left:0;
        width:100vw;
        height:100vh;
        background:rgba(0,0,0,0.92);
        display:flex;
        align-items:center;
        justify-content:center;
        z-index:999999;">
        <div style="
            background:red;
            padding:60px;
            border-radius:20px;
            font-size:42px;
            font-weight:bold;
            color:white;
            text-align:center;
            box-shadow:0 0 80px red;">
            🚨 CRITICAL FOREST THREAT 🚨<br><br>
            Immediate Ranger Deployment Required
        </div>
    </div>
    """, height=0, width=0)


# =====================================================
# FOREST SELECT
# =====================================================
forest_coords = {
    "Sathyamangalam Tiger Reserve": [77.0, 11.4, 77.5, 11.9],
    "Mudumalai Tiger Reserve": [76.3, 11.5, 76.7, 11.7],
    "Anamalai Tiger Reserve": [76.8, 10.2, 77.2, 10.5],
    "KMTR": [77.1, 8.4, 77.5, 8.8]
}

location = st.selectbox("📍 Select Forest Region", list(forest_coords.keys()))

col1, col2 = st.columns(2)
start_date = col1.date_input("Start Date", date(2024, 1, 1))
end_date = col2.date_input("End Date", date.today())


# =====================================================
# DASHBOARD METRICS
# =====================================================
c1, c2, c3 = st.columns(3)
c1.metric("Region", location)
c2.metric("Intrusions", st.session_state.person_count)
c3.metric("Monitoring Window", f"{(end_date - start_date).days} days")


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

    before = get_satellite_image(forest_coords[location], str(start_date), str(start_date))
    after = get_satellite_image(forest_coords[location], str(end_date), str(end_date))

    col1, col2 = st.columns(2)
    col1.image(before, caption="Start")
    col2.image(after, caption="End")

    tmp1 = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    tmp2 = tempfile.NamedTemporaryFile(delete=False, suffix=".png")

    Image.fromarray(before).save(tmp1.name)
    Image.fromarray(after).save(tmp2.name)

    result, percent = detect_deforestation(tmp1.name, tmp2.name)

    st.image(result)
    st.metric("Forest Loss", f"{percent:.2f}%")

    risk_score = percent + (30 if st.session_state.intrusion else 0)
    st.metric("Threat Score", f"{risk_score:.2f}%")

    if risk_score >= 50:
        st.session_state.alert_active = True
        global_alert.error("🚨 High deforestation detected!")

    os.remove(tmp1.name)
    os.remove(tmp2.name)


# =====================================================
# CAMERA TRAP
# =====================================================
st.subheader("🚨 Camera Trap Monitoring")

img = st.file_uploader("Upload Camera Trap Image", type=["jpg", "png", "jpeg"])

if img:

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
    tmp.write(img.getbuffer())
    tmp.close()

    image_hash = hashlib.md5(img.getvalue()).hexdigest()

    result, intrusion, detected = detect_intrusion(tmp.name)

    st.image(result)

    st.session_state.intrusion = intrusion

    counts = Counter(detected)

    st.write("### Detection Summary")
    for k, v in counts.items():
        st.write(f"**{k.capitalize()} × {v}**")

    if intrusion:

        # FLOATING ALERT (TOP RIGHT)
        st.markdown("""
        <div style="
        position:fixed;
        top:80px;
        right:20px;
        background:red;
        color:white;
        padding:15px 25px;
        border-radius:10px;
        z-index:9999;
        font-weight:bold;">
        🚨 Human detected – Possible poaching activity
        </div>
        """, unsafe_allow_html=True)

        if st.session_state.last_intrusion_image != image_hash:
            st.session_state.person_count += counts.get("person", 0)
            st.session_state.last_intrusion_image = image_hash

        global_alert.error("🚨 Intrusion detected in protected zone!")
        st.session_state.alert_active = True

    else:
        global_alert.success("🟢 Wildlife movement detected – Area secure")

    os.remove(tmp.name)


# =====================================================
# ACKNOWLEDGE ALERT
# =====================================================
if st.session_state.alert_active:
    if st.button("✅ Acknowledge Alert"):
        st.session_state.alert_active = False
        st.rerun()
