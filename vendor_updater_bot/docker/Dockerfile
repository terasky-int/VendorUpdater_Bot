FROM python:3.10-slim

WORKDIR /app

# Install system dependencies for email processing
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN cat requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ src/
COPY main.py .
COPY config/ config/

# Create necessary directories
RUN mkdir -p data/raw_emails data/clean_text data/eval logs

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Run the ingestion pipeline
CMD ["python", "main.py", "--local", "--folder", "/data/emails"]