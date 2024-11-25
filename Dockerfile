FROM python:3.12-slim

# Create app user
RUN groupadd -r app && useradd -r -g app app

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libjpeg-dev \
    libpng-dev \
    zlib1g-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code first (as root)
COPY . .

# Initialize database and migrations as root
ENV FLASK_APP=/app/app
RUN mkdir -p /app/instance /app/migrations/versions && \
    touch /app/instance/app.db && \
    flask db init && \
    chown -R app:app /app && \
    chmod -R 777 /app && \
    chmod +x entrypoint.sh

# Set environment variables
ENV FLASK_ENV=production
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV INIT_DB=true

# Switch to non-root user
USER app

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["gunicorn", "-w", "4", "--timeout", "120", "--keep-alive", "5", "--max-requests", "1000", "--max-requests-jitter", "50", "-b", "0.0.0.0:8000", "app:create_app()"]
