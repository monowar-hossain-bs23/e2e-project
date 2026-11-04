# syntax=docker/dockerfile:1
FROM python:3.12-slim

# Prevent Python from writing .pyc files and buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1

WORKDIR /app

# Install basic system utilities
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry (v2.x to match poetry.lock)
RUN pip install --no-cache-dir "poetry>=2.0.0,<3.0.0"

# Copy dependency files first to leverage Docker layer caching
COPY pyproject.toml poetry.lock ./

# Install all dependencies (including dev dependencies for testing)
RUN poetry install --no-root

# Copy application source code
COPY . .

# Expose web port internally
EXPOSE 8000

# Run migrations and start Django development server by default
CMD ["sh", "-c", "python manage.py migrate && python manage.py runserver 0.0.0.0:8000"]
