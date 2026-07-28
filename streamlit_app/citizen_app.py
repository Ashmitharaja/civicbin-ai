import os

import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()
BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")

st.set_page_config(page_title="CivicBin AI - Report a Bin", page_icon="🗑️")
st.title("Report an Overflowing Bin")
st.write("Snap a photo of the bin and we'll route a collection crew automatically.")

with st.form("report_form"):
    photo = st.camera_input("Take a photo of the bin") or st.file_uploader(
        "...or upload a photo", type=["jpg", "jpeg", "png"]
    )
    col1, col2 = st.columns(2)
    lat = col1.number_input("Latitude", value=13.0827, format="%.6f")
    lng = col2.number_input("Longitude", value=80.2707, format="%.6f")
    submitted = st.form_submit_button("Submit report")

if submitted:
    if not photo:
        st.error("Please add a photo first.")
    else:
        with st.spinner("Analyzing photo with Gemini..."):
            files = {"photo": (photo.name if hasattr(photo, "name") else "photo.jpg", photo.getvalue())}
            data = {"lat": lat, "lng": lng}
            resp = requests.post(f"{BACKEND_URL}/report", data=data, files=files, timeout=60)

        if resp.ok:
            result = resp.json()
            st.success(f"Reported! Status detected: **{result['status'].replace('_', ' ').title()}**")
            st.caption(result["reasoning"])
        else:
            st.error(f"Something went wrong: {resp.text}")
