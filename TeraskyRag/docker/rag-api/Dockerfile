FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create directory structure
RUN mkdir -p src api graph && touch src/__init__.py api/__init__.py graph/__init__.py

# Copy application files
COPY src/ src/
COPY api/ api/
COPY graph/ graph/
COPY config/ config/

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8000

# Run the RAG API
CMD ["python", "-m", "uvicorn", "api.rag_api:app", "--host", "0.0.0.0", "--port", "8000"]