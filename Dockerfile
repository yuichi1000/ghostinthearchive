# Cloud Run Dockerfile for Python pipelines and services
# Supports: mystery pipeline, podcast pipeline, curator service, alchemist pipeline

FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY pyproject.toml ./
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# rembg U2-NET モデルをプリダウンロード（初回実行時の待ちを回避）
RUN python -c "from rembg import new_session; new_session('u2netp')"

# Copy source code
COPY shared/ ./shared/
COPY mystery_agents/ ./mystery_agents/
COPY curator_agents/ ./curator_agents/
COPY podcast_agents/ ./podcast_agents/
COPY alchemist_agents/ ./alchemist_agents/
COPY services/ ./services/

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV GOOGLE_CLOUD_PROJECT=ghostinthearchive
ENV GOOGLE_CLOUD_LOCATION=global
ENV GOOGLE_GENAI_USE_VERTEXAI=TRUE

# Default entrypoint (overridden by Cloud Run configuration)
# mystery pipeline: python -m mystery_agents "<query>"
# podcast pipeline: python -m podcast_agents "<mystery_id>"
# curator service:  python services/curator.py
# pipeline server:  python services/pipeline_server.py
ENTRYPOINT ["python"]
