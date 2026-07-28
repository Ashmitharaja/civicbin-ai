import os

import folium
import pandas as pd
import requests
import streamlit as st
from dotenv import load_dotenv
from streamlit_folium import st_folium

load_dotenv()
BACKEND_URL = os.environ.get("BACKEND_URL") or st.secrets.get("BACKEND_URL", "http://localhost:8000")

st.set_page_config(page_title="CivicBin AI - Municipal Dashboard", layout="wide")
st.title("CivicBin AI — Municipal Dashboard")

STATUS_COLOR = {
    "overflowing": "red",
    "full": "orange",
    "half_full": "beige",
    "empty": "green",
}

col_map, col_stats = st.columns([2, 1])

bins_resp = requests.get(f"{BACKEND_URL}/bins", timeout=30)
bins = bins_resp.json().get("bins", []) if bins_resp.ok else []

with col_map:
    st.subheader("Active bin reports")
    m = folium.Map(location=[13.0827, 80.2707], zoom_start=12)
    for b in bins:
        folium.Marker(
            location=[b["lat"], b["lng"]],
            popup=f"{b['status']} ({b['confidence']:.0%} confidence)",
            icon=folium.Icon(color=STATUS_COLOR.get(b["status"], "gray")),
        ).add_to(m)
    st_folium(m, width=800, height=500)

with col_stats:
    st.subheader("Summary")
    df = pd.DataFrame(bins)
    if not df.empty:
        st.metric("Active reports", len(df))
        st.metric("Overflowing", int((df["status"] == "overflowing").sum()))
        st.bar_chart(df["status"].value_counts())
    else:
        st.info("No active reports.")

st.divider()
st.subheader("AI-planned collection route")
if st.button("Generate route (TriageAgent → RouteAgent via A2A)"):
    with st.spinner("Agents are planning the route..."):
        route_resp = requests.get(f"{BACKEND_URL}/route", timeout=30)
    if route_resp.ok:
        route = route_resp.json()
        if route.get("route"):
            st.write(f"**{route['stop_count']} stops**, ordered by urgency and travel distance:")
            st.table(pd.DataFrame(route["route"]))
        else:
            st.info(route.get("message", "No stops needed right now."))
    else:
        st.error(f"Could not fetch route: {route_resp.text}")
