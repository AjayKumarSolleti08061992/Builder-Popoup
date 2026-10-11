#!/usr/bin/env bash
# Deploy The Café Companion to Google Cloud Run

set -e

PROJECT_ID=${1:-$(gcloud config get-value project 2>/dev/null)}
REGION=${2:-"us-central1"}
SERVICE_NAME="cafe-companion"

if [ -z "$PROJECT_ID" ]; then
  echo "Error: Google Cloud project ID not provided. Usage: ./deploy_cloud_run.sh <PROJECT_ID> [REGION]"
  exit 1
fi

echo "Building and deploying to Google Cloud Run for project: $PROJECT_ID ($REGION)..."

# Build and push container image using Cloud Build
gcloud builds submit --tag "gcr.io/${PROJECT_ID}/${SERVICE_NAME}:latest" .

# Deploy to Cloud Run
gcloud run deploy "$SERVICE_NAME" \
  --image "gcr.io/${PROJECT_ID}/${SERVICE_NAME}:latest" \
  --platform managed \
  --region "$REGION" \
  --allow-unauthenticated \
  --set-env-vars "GEMINI_MODEL=gemini-2.5-flash"

echo "Successfully deployed to Google Cloud Run!"
