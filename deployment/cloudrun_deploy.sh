#!/usr/bin/env bash
# Deploys the FastAPI backend (backend/main.py) to Cloud Run.
# Run from the repo root: bash deployment/cloudrun_deploy.sh
set -euo pipefail

PROJECT_ID="${GOOGLE_CLOUD_PROJECT:?Set GOOGLE_CLOUD_PROJECT first}"
REGION="${GOOGLE_CLOUD_LOCATION:-us-central1}"
SERVICE_NAME="civicbin-backend"

gcloud config set project "$PROJECT_ID"

gcloud builds submit --tag "gcr.io/$PROJECT_ID/$SERVICE_NAME" -f deployment/Dockerfile .

gcloud run deploy "$SERVICE_NAME" \
  --image "gcr.io/$PROJECT_ID/$SERVICE_NAME" \
  --platform managed \
  --region "$REGION" \
  --allow-unauthenticated \
  --set-env-vars "GOOGLE_CLOUD_PROJECT=$PROJECT_ID,GOOGLE_CLOUD_LOCATION=$REGION" \
  --set-secrets "GOOGLE_API_KEY=civicbin-gemini-key:latest" \
  --memory 512Mi

echo "Deployed. Update BACKEND_URL in the Streamlit apps' .env to the printed URL."
