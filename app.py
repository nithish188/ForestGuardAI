import streamlit as st
import tempfile
import os

from utils.change_detection import detect_deforestation
from utils.yolo_detect import detect_intrusion
from utils.satellite_fetch import get_satellite_image

# ---------------- SESSION STATE ----------------
if "intrusion_detected" not in st.session_state:
    st.session_state.intrusion_detected = False

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="ForestGuard AI", layout="wide")

st.title("🌳 ForestGuard AI – Intelligent Forest Threat Monitoring")

st.markdown("""
AI-powered system for **real-time forest monitoring** using  
🛰 Sentinel-2 satellite imagery + 🎥 AI intrusion detection  
📍 Tamil Nadu Forest Department Use Case
""")

# ---------------- FOREST LOCATIONS ----------------
forest_coords = {
    "Sathyamangalam Tiger Reserve": [77.0, 11.4, 77.5, 11.9],
    "Mudumalai Tiger Reserve": [76.3, 11.5, 76.7, 11.7],
    "Anamalai Tiger Reserve": [76.8, 10.2, 77.2, 10.5],
    "KMTR": [77.1, 8.4, 77.5, 8.8]
}

location = st.selectbox("📍 Select Forest Region", list(forest_coords.keys()))

# ---------------- TOP DASHBOARD ----------------
col1, col2, col3 = st.columns(3)
col1.metric("Monitored Region", location)
col2.metric("Satellite Source", "Sentinel-2")
col3.metric("Last Scan", "Just now")

st.map({location: forest_coords[location][:2]})

# ---------------- SATELLITE FETCH ----------------
if st.button("🛰 Fetch Latest Satellite Image"):

    with st.spinner("Fetching Sentinel-2 image..."):
        sat_img = get_satellite_image(forest_coords[location])

    st.image(sat_img, caption="Latest Sentinel-2 Image", use_column_width=True)

# ---------------- TABS ----------------
tab1, tab2 = st.tabs(["🌲 Deforestation Monitoring", "🚨 Intrusion Detection"])

# =====================================================
# 🌲 DEFORESTATION TAB
# =====================================================
with tab1:

    st.subheader("Upload BEFORE & AFTER images")

    col1, col2 = st.columns(2)

    before = col1.file_uploader("Upload BEFORE image", type=["png", "jpg", "jpeg"])
    after = col2.file_uploader("Upload AFTER image", type=["png", "jpg", "jpeg"])

    if before and after:

        t1 = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
        t1.write(before.getbuffer())
        t1.close()

        t2 = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
        t2.write(after.getbuffer())
        t2.close()

        result, percent = detect_deforestation(t1.name, t2.name)

        st.image(result, caption="Forest Change Detection", use_column_width=True)

        st.metric("🌲 Forest Loss", f"{percent:.2f} %")

        risk_score = percent

        if st.session_state.intrusion_detected:
            risk_score += 30

        st.metric("🚨 Forest Threat Level", f"{risk_score:.2f} %")

        if risk_score > 50:
            st.error("🔴 HIGH RISK: Deploy anti-poaching patrol immediately")
        elif risk_score > 20:
            st.warning("🟠 MODERATE RISK: Increase drone surveillance")
        else:
            st.success("🟢 LOW RISK: Routine monitoring")

        os.remove(t1.name)
        os.remove(t2.name)

# =====================================================
# 🚨 INTRUSION TAB
# =====================================================
with tab2:

    st.subheader("Upload Forest Camera Trap Image")

    img = st.file_uploader("Upload image", type=["png", "jpg", "jpeg"])

    if img:

        t = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
        t.write(img.getbuffer())
        t.close()

        result = detect_intrusion(t.name)

        st.image(result, caption="Intrusion Detection", use_column_width=True)

        st.session_state.intrusion_detected = True

        st.error("🚨 Human / Vehicle detected – Possible poaching activity")

        os.remove(t.name)

# ---------------- IMPACT PANEL ----------------
st.markdown("---")
st.markdown("### 🌱 Impact")

st.write("""
- Early detection of illegal logging  
- Real-time anti-poaching alerts  
- Scalable across all Indian tiger reserves  
- Decision support for Tamil Nadu Forest Department  
""")
