FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements from parent directory
COPY ../../requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy only RAG API related files
COPY ../../rag_api.py .
COPY ../../src/llm_utils.py src/
COPY ../../src/config_utils.py src/
COPY ../../src/__init__.py src/
COPY ../../config/ config/

# Create empty __init__.py files
RUN touch src/__init__.py

# Expose port
EXPOSE 8000

# Run the RAG API
CMD ["python", "-m", "uvicorn", "rag_api:app", "--host", "0.0.0.0", "--port", "8000"]