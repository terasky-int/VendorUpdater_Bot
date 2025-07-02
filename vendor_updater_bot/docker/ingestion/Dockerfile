FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY ../../requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY ../../src/ src/
COPY ../../config/ config/
COPY ../../main.py .
COPY ../../graph_db_consolidated.py .
COPY ../../*.py .

# Create necessary directories
RUN mkdir -p data/raw_emails data/clean_text data/eval logs

# Expose port for monitoring
EXPOSE 8080

# Default command
CMD ["python", "main.py", "--local", "--folder", "data/raw_emails"]