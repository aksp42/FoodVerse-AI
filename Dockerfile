# =============================================================================
# FoodVerse AI — Multi-Stage Production Dockerfile for Google Cloud Run
# =============================================================================

# --- Stage 1: Build React/Vite Frontend ---
FROM node:20-slim AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

# --- Stage 2: Production Python Backend ---
FROM python:3.11-slim AS runner

# Install system libraries needed by OpenCV headless & media processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libgomp1 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python production dependencies
COPY backend/requirements-prod.txt ./requirements-prod.txt
RUN pip install --no-cache-dir -r requirements-prod.txt

# Copy backend application code and SQLite database baseline
COPY backend/ ./

# Copy compiled frontend SPA from Stage 1 into frontend_dist
COPY --from=frontend-builder /app/frontend/dist ./frontend_dist

# Cloud Run injects PORT environment variable (default 8080)
ENV PORT=8080
ENV PYTHONUNBUFFERED=1

EXPOSE 8080

# Start Uvicorn ASGI server
CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT:-8080}"]
