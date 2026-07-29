import os

import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()
BACKEND_URL = os.environ.get("BACKEND_URL") or st.secrets.get("BACKEND_URL", "http://localhost:8000")

st.set_page_config(page_title="CivicBin AI - Driver App", page_icon="🚛")
st.title("🚛 Driver — Today's Stops")

tab_stops, tab_register = st.tabs(["My route", "Register a truck"])

with tab_stops:
    trucks_resp = requests.get(f"{BACKEND_URL}/trucks", timeout=30)
    trucks = trucks_resp.json().get("trucks", []) if trucks_resp.ok else []

    if not trucks:
        st.info("No trucks registered yet. Use the 'Register a truck' tab to add one.")
    else:
        truck_names = {f"{t['name']} ({t.get('driver_name', 'unassigned')})": t for t in trucks}
        chosen_label = st.selectbox("Select your truck", list(truck_names.keys()))
        truck = truck_names[chosen_label]

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
                for s in my_stops:
                    with st.container(border=True):
                        st.write(f"**Stop {s['stop']}: {s['city']}**")
                        st.caption(f"{s['status']} — ({s['lat']}, {s['lng']})")
                        if st.button("Mark collected", key=f"collect_{s['id']}"):
                            collect_resp = requests.post(f"{BACKEND_URL}/collect/{s['id']}", timeout=15)
                            if collect_resp.ok:
                                st.success("Marked collected — refresh route to update the list.")
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