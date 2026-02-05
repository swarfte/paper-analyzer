# Use Python 3.14 slim image as base
FROM python:3.14-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SECRET_KEY=build-time-secret-key-change-in-production \
    DJANGO_DEBUG=False \
    # Set uv cache directory
    UV_CACHE_DIR=/tmp/uv-cache

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml ./

# Install dependencies using uv
RUN uv sync --no-dev

# Copy project files
COPY . .

# Create directories for media and static files
RUN mkdir -p media staticfiles

# Expose port 8000
EXPOSE 8000

# Default command (will be overridden by docker-compose)
CMD ["sh", "-c", "uv run python setup.py && uv run gunicorn paper_analyzer.wsgi:application --bind 0.0.0.0:8000"]
