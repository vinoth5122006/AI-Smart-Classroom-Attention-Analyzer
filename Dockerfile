# AI Smart Classroom Attention Analyzer - Production Dockerfile
# Single-stage build for reliable module resolution on Render, Railway, Hugging Face Spaces

FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements-web.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements-web.txt

COPY . .

# GitHub uploads from Windows can store "modules\file.py" as a filename.
# Rebuild real directories so `import modules` works on Linux.
RUN python normalize_win_paths.py /app && \
    test -f /app/modules/attention_engine.py && \
    python -c "from modules.attention_engine import AttentionEngine"

RUN mkdir -p /app/data /app/reports

ENV PORT=7860
ENV HOST=0.0.0.0
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV LOG_FORMAT=json

EXPOSE 7860 8000 10000

CMD ["sh", "-c", "uvicorn web_app:app --host 0.0.0.0 --port ${PORT:-7860}"]
