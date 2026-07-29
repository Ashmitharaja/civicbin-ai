import os

import folium
import requests
import streamlit as st
from dotenv import load_dotenv
from streamlit_folium import st_folium

load_dotenv()
BACKEND_URL = os.environ.get("BACKEND_URL") or st.secrets.get("BACKEND_URL", "http://localhost:8000")

st.set_page_config(page_title="CivicBin AI - Driver App", layout="wide")

st.markdown("""
<style>
.block-container {padding-top: 2rem; padding-bottom: 3rem;}
.cb-header {
    background: linear-gradient(135deg, #0F4C43 0%, #1B6E5C 100%);
    padding: 26px 28px; border-radius: 12px; margin-bottom: 22px;
}
.cb-header h1 {color: #FFFFFF; font-size: 24px; margin: 0; font-weight: 700;}
.cb-header p {color: #CFE8E1; font-size: 14px; margin: 6px 0 0 0;}
.cb-stop-card {
    background: #FFFFFF; border: 1px solid #E5E9EB; border-left: 5px solid #1B6E5C;
    border-radius: 8px; padding: 16px 18px; margin-bottom: 12px;
}
div.stButton > button, div.stFormSubmitButton > button {
    background-color: #1B6E5C; color: white; border: none; border-radius: 8px;
    padding: 9px 20px; font-weight: 600;
}
div.stButton > button:hover, div.stFormSubmitButton > button:hover {background-color: #0F4C43; color: white;}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="cb-header">
  <h1>Driver — Today's Stops</h1>
  <p>View your assigned route, track live position, and mark bins collected.</p>
</div>
""", unsafe_allow_html=True)

tab_stops, tab_register = st.tabs(["My Route", "Register a Truck"])

with tab_stops:
    trucks_resp = requests.get(f"{BACKEND_URL}/trucks", timeout=30)
    trucks = trucks_resp.json().get("trucks", []) if trucks_resp.ok else []

    if not trucks:
        st.info("No trucks registered yet. Use the 'Register a Truck' tab to add one.")
    else:
        truck_names = {f"{t['name']} ({t.get('driver_name', 'unassigned')})": t for t in trucks}
        chosen_label = st.selectbox("Select your truck", list(truck_names.keys()))
        truck = truck_names[chosen_label]

        st.markdown(f"""
        <div class="cb-stop-card">
            <strong>Current position</strong><br/>
            <span style="color:#6B7280;">{truck['lat']:.5f}, {truck['lng']:.5f}</span>
        </div>
        """, unsafe_allow_html=True)

        pos_map = folium.Map(location=[truck["lat"], truck["lng"]], zoom_start=10, tiles="CartoDB positron")
        folium.Marker(
            location=[truck["lat"], truck["lng"]],
            popup=f"{truck['name']} — current position",
            icon=folium.DivIcon(html=f"""<div style="background:#1B6E5C;color:white;
                border-radius:6px;padding:4px 10px;font-weight:700;font-size:12px;
                border:2px solid white;">{truck['name']}</div>"""),
        ).add_to(pos_map)
        st_folium(pos_map, width=700, height=280, key="driver_pos_map")

        if st.button("Refresh my route"):
            with st.spinner("Fetching latest assignment..."):
                route_resp = requests.get(f"{BACKEND_URL}/route", timeout=30)
            st.session_state["driver_route"] = route_resp.json() if route_resp.ok else None

        route = st.session_state.get("driver_route")
        if route:
            my_stops = []
            for t in route.get("trucks", []):
                if t.get("truck_id") == truck["id"]:
                    my_stops = t["stops"]
                    break

            if not my_stops:
                st.info("No stops currently assigned to this truck.")
            else:
                severity_color = {
                    "overflowing": "#D32F2F", "full": "#F57C00",
                    "half_full": "#C9A227", "empty": "#2E7D32",
                }
                for s in my_stops:
                    color = severity_color.get(s["status"], "#616161")
                    st.markdown(f"""
                    <div class="cb-stop-card" style="border-left-color:{color};">
                        <strong>Stop {s['stop']}: {s['city']}</strong><br/>
                        <span style="color:{color};font-weight:600;">{s['status'].replace('_', ' ').title()}</span>
                        <span style="color:#6B7280;"> — {s['lat']}, {s['lng']}</span>
                    </div>
                    """, unsafe_allow_html=True)
                    if st.button("Mark collected", key=f"collect_{s['id']}"):
                        collect_resp = requests.post(
                            f"{BACKEND_URL}/collect/{s['id']}",
                            data={"truck_id": truck["id"], "lat": s["lat"], "lng": s["lng"]},
                            timeout=15,
                        )
                        if collect_resp.ok:
                            st.success("Marked collected. Truck position updated — refresh route to re-optimize remaining stops.")
                        else:
                            st.error(f"Could not update: {collect_resp.text}")
        else:
            st.info("Click 'Refresh my route' to load today's assignment.")

with tab_register:
    st.write("Register a truck once per vehicle — it then becomes eligible for route assignment.")
    with st.form("register_truck_form"):
        name = st.text_input("Truck name / number", placeholder="e.g. TN-07-AB-1234")
        driver_name = st.text_input("Driver name")
        col1, col2 = st.columns(2)
        lat = col1.number_input("Current latitude", value=13.0827, format="%.6f")
        lng = col2.number_input("Current longitude", value=80.2707, format="%.6f")
        capacity = st.number_input("Capacity (max stops per run)", min_value=1, value=8)
        submitted = st.form_submit_button("Register truck")

    if submitted:
        if not name or not driver_name:
            st.error("Truck name and driver name are required.")
        else:
            resp = requests.post(
                f"{BACKEND_URL}/trucks",
                data={"name": name, "driver_name": driver_name, "lat": lat, "lng": lng, "capacity": capacity},
                timeout=15,
            )
            if resp.ok:
                st.success(f"Truck registered: {resp.json()['truck_id']}")
            else:
                st.error(f"Could not register truck: {resp.text}")