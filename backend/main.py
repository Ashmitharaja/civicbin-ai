"""
FastAPI backend. Deployed to Cloud Run.

Endpoints:
  POST /report  -> citizen submits a bin photo + location; classified by
                   Gemini, saved to Firestore + BigQuery
  GET  /bins    -> all active (uncollected) bin reports, for the dashboard map
  GET  /route   -> today's prioritized collection route (calls RouteAgent's
                   tool logic directly for a fast HTTP path; the ADK/A2A
                   agents in agents/ are the "agentic" entry point used by
                   adk web / other agents, this endpoint reuses the same
                   underlying function for the dashboard's convenience)
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
from backend.firebase_service import get_active_reports, save_report
from backend.gemini_service import classify_bin_image

app = FastAPI(title="CivicBin AI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten before real deployment
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/report")
async def create_report(lat: float = Form(...), lng: float = Form(...), city: str = Form(""), photo: UploadFile = File(...)):
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


@app.get("/health")
def health():
    return {"status": "ok"}
