# Multi-stage build for auth-service
# Stage 1: Builder stage for dependencies
FROM python:3.11-slim as builder

# Set environment variables for build stage
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install build tools
RUN pip install --upgrade pip setuptools wheel

# Create requirements.txt from dependencies
WORKDIR /build
COPY services/auth-service/pyproject.toml /build/

# Create requirements.txt with exact versions
RUN echo "fastapi==0.104.0" > requirements.txt && \
    echo "uvicorn[standard]==0.24.0" >> requirements.txt && \
    echo "sqlalchemy==2.0.23" >> requirements.txt && \
    echo "alembic==1.12.1" >> requirements.txt && \
    echo "asyncpg==0.29.0" >> requirements.txt && \
    echo "redis==5.0.1" >> requirements.txt && \
    echo "python-jose[cryptography]==3.3.0" >> requirements.txt && \
    echo "python-multipart==0.0.6" >> requirements.txt && \
    echo "pydantic==2.5.0" >> requirements.txt

# Pre-download and build wheels
RUN pip wheel --wheel-dir /build/wheels -r requirements.txt

# Stage 2: Runtime stage
FROM python:3.11-slim as runtime

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PATH="/home/appuser/.local/bin:$PATH"

# Install only runtime dependencies (no build tools)
RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user first
RUN adduser --disabled-password --gecos '' appuser

# Create app directory with proper ownership
WORKDIR /app
RUN chown appuser:appuser /app

# Switch to non-root user
USER appuser

# Copy wheels and requirements from builder stage
COPY --from=builder --chown=appuser:appuser /build/wheels /tmp/wheels
COPY --from=builder --chown=appuser:appuser /build/requirements.txt /tmp/

# Install dependencies from pre-built wheels
RUN pip install --user --no-cache-dir --find-links /tmp/wheels -r /tmp/requirements.txt && \
    rm -rf /tmp/wheels /tmp/requirements.txt

# Copy scripts and application files with proper ownership
COPY --chown=appuser:appuser scripts/wait-for-services.py /app/wait-for-services.py
COPY --chown=appuser:appuser scripts/healthcheck.py /usr/local/bin/healthcheck.py
COPY --chown=appuser:appuser shared/ /app/shared/
COPY --chown=appuser:appuser services/auth-service/app/ /app/app/

# Make health check script executable
USER root
RUN chmod +x /usr/local/bin/healthcheck.py
USER appuser

# Expose port
EXPOSE 8001

# Health check using dedicated script
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD ["python3", "/usr/local/bin/healthcheck.py"]

# Run the application with TCP dependency waiting and multiple workers
CMD ["sh", "-c", "python3 /app/wait-for-services.py postgres:tcp://postgres:5432 redis:tcp://redis:6379 --timeout 60 --verbose && uvicorn app.main:app --host 0.0.0.0 --port 8001 --workers 2"]