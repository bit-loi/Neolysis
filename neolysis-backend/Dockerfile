# ============================================
# Stage 1: Build dependencies
# ============================================
FROM python:3.12-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ============================================
# Stage 2: Production image
# ============================================
FROM python:3.12-slim

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    libxrender1 \
    libxext6 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /install /usr/local

WORKDIR /app

# Copy application code
COPY . .

# Create storage directory for docking jobs
RUN mkdir -p storage/docking

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["sh", "-c", "python -m alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port 8000"]
