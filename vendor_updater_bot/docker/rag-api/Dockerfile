FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY Docker/rag-api/requirements-rag.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Create src directory and __init__.py
RUN mkdir -p src && touch src/__init__.py

# Copy only RAG API related files
COPY rag_api.py .
COPY src/llm_utils.py src/
COPY src/config_utils.py src/
COPY config/ config/

# Expose port
EXPOSE 8001

# Run the RAG API
CMD ["python", "-m", "uvicorn", "rag_api:app", "--host", "0.0.0.0", "--port", "8001"]