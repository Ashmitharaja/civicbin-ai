# import os

# import folium
# import pandas as pd
# import requests
# import streamlit as st
# from dotenv import load_dotenv
# from streamlit_folium import st_folium

# load_dotenv()
# BACKEND_URL = os.environ.get("BACKEND_URL") or st.secrets.get("BACKEND_URL", "http://localhost:8000")

# st.set_page_config(page_title="CivicBin AI - Municipal Dashboard", layout="wide")

# st.markdown("""
# <style>
# .block-container {padding-top: 2rem; padding-bottom: 3rem;}
# .cb-header {
#     background: linear-gradient(135deg, #0F4C43 0%, #1B6E5C 100%);
#     padding: 28px 32px; border-radius: 12px; margin-bottom: 24px;
# }
# .cb-header h1 {color: #FFFFFF; font-size: 28px; margin: 0; font-weight: 700;}
# .cb-header p {color: #CFE8E1; font-size: 14px; margin: 6px 0 0 0;}
# .cb-card {
#     background: #FFFFFF; border: 1px solid #E5E9EB; border-radius: 10px;
#     padding: 18px 20px; margin-bottom: 14px;
# }
# .cb-badge {
#     display: inline-block; padding: 3px 10px; border-radius: 20px;
#     font-size: 12px; font-weight: 600; color: white;
# }
# .cb-section-title {font-size: 18px; font-weight: 700; color: #1F2937; margin-bottom: 4px;}
# .cb-section-sub {font-size: 13px; color: #6B7280; margin-bottom: 16px;}
# div.stButton > button {
#     background-color: #1B6E5C; color: white; border: none; border-radius: 8px;
#     padding: 10px 20px; font-weight: 600;
# }
# div.stButton > button:hover {background-color: #0F4C43; color: white;}
# </style>
# """, unsafe_allow_html=True)

# st.markdown("""
# <div class="cb-header">
#   <h1>Municipal Waste Operations Dashboard</h1>
#   <p>Live bin status, fleet position, and AI-planned collection routing</p>
# </div>
# """, unsafe_allow_html=True)

# STATUS_COLOR = {
#     "overflowing": "#D32F2F",
#     "full": "#F57C00",
#     "half_full": "#C9A227",
#     "empty": "#2E7D32",
# }
# STATUS_LABEL = {
#     "overflowing": "Overflowing",
#     "full": "Full",
#     "half_full": "Half Full",
#     "empty": "Empty",
# }

# bins_resp = requests.get(f"{BACKEND_URL}/bins", timeout=30)
# bins = bins_resp.json().get("bins", []) if bins_resp.ok else []

# trucks_resp = requests.get(f"{BACKEND_URL}/trucks", timeout=30)
# trucks_live = trucks_resp.json().get("trucks", []) if trucks_resp.ok else []

# col_map, col_stats = st.columns([2, 1])

# with col_map:
#     st.markdown('<div class="cb-section-title">Live map</div>', unsafe_allow_html=True)
#     st.markdown('<div class="cb-section-sub">Bin reports and current fleet position</div>', unsafe_allow_html=True)
#     m = folium.Map(location=[13.0827, 80.2707], zoom_start=6, tiles="CartoDB positron")

#     for b in bins:
#         city_label = f"{b.get('city')} — " if b.get("city") else ""
#         color = STATUS_COLOR.get(b["status"], "#616161")
#         folium.CircleMarker(
#             location=[b["lat"], b["lng"]],
#             radius=8, color=color, fill=True, fill_color=color, fill_opacity=0.9, weight=2,
#             popup=f"{city_label}{STATUS_LABEL.get(b['status'], b['status'])} ({b['confidence']:.0%} confidence)",
#         ).add_to(m)

#     for t in trucks_live:
#         folium.Marker(
#             location=[t["lat"], t["lng"]],
#             popup=f"Truck {t.get('name', t.get('id'))} — Driver: {t.get('driver_name', 'unassigned')} — Status: {t.get('status', 'unknown')}",
#             icon=folium.DivIcon(html=f"""<div style="background:#1B6E5C;color:white;
#                 border-radius:6px;padding:4px 8px;font-weight:700;font-size:12px;
#                 border:2px solid white;box-shadow:0 1px 3px rgba(0,0,0,0.3);
#                 white-space:nowrap;">{t.get('name', 'Truck')}</div>"""),
#         ).add_to(m)

#     st_folium(m, width=800, height=500, key="main_map")

# with col_stats:
#     st.markdown('<div class="cb-section-title">Summary</div>', unsafe_allow_html=True)
#     df = pd.DataFrame(bins)
#     if not df.empty:
#         c1, c2 = st.columns(2)
#         c1.metric("Active reports", len(df))
#         c2.metric("Overflowing", int((df["status"] == "overflowing").sum()))
#         st.markdown('<div class="cb-card">', unsafe_allow_html=True)
#         st.write("Status breakdown")
#         st.bar_chart(df["status"].value_counts())
#         st.markdown('</div>', unsafe_allow_html=True)
#     else:
#         st.info("No active reports.")

#     st.markdown('<div class="cb-section-title" style="margin-top:20px;">Fleet</div>', unsafe_allow_html=True)
#     if trucks_live:
#         for t in trucks_live:
#             st.markdown(f"""
#             <div class="cb-card">
#                 <strong>{t.get('name')}</strong><br/>
#                 <span style="color:#6B7280;font-size:13px;">Driver: {t.get('driver_name', 'unassigned')}</span><br/>
#                 <span style="color:#6B7280;font-size:13px;">Position: {t['lat']:.4f}, {t['lng']:.4f}</span><br/>
#                 <span class="cb-badge" style="background-color:{'#2E7D32' if t.get('status')=='available' else '#616161'};">{t.get('status', 'unknown')}</span>
#             </div>
#             """, unsafe_allow_html=True)
#     else:
#         st.info("No trucks registered yet.")

# st.divider()
# st.markdown('<div class="cb-section-title">AI-planned collection route</div>', unsafe_allow_html=True)
# st.markdown('<div class="cb-section-sub">Each truck is assigned the nearest available stops from its current live position, then sequenced by shortest travel path.</div>', unsafe_allow_html=True)

# if st.button("Generate route (TriageAgent -> RouteAgent via A2A)"):
#     with st.spinner("Agents are planning the route..."):
#         route_resp = requests.get(f"{BACKEND_URL}/route", timeout=30)
#     if route_resp.ok:
#         st.session_state["route_result"] = route_resp.json()
#     else:
#         st.session_state["route_result"] = None
#         st.error(f"Could not fetch route: {route_resp.text}")

# route = st.session_state.get("route_result")
# if route:
#     if route.get("message"):
#         st.info(route["message"])

#     trucks = route.get("trucks", [])
#     if not trucks:
#         st.info("No stops needed right now.")
#     else:
#         all_stops = []
#         for truck in trucks:
#             label = f"{truck['name']}" + (f" — Driver: {truck['driver_name']}" if truck.get("driver_name") else "")
#             st.markdown(f'<div class="cb-card"><strong>{label}</strong> — {len(truck["stops"])} stop(s)</div>', unsafe_allow_html=True)
#             display_df = pd.DataFrame(truck["stops"])[["stop", "city", "status", "lat", "lng"]]
#             display_df["status"] = display_df["status"].map(lambda s: STATUS_LABEL.get(s, s))
#             display_df.columns = ["Stop #", "Location", "Severity", "Latitude", "Longitude"]
#             st.table(display_df)
#             all_stops.extend(truck["stops"])

#         if route.get("unassigned"):
#             st.warning(f"{len(route['unassigned'])} bin(s) could not be assigned — all trucks are at capacity.")
#             st.table(pd.DataFrame(route["unassigned"]))

#         if all_stops:
#             route_map = folium.Map(location=[all_stops[0]["lat"], all_stops[0]["lng"]], zoom_start=6, tiles="CartoDB positron")
#             palette = ["#D14A2E", "#2E6FD1", "#2EA85A", "#B02EA8", "#D1962E"]
#             for t_idx, truck in enumerate(trucks):
#                 color = palette[t_idx % len(palette)]
#                 coords = [(s["lat"], s["lng"]) for s in truck["stops"]]
#                 if len(coords) > 1:
#                     folium.PolyLine(coords, color=color, weight=3, opacity=0.7).add_to(route_map)
#                 for s in truck["stops"]:
#                     folium.Marker(
#                         location=[s["lat"], s["lng"]],
#                         popup=f"{truck['name']} — Stop {s['stop']}: {s['city']} ({STATUS_LABEL.get(s['status'], s['status'])})",
#                         icon=folium.DivIcon(html=f"""<div style="background:{color};color:white;
#                             border-radius:50%;width:26px;height:26px;display:flex;
#                             align-items:center;justify-content:center;font-weight:bold;
#                             font-size:13px;border:2px solid white;box-shadow:0 1px 3px rgba(0,0,0,0.3);">{s['stop']}</div>"""),
#                     ).add_to(route_map)
#             st.markdown('<div class="cb-section-title" style="margin-top:16px;">Route by truck</div>', unsafe_allow_html=True)
#             st.markdown("<div class=\"cb-section-sub\">Each color represents one truck's path in visiting order.</div>", unsafe_allow_html=True)
#             st_folium(route_map, width=800, height=500, key="route_map")

import os

import folium
import pandas as pd
import requests
import streamlit as st
from dotenv import load_dotenv
from streamlit_folium import st_folium

load_dotenv()
BACKEND_URL = os.environ.get("BACKEND_URL") or st.secrets.get("BACKEND_URL", "http://localhost:8000")

OSRM_URL = "https://router.project-osrm.org/route/v1/driving"


def get_road_path(stops):
    """Real road-following path between stops, via OSRM's free public
    routing engine (returns actual driving geometry, not a straight line).
    Falls back to a straight line only if the routing service is
    unreachable, so the map never breaks even if OSRM is briefly down."""
    if len(stops) < 2:
        return [(s["lat"], s["lng"]) for s in stops]
    coords_str = ";".join(f"{s['lng']},{s['lat']}" for s in stops)
    try:
        resp = requests.get(
            f"{OSRM_URL}/{coords_str}",
            params={"overview": "full", "geometries": "geojson"},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("code") == "Ok" and data.get("routes"):
            geometry = data["routes"][0]["geometry"]["coordinates"]  # [lon, lat] pairs
            return [(lat, lon) for lon, lat in geometry]
    except requests.RequestException:
        pass
    return [(s["lat"], s["lng"]) for s in stops]

st.set_page_config(page_title="CivicBin AI - Municipal Dashboard", layout="wide")

st.markdown("""
<style>
.block-container {padding-top: 2rem; padding-bottom: 3rem;}
.cb-header {
    background: linear-gradient(135deg, #0F4C43 0%, #1B6E5C 100%);
    padding: 28px 32px; border-radius: 12px; margin-bottom: 24px;
}
.cb-header h1 {color: #FFFFFF; font-size: 28px; margin: 0; font-weight: 700;}
.cb-header p {color: #CFE8E1; font-size: 14px; margin: 6px 0 0 0;}
.cb-card {
    background: #FFFFFF; border: 1px solid #E5E9EB; border-radius: 10px;
    padding: 18px 20px; margin-bottom: 14px;
}
.cb-badge {
    display: inline-block; padding: 3px 10px; border-radius: 20px;
    font-size: 12px; font-weight: 600; color: white;
}
.cb-section-title {font-size: 18px; font-weight: 700; color: #1F2937; margin-bottom: 4px;}
.cb-section-sub {font-size: 13px; color: #6B7280; margin-bottom: 16px;}
div.stButton > button {
    background-color: #1B6E5C; color: white; border: none; border-radius: 8px;
    padding: 10px 20px; font-weight: 600;
}
div.stButton > button:hover {background-color: #0F4C43; color: white;}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="cb-header">
  <h1>Municipal Waste Operations Dashboard</h1>
  <p>Live bin status, fleet position, and AI-planned collection routing</p>
</div>
""", unsafe_allow_html=True)

STATUS_COLOR = {
    "overflowing": "#D32F2F",
    "full": "#F57C00",
    "half_full": "#C9A227",
    "empty": "#2E7D32",
}
STATUS_LABEL = {
    "overflowing": "Overflowing",
    "full": "Full",
    "half_full": "Half Full",
    "empty": "Empty",
}

bins_resp = requests.get(f"{BACKEND_URL}/bins", timeout=30)
bins = bins_resp.json().get("bins", []) if bins_resp.ok else []

trucks_resp = requests.get(f"{BACKEND_URL}/trucks", timeout=30)
trucks_live = trucks_resp.json().get("trucks", []) if trucks_resp.ok else []

col_map, col_stats = st.columns([2, 1])

with col_map:
    st.markdown('<div class="cb-section-title">Live map</div>', unsafe_allow_html=True)
    st.markdown('<div class="cb-section-sub">Bin reports and current fleet position</div>', unsafe_allow_html=True)
    m = folium.Map(location=[13.0827, 80.2707], zoom_start=6, tiles="CartoDB positron")

    for b in bins:
        city_label = f"{b.get('city')} — " if b.get("city") else ""
        color = STATUS_COLOR.get(b["status"], "#616161")
        folium.CircleMarker(
            location=[b["lat"], b["lng"]],
            radius=8, color=color, fill=True, fill_color=color, fill_opacity=0.9, weight=2,
            popup=f"{city_label}{STATUS_LABEL.get(b['status'], b['status'])} ({b['confidence']:.0%} confidence)",
        ).add_to(m)

    for t in trucks_live:
        folium.Marker(
            location=[t["lat"], t["lng"]],
            popup=f"Truck {t.get('name', t.get('id'))} — Driver: {t.get('driver_name', 'unassigned')} — Status: {t.get('status', 'unknown')}",
            icon=folium.DivIcon(html=f"""<div style="background:#1B6E5C;color:white;
                border-radius:6px;padding:4px 8px;font-weight:700;font-size:12px;
                border:2px solid white;box-shadow:0 1px 3px rgba(0,0,0,0.3);
                white-space:nowrap;">{t.get('name', 'Truck')}</div>"""),
        ).add_to(m)

    st_folium(m, width=800, height=500, key="main_map")

with col_stats:
    st.markdown('<div class="cb-section-title">Summary</div>', unsafe_allow_html=True)
    df = pd.DataFrame(bins)
    if not df.empty:
        c1, c2 = st.columns(2)
        c1.metric("Active reports", len(df))
        c2.metric("Overflowing", int((df["status"] == "overflowing").sum()))
        st.markdown('<div class="cb-card">', unsafe_allow_html=True)
        st.write("Status breakdown")
        st.bar_chart(df["status"].value_counts())
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("No active reports.")

    st.markdown('<div class="cb-section-title" style="margin-top:20px;">Fleet</div>', unsafe_allow_html=True)
    if trucks_live:
        for t in trucks_live:
            st.markdown(f"""
            <div class="cb-card">
                <strong>{t.get('name')}</strong><br/>
                <span style="color:#6B7280;font-size:13px;">Driver: {t.get('driver_name', 'unassigned')}</span><br/>
                <span style="color:#6B7280;font-size:13px;">Position: {t['lat']:.4f}, {t['lng']:.4f}</span><br/>
                <span class="cb-badge" style="background-color:{'#2E7D32' if t.get('status')=='available' else '#616161'};">{t.get('status', 'unknown')}</span>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No trucks registered yet.")

st.divider()
st.markdown('<div class="cb-section-title">AI-planned collection route</div>', unsafe_allow_html=True)
st.markdown('<div class="cb-section-sub">Each truck is assigned the nearest available stops from its current live position, then sequenced by shortest travel path.</div>', unsafe_allow_html=True)

if st.button("Generate route (TriageAgent -> RouteAgent via A2A)"):
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
            label = f"{truck['name']}" + (f" — Driver: {truck['driver_name']}" if truck.get("driver_name") else "")
            st.markdown(f'<div class="cb-card"><strong>{label}</strong> — {len(truck["stops"])} stop(s)</div>', unsafe_allow_html=True)
            display_df = pd.DataFrame(truck["stops"])[["stop", "city", "status", "lat", "lng"]]
            display_df["status"] = display_df["status"].map(lambda s: STATUS_LABEL.get(s, s))
            display_df.columns = ["Stop #", "Location", "Severity", "Latitude", "Longitude"]
            st.table(display_df)
            all_stops.extend(truck["stops"])

        if route.get("unassigned"):
            st.warning(f"{len(route['unassigned'])} bin(s) could not be assigned — all trucks are at capacity.")
            st.table(pd.DataFrame(route["unassigned"]))

        if all_stops:
            route_map = folium.Map(location=[all_stops[0]["lat"], all_stops[0]["lng"]], zoom_start=6, tiles="CartoDB positron")
            palette = ["#D14A2E", "#2E6FD1", "#2EA85A", "#B02EA8", "#D1962E"]
            with st.spinner("Fetching real road paths..."):
                for t_idx, truck in enumerate(trucks):
                    color = palette[t_idx % len(palette)]
                    if len(truck["stops"]) > 1:
                        road_path = get_road_path(truck["stops"])
                        folium.PolyLine(road_path, color=color, weight=4, opacity=0.75).add_to(route_map)
                    for s in truck["stops"]:
                        folium.Marker(
                            location=[s["lat"], s["lng"]],
                            popup=f"{truck['name']} — Stop {s['stop']}: {s['city']} ({STATUS_LABEL.get(s['status'], s['status'])})",
                            icon=folium.DivIcon(html=f"""<div style="background:{color};color:white;
                                border-radius:50%;width:26px;height:26px;display:flex;
                                align-items:center;justify-content:center;font-weight:bold;
                                font-size:13px;border:2px solid white;box-shadow:0 1px 3px rgba(0,0,0,0.3);">{s['stop']}</div>"""),
                        ).add_to(route_map)
            st.markdown('<div class="cb-section-title" style="margin-top:16px;">Route by truck</div>', unsafe_allow_html=True)
            st.markdown("<div class=\"cb-section-sub\">Each path follows real roads between stops, in visiting order.</div>", unsafe_allow_html=True)
            st_folium(route_map, width=800, height=500, key="route_map")
