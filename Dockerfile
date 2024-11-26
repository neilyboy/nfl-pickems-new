FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV FLASK_APP=app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy entrypoint script first and set permissions
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

# Copy project
COPY . .

# Create directories and set permissions
RUN mkdir -p /app/instance && \
    mkdir -p /app/migrations/versions && \
    chmod -R 777 /app/instance && \
    chmod -R 777 /app/migrations

# Create appuser for running the application
RUN groupadd -r appgroup && useradd -r -g appgroup appuser && \
    chown -R appuser:appgroup /app

# Switch to appuser
USER appuser

# Run entrypoint script
ENTRYPOINT ["./entrypoint.sh"]
