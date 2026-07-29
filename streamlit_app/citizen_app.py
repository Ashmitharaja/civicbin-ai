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


st.set_page_config(page_title="CivicBin AI - Report a Bin", page_icon="🗑️")
st.title("Report an Overflowing Bin")
st.write("Snap a photo of the bin and we'll route a collection crew automatically.")

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
            st.success(f"Reported! Status detected: **{result['status'].replace('_', ' ').title()}**")
            st.caption(result["reasoning"])
        else:
            st.error(f"Something went wrong: {resp.text}")