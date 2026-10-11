# Use official lightweight Python image
FROM python:3.12-slim

# Set working directory in container
WORKDIR /app

# Ensure output is sent directly to terminal without buffering
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code and assets
COPY app/ ./app/
COPY static/ ./static/
COPY templates/ ./templates/
COPY main.py .

# Expose Cloud Run default port
EXPOSE 8080

# Launch FastAPI app with Uvicorn on Cloud Run dynamically assigned PORT
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT}"]
