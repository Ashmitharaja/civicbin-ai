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
                 reasoning: str, photo_url: str | None = None) -> str:
    report_id = str(uuid.uuid4())
    db.collection(COLLECTION).document(report_id).set({
        "id": report_id,
        "lat": lat,
        "lng": lng,
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
