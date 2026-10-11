# PowerShell script to deploy The Café Companion to Google Cloud Run

param (
    [string]$ProjectId = "",
    [string]$Region = "us-central1",
    [string]$ServiceName = "cafe-companion"
)

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " Deploying The Café Companion to Google Cloud Run" -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Cyan

if ([string]::IsNullOrWhiteSpace($ProjectId)) {
    $ProjectId = gcloud config get-value project 2>$null
}

if ([string]::IsNullOrWhiteSpace($ProjectId)) {
    Write-Error "Please specify your Google Cloud Project ID with -ProjectId <id>"
    exit 1
}

Write-Host "Target Google Cloud Project: $ProjectId" -ForegroundColor Yellow
Write-Host "Target Region: $Region" -ForegroundColor Yellow

# Step 1: Submit build to Google Cloud Build
Write-Host "1. Submitting container build to Cloud Build..." -ForegroundColor Cyan
gcloud builds submit --tag "gcr.io/$ProjectId/${ServiceName}:latest" .

# Step 2: Deploy to Cloud Run
Write-Host "2. Deploying service to Google Cloud Run..." -ForegroundColor Cyan
gcloud run deploy $ServiceName `
    --image "gcr.io/$ProjectId/${ServiceName}:latest" `
    --platform managed `
    --region $Region `
    --allow-unauthenticated `
    --set-env-vars "GEMINI_MODEL=gemini-2.5-flash"

Write-Host "==========================================================" -ForegroundColor Green
Write-Host " Deployment Complete! Service is now live on Cloud Run." -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green
