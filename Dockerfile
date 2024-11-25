FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Create app user and group
RUN groupadd -r appgroup && \
    useradd -r -g appgroup -d /app appuser && \
    mkdir -p /app/instance && \
    mkdir -p /app/migrations/versions && \
    chown -R appuser:appgroup /app && \
    chmod -R 755 /app && \
    chmod 777 /app/instance

# Copy requirements and install dependencies
COPY --chown=appuser:appgroup requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY --chown=appuser:appgroup . .
RUN chmod +x /app/entrypoint.sh

# Set environment variables
ENV FLASK_APP=/app/app \
    FLASK_ENV=production \
    PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    DATABASE_URL=sqlite:////app/instance/app.db \
    DATABASE_DIR=/app/instance

# Switch to app user
USER appuser

# Expose port
EXPOSE 8000

# Set entrypoint and command
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "app:create_app()"]
