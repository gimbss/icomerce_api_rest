# =============================================================================
# Build stage
# =============================================================================
FROM python:3.14-slim AS builder

WORKDIR /app

# Install build dependencies for psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt psycopg2-binary

# =============================================================================
# Runtime stage
# =============================================================================
FROM python:3.14-slim

WORKDIR /app

# Install runtime dependency for psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY . .

# Create database directory for SQLite (used in local dev)
RUN mkdir -p /app/app/database

EXPOSE 8000

# Run with uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]