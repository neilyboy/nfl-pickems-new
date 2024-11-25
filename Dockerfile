FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create app user and directories
RUN groupadd -r app && \
    useradd -r -g app -s /bin/bash -d /app app && \
    mkdir -p /app/instance /app/migrations/versions && \
    touch /app/instance/app.db && \
    chown -R app:app /app && \
    chmod -R 777 /app/instance && \
    chmod 666 /app/instance/app.db && \
    chmod -R 777 /app/migrations

# Copy application code
COPY . .
RUN chown -R app:app /app && \
    chmod +x /app/entrypoint.sh

# Set environment variables
ENV FLASK_APP=/app/app \
    FLASK_ENV=production \
    PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    DATABASE_URL=sqlite:////app/instance/app.db

# Switch to app user
USER app

# Expose port 8000
EXPOSE 8000

# Set entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]

# Default command
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "app:create_app()"]
