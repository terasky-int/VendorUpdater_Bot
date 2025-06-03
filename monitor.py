import time
import json
import logging
import os
from datetime import datetime

def log_metrics(success, start_time, error=None, processed_count=0, details=None):
    """
    Log metrics about pipeline execution
    
    Args:
        success: Whether the pipeline run was successful
        start_time: Start time of the pipeline (from time.time())
        error: Error message if any
        processed_count: Number of emails processed
        details: Additional details to log
    """
    duration = time.time() - start_time
    
    metrics = {
        "timestamp": datetime.now().isoformat(),
        "success": success,
        "duration_seconds": round(duration, 2),
        "emails_processed": processed_count,
        "error": error
    }
    
    if details:
        metrics.update(details)
    
    # Ensure logs directory exists
    os.makedirs("logs", exist_ok=True)
    
    # Write to metrics file
    with open("logs/metrics.jsonl", "a") as f:
        f.write(json.dumps(metrics) + "\n")
    
    # Log to console
    if success:
        logging.info(f"Pipeline completed in {duration:.2f}s, processed {processed_count} emails")
    else:
        logging.critical(f"Pipeline failed after {duration:.2f}s: {error}")

def get_system_metrics():
    """Get basic system metrics"""
    import psutil
    
    return {
        "cpu_percent": psutil.cpu_percent(),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage('/').percent
    }

def check_health():
    """Check system health and ChromaDB status"""
    from src import llm_utils
    
    try:
        # Check ChromaDB
        collection = llm_utils.get_chroma_collection()
        doc_count = collection.count()
        
        # Get system metrics
        system_metrics = get_system_metrics()
        
        return {
            "status": "healthy",
            "document_count": doc_count,
            "system": system_metrics,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    
    # Run health check
    health = check_health()
    print(json.dumps(health, indent=2))