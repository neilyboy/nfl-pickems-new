FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create instance directory with proper permissions
RUN mkdir -p instance && chmod 777 instance

# Create migrations directory with proper permissions
RUN mkdir -p migrations && chmod 777 migrations

# Set environment variables
ENV FLASK_APP=app
ENV FLASK_ENV=production
ENV PYTHONPATH=/app

# The entrypoint script will be used to run the application
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "app:create_app()"]
