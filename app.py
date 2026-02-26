import streamlit as st
import tempfile
import os
from utils.change_detection import detect_deforestation
from utils.yolo_detect import detect_intrusion

# ---------------- SESSION STATE ----------------
if "intrusion_detected" not in st.session_state:
    st.session_state.intrusion_detected = False

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="ForestGuard AI", layout="wide")

st.title("🌳 ForestGuard AI")

st.markdown("""
### 🛰 AI-Powered Forest & Wildlife Monitoring System  
Using Satellite Imagery & Real-Time Camera Trap Detection  
**Region: Tamil Nadu, India**
""")

# ---------------- LOCATION SELECTOR ----------------
location = st.selectbox(
    "📍 Select Forest Region",
    [
        "Sathyamangalam Tiger Reserve",
        "Mudumalai Tiger Reserve",
        "Anamalai Tiger Reserve",
        "Kalakkad Mundanthurai Tiger Reserve (KMTR)"
    ]
)

st.info(f"Monitoring Region: {location}")

# ---------------- TABS ----------------
tab1, tab2 = st.tabs(["🌲 Deforestation Monitoring", "🚨 Intrusion Detection"])


# =========================================================
# 🌲 TAB 1 — DEFORESTATION
# =========================================================
with tab1:

    st.subheader("Upload Satellite Images")

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

        with st.spinner("Analyzing forest change..."):
            result, percent = detect_deforestation(t1.name, t2.name)

        st.image(result, caption="Detected Forest Change", use_column_width=True)

        st.metric("🌲 Forest Loss", f"{percent:.2f} %")

        # ---------------- THREAT SCORE CALCULATION ----------------
        risk_score = percent

        if st.session_state.intrusion_detected:
            risk_score += 30

        st.metric("🚨 Forest Threat Level", f"{risk_score:.2f} %")

        # ---------------- ALERT SYSTEM ----------------
        if risk_score > 50:
            st.error("🔴 HIGH RISK: Immediate action required!")
        elif risk_score > 20:
            st.warning("🟠 MODERATE RISK: Patrol recommended")
        else:
            st.success("🟢 LOW RISK")

        os.remove(t1.name)
        os.remove(t2.name)


# =========================================================
# 🚨 TAB 2 — INTRUSION DETECTION
# =========================================================
with tab2:

    st.subheader("Upload Forest Camera Image")

    img = st.file_uploader("Upload Image", type=["png", "jpg", "jpeg"])

    if img:

        t = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
        t.write(img.getbuffer())
        t.close()

        with st.spinner("Running AI intrusion detection..."):
            result = detect_intrusion(t.name)

        st.image(result, caption="Detection Result", use_column_width=True)

        # 🔥 SET INTRUSION FLAG
        st.session_state.intrusion_detected = True

        st.error("🚨 Human/Vehicle detected → Possible Poaching Activity!")

        os.remove(t.name)


# ---------------- FOOTER ----------------
st.markdown("---")
st.markdown("Built for Hackathon Demo | Data: Sentinel-2 | Model: YOLOv8")