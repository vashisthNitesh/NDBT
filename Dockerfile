# ==============================================================================
# Multi-Stage Dockerfile for NDBT Transport Portal (Vue 3 + Django + Gunicorn)
# Builds Vue 3 SPA frontend and runs Django backend together on a single port.
# Fully compatible with Render Web Services and standard Docker environments.
# ==============================================================================

# ------------------------------------------------------------------------------
# Stage 1: Build Vue 3 Single Page Application
# ------------------------------------------------------------------------------
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm install

COPY frontend/ ./
RUN npm run build

# ------------------------------------------------------------------------------
# Stage 2: Python Backend Runtime
# ------------------------------------------------------------------------------
FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

# Install required system dependencies (Postgres client libraries, curl, build essentials)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend codebase
COPY . ./

# Copy built Vue 3 static distribution from Stage 1
COPY --from=frontend-builder /app/frontend/dist /app/frontend/dist

# Collect static assets into staticfiles
RUN python manage.py collectstatic --noinput

# Expose container port
EXPOSE 8000

# Health check to ensure web server is responding
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:${PORT:-8000}/ || exit 1

# Launch Gunicorn dynamically bound to $PORT (set by Render, defaults to 8000)
CMD ["sh", "-c", "python manage.py migrate --noinput && gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 3 --timeout 120"]
