import os

import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()
BACKEND_URL = os.environ.get("BACKEND_URL") or st.secrets.get("BACKEND_URL", "http://localhost:8000")

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"


def search_india_places(query: str):
    """Live search across every Indian city/town/village via OpenStreetMap's
    free Nominatim geocoder. Returns a list of {label, lat, lng} dicts."""
    if not query or len(query.strip()) < 2:
        return []
    try:
        resp = requests.get(
            NOMINATIM_URL,
            params={
                "q": query,
                "format": "json",
                "countrycodes": "in",
                "limit": 6,
                "addressdetails": 1,
            },
            headers={"User-Agent": "CivicBinAI/1.0 (hackathon demo)"},
            timeout=8,
        )
        resp.raise_for_status()
        results = []
        for item in resp.json():
            addr = item.get("address", {})
            place = (
                addr.get("city") or addr.get("town") or addr.get("village")
                or addr.get("county") or item.get("display_name", "").split(",")[0]
            )
            state = addr.get("state", "")
            label = f"{place}, {state}" if state else place
            results.append({"label": label, "lat": float(item["lat"]), "lng": float(item["lon"])})
        return results
    except requests.RequestException:
        return []


st.set_page_config(page_title="CivicBin AI - Report a Bin", page_icon=None)

st.markdown("""
<style>
.block-container {padding-top: 2rem; padding-bottom: 3rem; max-width: 720px;}
.cb-header {
    background: linear-gradient(135deg, #0F4C43 0%, #1B6E5C 100%);
    padding: 26px 28px; border-radius: 12px; margin-bottom: 22px;
}
.cb-header h1 {color: #FFFFFF; font-size: 24px; margin: 0; font-weight: 700;}
.cb-header p {color: #CFE8E1; font-size: 14px; margin: 6px 0 0 0;}
.cb-result-card {
    background: #FFFFFF; border-left: 4px solid #1B6E5C; border-radius: 8px;
    padding: 16px 18px; margin-top: 16px; box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}
div.stButton > button, div.stFormSubmitButton > button {
    background-color: #1B6E5C; color: white; border: none; border-radius: 8px;
    padding: 10px 22px; font-weight: 600; width: 100%;
}
div.stButton > button:hover, div.stFormSubmitButton > button:hover {background-color: #0F4C43; color: white;}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="cb-header">
  <h1>Report an Overflowing Bin</h1>
  <p>Submit a photo and location — AI verifies severity and a collection crew is routed automatically.</p>
</div>
""", unsafe_allow_html=True)

query = st.text_input("Search for your city or town in India", placeholder="e.g. Coimbatore, Salem, Warangal...")
matches = search_india_places(query)

if query and not matches:
    st.warning("No matching place found — try a different spelling, or enter coordinates manually below.")

selected_label = None
default_lat, default_lng = 20.5937, 78.9629  # center of India, fallback
if matches:
    selected_label = st.selectbox("Select the exact place", [m["label"] for m in matches])
    chosen = next(m for m in matches if m["label"] == selected_label)
    default_lat, default_lng = chosen["lat"], chosen["lng"]

with st.form("report_form"):
    photo = st.camera_input("Take a photo of the bin") or st.file_uploader(
        "...or upload a photo", type=["jpg", "jpeg", "png"]
    )
    col1, col2 = st.columns(2)
    lat = col1.number_input("Latitude", value=default_lat, format="%.6f")
    lng = col2.number_input("Longitude", value=default_lng, format="%.6f")
    submitted = st.form_submit_button("Submit report")

if submitted:
    if not photo:
        st.error("Please add a photo first.")
    else:
        with st.spinner("Analyzing photo with Gemini..."):
            files = {"photo": (photo.name if hasattr(photo, "name") else "photo.jpg", photo.getvalue())}
            data = {"lat": lat, "lng": lng, "city": selected_label or ""}
            resp = requests.post(f"{BACKEND_URL}/report", data=data, files=files, timeout=60)

        if resp.ok:
            result = resp.json()
            severity_color = {
                "overflowing": "#D32F2F", "full": "#F57C00",
                "half_full": "#C9A227", "empty": "#2E7D32",
            }.get(result["status"], "#616161")
            st.markdown(f"""
            <div class="cb-result-card" style="border-left-color:{severity_color};">
                <strong style="color:{severity_color};font-size:16px;">
                    {result['status'].replace('_', ' ').title()}
                </strong>
                <p style="color:#4B5563;margin-top:8px;">{result['reasoning']}</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.error(f"Something went wrong: {resp.text}")
