# ChimeraC2 — Teamserver Dockerfile
FROM python:3.11-slim

# Keep Python output unbuffered so logs show up live in `docker compose logs`
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install deps first (layer caching — much faster rebuilds)
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the app code
COPY app /app/app

# Expose the FastAPI port
EXPOSE 8000

# Run uvicorn against the app module
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
