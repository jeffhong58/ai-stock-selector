# data_collector/Dockerfile
# AI Stock Selector Data Collector Dockerfile

# Use Python 3.11 slim image for better performance
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    libpq-dev \
    curl \
    cron \
    && rm -rf /var/lib/apt/lists/*

# Create app user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Copy backend shared modules
COPY ../backend/app /app/backend_app

# Create necessary directories
RUN mkdir -p /app/logs /app/data

# Set permissions
RUN chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=60s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://backend:8000/health', timeout=10)" || exit 1

# Default command
CMD ["python", "-m", "data_collector.schedulers.scheduled_tasks"]