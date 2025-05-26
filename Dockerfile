FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create assets directory and set permissions
RUN mkdir -p assets/images && \
    chmod -R 755 assets/

# Create non-root user for security
RUN useradd -m -u 1000 hippo && \
    chown -R hippo:hippo /app

USER hippo

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sqlite3; sqlite3.connect('hippo.db').close()" || exit 1

# Run the application
CMD ["python", "main.py"]