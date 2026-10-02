# AI Smart Classroom Attention Analyzer - Production Dockerfile
# Optimized for free and scalable cloud hosting: Hugging Face Spaces, Render, Google Cloud Run, Railway, AWS

FROM python:3.11-slim as builder

# Install minimal OS dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Cache dependencies
COPY requirements-web.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements-web.txt

# Final runtime image
FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy site-packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy app code
COPY . .

# Create data directory for SQLite storage
RUN mkdir -p /app/data /app/reports

# Default environment configuration
ENV PORT=7860
ENV HOST=0.0.0.0
ENV PYTHONUNBUFFERED=1
ENV LOG_FORMAT=json

EXPOSE 7860 8000 10000

# Shell wrapper to handle dynamic cloud port assignments ($PORT)
CMD ["sh", "-c", "uvicorn web_app:app --host 0.0.0.0 --port ${PORT:-7860}"]
