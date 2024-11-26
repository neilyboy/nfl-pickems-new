FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV FLASK_APP=app

# Create appuser
RUN groupadd -r appgroup && useradd -r -g appgroup appuser

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy entrypoint script first and set permissions
COPY entrypoint.sh /app/
RUN chmod +x /app/entrypoint.sh

# Copy project
COPY . .

# Create and set permissions for instance directory
RUN mkdir -p /app/instance && \
    mkdir -p /app/migrations/versions && \
    chown -R appuser:appgroup /app && \
    chmod -R 755 /app && \
    chmod 777 /app/instance && \
    chmod 777 /app/migrations/versions

# Set the user
USER appuser

# Run entrypoint script
ENTRYPOINT ["/app/entrypoint.sh"]
