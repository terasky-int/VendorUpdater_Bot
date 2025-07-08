FROM python:3.10-slim

WORKDIR /app

# Install system dependencies for email processing
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create directory structure and __init__.py files
RUN mkdir -p src tests misc/tst_emls && \
    touch src/__init__.py tests/__init__.py

# Copy application code
COPY src/ src/
COPY tests/ tests/
COPY config/ config/
COPY misc/ misc/
COPY main.py .
COPY test_config.py .
COPY test_docker.py .

# Create necessary directories
RUN mkdir -p data/raw_emails data/clean_text data/eval logs

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Run the ingestion pipeline
CMD ["python", "main.py", "--local", "--folder", "misc/tst_emls"]