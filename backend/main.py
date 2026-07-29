"""
FastAPI backend. Deployed to Cloud Run.

Endpoints:
  POST /report        -> citizen submits a bin photo + location; classified by
                          Gemini, saved to Firestore + BigQuery
  GET  /bins           -> all active (uncollected) bin reports, for the dashboard map
  GET  /route           -> today's truck-by-truck collection assignment (calls
                          RouteAgent's tool logic directly for a fast HTTP path;
                          the ADK/A2A agents in agents/ are the "agentic" entry
                          point used by adk web / other agents, this endpoint
                          reuses the same underlying function)
  GET  /trucks          -> all registered trucks and their live status
  POST /trucks          -> register a new truck/driver
  POST /trucks/{id}/location -> update a truck's live position (driver app GPS ping)
  POST /collect/{report_id}  -> mark a bin report as collected (driver app button)
"""
import shutil
import tempfile
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from backend.agents.route_agent.agent import get_priority_bins
from backend.bigquery_service import log_report
from backend.firebase_service import (
    get_active_reports,
    get_all_trucks,
    mark_collected,
    save_report,
    seed_truck,
    update_truck_location,
)
from backend.gemini_service import classify_bin_image

app = FastAPI(title="CivicBin AI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten before real deployment
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/report")
async def create_report(lat: float = Form(...), lng: float = Form(...),
                         city: str = Form(""), photo: UploadFile = File(...)):
    with tempfile.NamedTemporaryFile(suffix=Path(photo.filename).suffix, delete=False) as tmp:
        shutil.copyfileobj(photo.file, tmp)
        tmp_path = tmp.name

    classification = classify_bin_image(tmp_path)

    report_id = save_report(
        lat=lat,
        lng=lng,
        status=classification["status"],
        confidence=classification["confidence"],
        reasoning=classification["reasoning"],
        city=city,
    )
    try:
        log_report(
            report_id=report_id,
            lat=lat,
            lng=lng,
            status=classification["status"],
            confidence=classification["confidence"],
        )
    except Exception as exc:
        # Analytics logging is best-effort; never fail the citizen's report over it.
        print(f"[main] BigQuery logging failed (non-fatal): {exc}")

    return {"report_id": report_id, **classification}


@app.get("/bins")
def list_bins():
    return {"bins": get_active_reports()}


@app.get("/route")
def get_route():
    return get_priority_bins()


@app.get("/trucks")
def list_trucks():
    return {"trucks": get_all_trucks()}


@app.post("/trucks")
def register_truck(name: str = Form(...), driver_name: str = Form(...),
                    lat: float = Form(...), lng: float = Form(...),
                    capacity: int = Form(8)):
    truck_id = seed_truck(name=name, driver_name=driver_name, lat=lat, lng=lng, capacity=capacity)
    return {"truck_id": truck_id}


@app.post("/trucks/{truck_id}/location")
def set_truck_location(truck_id: str, lat: float = Form(...), lng: float = Form(...)):
    update_truck_location(truck_id, lat, lng)
    return {"status": "updated"}


@app.post("/collect/{report_id}")
def collect_report(report_id: str, truck_id: str = Form(...),
                    lat: float = Form(...), lng: float = Form(...)):
    mark_collected(report_id)
    # The truck is now physically at the bin it just collected — update its
    # live position so the next /route call re-sequences from here, not
    # from where it started the day.
    update_truck_location(truck_id, lat, lng)
    return {"status": "collected", "report_id": report_id, "truck_moved_to": {"lat": lat, "lng": lng}}


@app.get("/health")
def health():
    return {"status": "ok"}
