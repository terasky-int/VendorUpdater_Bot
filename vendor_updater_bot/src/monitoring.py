"""
Monitoring and alerting for VendorUpdater_Bot
"""

import logging
import json
import time
import os
import platform
import psutil
from datetime import datetime

def log_metrics(pipeline_run, start_time, emails_processed=0, error=None):
    """
    Log metrics about pipeline execution
    
    Args:
        pipeline_run: Name or identifier for the pipeline run
        start_time: Start time of the pipeline (from time.time())
        emails_processed: Number of emails processed
        error: Error message if any
    """
    duration = time.time() - start_time
    success = error is None
    
    # Get system metrics
    system_metrics = {
        "cpu_percent": psutil.cpu_percent(),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage('/').percent if platform.system() != 'Windows' else psutil.disk_usage('C:\\').percent
    }
    
    metrics = {
        "timestamp": datetime.now().isoformat(),
        "pipeline": pipeline_run,
        "success": success,
        "duration_seconds": round(duration, 2),
        "emails_processed": emails_processed,
        "error": str(error) if error else None,
        "system": system_metrics
    }
    
    # Ensure logs directory exists
    os.makedirs("logs", exist_ok=True)
    
    # Write to metrics file
    with open("logs/metrics.jsonl", "a") as f:
        f.write(json.dumps(metrics) + "\n")
    
    # Log to console
    if success:
        logging.info(f"Pipeline completed in {duration:.2f}s, processed {emails_processed} emails")
    else:
        logging.error(f"Pipeline failed after {duration:.2f}s: {error}")
        
    return metrics

def check_health():
    """
    Check system health and component status
    
    Returns:
        Dict with health status information
    """
    try:
        # Check system resources
        system_metrics = {
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent if platform.system() != 'Windows' else psutil.disk_usage('C:\\').percent
        }
        
        # Check ChromaDB
        chromadb_status = "unknown"
        doc_count = 0
        try:
            from src import llm_utils
            collection = llm_utils.get_chroma_collection()
            doc_count = collection.count()
            chromadb_status = "healthy"
        except Exception as e:
            chromadb_status = f"error: {str(e)}"
        
        # Check Neo4j if available
        neo4j_status = "unknown"
        try:
            from graph_db import connect_to_graph
            graph = connect_to_graph()
            if graph:
                neo4j_status = "connected"
            else:
                neo4j_status = "failed to connect"
        except Exception as e:
            neo4j_status = f"error: {str(e)}"
        
        # Check AWS credentials
        aws_status = "unknown"
        try:
            import boto3
            sts = boto3.client('sts')
            sts.get_caller_identity()
            aws_status = "authenticated"
        except Exception as e:
            aws_status = f"error: {str(e)}"
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "system": system_metrics,
            "components": {
                "chromadb": {
                    "status": chromadb_status,
                    "document_count": doc_count
                },
                "neo4j": {
                    "status": neo4j_status
                },
                "aws": {
                    "status": aws_status
                }
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }

def alert(message, level="error"):
    """
    Send an alert
    
    Args:
        message: Alert message
        level: Alert level (info, warning, error, critical)
    """
    # Log the alert
    if level == "info":
        logging.info(f"ALERT: {message}")
    elif level == "warning":
        logging.warning(f"ALERT: {message}")
    elif level == "error":
        logging.error(f"ALERT: {message}")
    elif level == "critical":
        logging.critical(f"ALERT: {message}")
    
    # Ensure logs directory exists
    os.makedirs("logs", exist_ok=True)
    
    # Write to alerts file
    with open("logs/alerts.jsonl", "a") as f:
        alert_data = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "message": message
        }
        f.write(json.dumps(alert_data) + "\n")
    
    # TODO: Implement external alerting (email, Slack, etc.)
    # For now, just log to console and file

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    
    # Check health
    health = check_health()
    print(json.dumps(health, indent=2))
    
    # Test alert
    alert("This is a test alert", "info")