FROM python:3.12-slim

# Install system dependencies including sudo
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    sudo \
    && rm -rf /var/lib/apt/lists/*

# Create app directory and set up app user
RUN mkdir -p /app && \
    groupadd -r app && \
    useradd -r -g app -s /bin/bash -d /app app && \
    chown -R app:app /app

# Allow app user to use sudo for specific commands without password
RUN echo "app ALL=(ALL) NOPASSWD: /usr/local/bin/flask" >> /etc/sudoers

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set permissions
RUN chown -R app:app /app && \
    chmod +x /app/entrypoint.sh

# Set environment variables
ENV FLASK_APP=/app/app \
    FLASK_ENV=production \
    PYTHONPATH=/app \
    PYTHONUNBUFFERED=1

# Switch to app user
USER app

# Set entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]

# Default command
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:create_app()"]
