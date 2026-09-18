# ==============================================================================
# WATTPAD AI AUDIOBOOK - PRODUCTION DOCKERFILE
# ==============================================================================

FROM python:3.11-slim AS base

# Prevent Python from writing .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000 \
    HOST=0.0.0.0

WORKDIR /app

# Install system runtime dependencies:
# - libsndfile1: Required by soundfile library for audio I/O
# - ffmpeg: Audio encoding, conversion & streaming support
# - curl: Container health checks
# - libgomp1: OpenMP runtime for ONNX Neural TTS acceleration
RUN apt-get update && apt-get install -y --no-install-recommends \
    libsndfile1 \
    ffmpeg \
    curl \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Layer cache optimization: Copy and install Python dependencies first
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/backend/requirements.txt

# Copy application source code
COPY backend/ /app/backend/
COPY frontend/ /app/frontend/
COPY tests/ /app/tests/

# Ensure persistent data directories exist
RUN mkdir -p /app/backend/data/audio \
             /app/backend/data/archives \
             /app/backend/data/stories \
             /app/backend/data/custom_texts \
             /app/backend/data/tasks \
             /app/backend/data/users

# Expose standard application port
EXPOSE 8000

# Health check to monitor server availability
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/languages || exit 1

# Start FastAPI application with Uvicorn
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
