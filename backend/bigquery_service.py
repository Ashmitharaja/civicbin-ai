"""
Appends every report to BigQuery so the dashboard can chart overflow
hotspots/trends over time. Firestore stays the source of truth for
"active right now"; BigQuery is the historical log for analytics.
"""
import datetime
import os

from dotenv import load_dotenv

load_dotenv()

from google.cloud import bigquery
from google.oauth2 import service_account

_cred_path = os.environ.get("FIREBASE_CREDENTIALS_PATH")
if _cred_path and os.path.exists(_cred_path):
    _credentials = service_account.Credentials.from_service_account_file(_cred_path)
    client = bigquery.Client(project=os.environ["GOOGLE_CLOUD_PROJECT"], credentials=_credentials)
else:
    # Falls back to Application Default Credentials (gcloud auth application-default login)
    client = bigquery.Client(project=os.environ["GOOGLE_CLOUD_PROJECT"])

_DATASET = os.environ.get("BIGQUERY_DATASET", "civicbin")
_TABLE = os.environ.get("BIGQUERY_TABLE", "overflow_reports")
TABLE_ID = f"{client.project}.{_DATASET}.{_TABLE}"


def log_report(report_id: str, lat: float, lng: float, status: str,
                confidence: float) -> None:
    rows = [{
        "id": report_id,
        "lat": lat,
        "lng": lng,
        "status": status,
        "confidence": confidence,
        "logged_at": datetime.datetime.utcnow().isoformat(),
    }]
    errors = client.insert_rows_json(TABLE_ID, rows)
    if errors:
        # Don't crash the request over analytics; just surface it in logs.
        print(f"[bigquery_service] insert errors: {errors}")


def get_overflow_trend(days: int = 30):
    """Daily count of 'overflowing' reports for the last N days."""
    query = f"""
        SELECT DATE(logged_at) AS day, COUNT(*) AS overflow_count
        FROM `{TABLE_ID}`
        WHERE status = 'overflowing'
          AND logged_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL @days DAY)
        GROUP BY day
        ORDER BY day
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("days", "INT64", days)]
    )
    return [dict(row) for row in client.query(query, job_config=job_config)]