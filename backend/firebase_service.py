"""
Firestore access layer. Stores each bin report as a document in the
`bin_reports` collection.
"""
import datetime
import os
import uuid

from dotenv import load_dotenv

load_dotenv()

import firebase_admin
from firebase_admin import credentials, firestore

_cred_path = os.environ.get("FIREBASE_CREDENTIALS_PATH", "./firebase-service-account.json")

if not firebase_admin._apps:
    cred = credentials.Certificate(_cred_path)
    firebase_admin.initialize_app(cred)

db = firestore.client()
COLLECTION = "bin_reports"


def save_report(lat: float, lng: float, status: str, confidence: float,
                 reasoning: str, city: str = "", photo_url: str | None = None) -> str:
    report_id = str(uuid.uuid4())
    db.collection(COLLECTION).document(report_id).set({
        "id": report_id,
        "lat": lat,
        "lng": lng,
        "city": city,
        "status": status,
        "confidence": confidence,
        "reasoning": reasoning,
        "photo_url": photo_url,
        "collected": False,
        "created_at": datetime.datetime.utcnow().isoformat(),
    })
    return report_id


def get_active_reports() -> list[dict]:
    """Reports that haven't been marked collected yet."""
    docs = db.collection(COLLECTION).where("collected", "==", False).stream()
    return [d.to_dict() for d in docs]


def mark_collected(report_id: str) -> None:
    db.collection(COLLECTION).document(report_id).update({"collected": True})


# ---------------------------------------------------------------------------
# Trucks / drivers — live dispatch state
# ---------------------------------------------------------------------------
TRUCKS_COLLECTION = "trucks"


def seed_truck(name: str, driver_name: str, lat: float, lng: float, capacity: int = 8) -> str:
    """Register a truck/driver. Call this once per truck when onboarding a
    vehicle (e.g. from an admin screen) — not on every request."""
    truck_id = str(uuid.uuid4())
    db.collection(TRUCKS_COLLECTION).document(truck_id).set({
        "id": truck_id,
        "name": name,
        "driver_name": driver_name,
        "lat": lat,
        "lng": lng,
        "capacity": capacity,
        "load": 0,
        "status": "available",  # available | on_route | offline
    })
    return truck_id


def get_available_trucks() -> list[dict]:
    docs = db.collection(TRUCKS_COLLECTION).where("status", "==", "available").stream()
    return [d.to_dict() for d in docs]


def get_all_trucks() -> list[dict]:
    docs = db.collection(TRUCKS_COLLECTION).stream()
    return [d.to_dict() for d in docs]


def update_truck_location(truck_id: str, lat: float, lng: float) -> None:
    """A driver's app would call this periodically (like a taxi app's GPS
    ping) to keep the truck's live position current for routing."""
    db.collection(TRUCKS_COLLECTION).document(truck_id).update({"lat": lat, "lng": lng})


def set_truck_status(truck_id: str, status: str) -> None:
    db.collection(TRUCKS_COLLECTION).document(truck_id).update({"status": status})