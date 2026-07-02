FROM python:3.12-slim

WORKDIR /app

# System deps: build-essential/curl as before, libgomp1 for fastembed's
# ONNX runtime (the local, free embedding model).
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download the local embedding model at build time so the first real
# request doesn't pay a cold-start download. Safe to skip/fail here --
# app/core/llm_client.py lazy-loads it on first use either way.
RUN python -c "from fastembed import TextEmbedding; TextEmbedding(model_name='BAAI/bge-small-en-v1.5')" || true

COPY . .

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run migrations then start the server. Binds to $PORT when set (Render,
# and most PaaS providers, inject this) and falls back to 8000 for local
# docker-compose, where PORT is never set.
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
