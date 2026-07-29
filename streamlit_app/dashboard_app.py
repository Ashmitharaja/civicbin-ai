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
st.title("🏛️ CivicBin AI — Municipal Dashboard")

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
        city_label = f"{b.get('city')} — " if b.get("city") else ""
        folium.Marker(
            location=[b["lat"], b["lng"]],
            popup=f"{city_label}{b['status']} ({b['confidence']:.0%} confidence)",
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
st.subheader("🤖 AI-planned collection route")
st.caption("Each truck is assigned stops based on its current position — nearest available truck gets each bin, like a dispatch system.")

if st.button("Generate route (TriageAgent → RouteAgent via A2A)"):
    with st.spinner("Agents are planning the route..."):
        route_resp = requests.get(f"{BACKEND_URL}/route", timeout=30)
    if route_resp.ok:
        st.session_state["route_result"] = route_resp.json()
    else:
        st.session_state["route_result"] = None
        st.error(f"Could not fetch route: {route_resp.text}")

route = st.session_state.get("route_result")
if route:
    if route.get("message"):
        st.info(route["message"])

    trucks = route.get("trucks", [])
    if not trucks:
        st.info("No stops needed right now.")
    else:
        all_stops = []
        for truck in trucks:
            label = f"{truck['name']}" + (f" — driver: {truck['driver_name']}" if truck.get("driver_name") else "")
            st.write(f"**{label}** ({len(truck['stops'])} stops)")
            display_df = pd.DataFrame(truck["stops"])[["stop", "city", "status", "lat", "lng"]]
            display_df.columns = ["Stop #", "Location", "Severity", "Latitude", "Longitude"]
            st.table(display_df)
            all_stops.extend(truck["stops"])

        if route.get("unassigned"):
            st.warning(f"{len(route['unassigned'])} bin(s) could not be assigned — all trucks are at capacity.")
            st.table(pd.DataFrame(route["unassigned"]))

        if all_stops:
            route_map = folium.Map(location=[all_stops[0]["lat"], all_stops[0]["lng"]], zoom_start=6)
            palette = ["#D14A2E", "#2E6FD1", "#2EA85A", "#B02EA8", "#D1962E"]
            for t_idx, truck in enumerate(trucks):
                color = palette[t_idx % len(palette)]
                coords = [(s["lat"], s["lng"]) for s in truck["stops"]]
                if len(coords) > 1:
                    folium.PolyLine(coords, color=color, weight=3, opacity=0.6).add_to(route_map)
                for s in truck["stops"]:
                    folium.Marker(
                        location=[s["lat"], s["lng"]],
                        popup=f"{truck['name']} — Stop {s['stop']}: {s['city']} ({s['status']})",
                        icon=folium.DivIcon(html=f"""<div style="background:{color};color:white;
                            border-radius:50%;width:26px;height:26px;display:flex;
                            align-items:center;justify-content:center;font-weight:bold;
                            font-size:13px;border:2px solid white;">{s['stop']}</div>"""),
                    ).add_to(route_map)
            st.write("**Route by truck (color = truck):**")
            st_folium(route_map, width=800, height=500, key="route_map")