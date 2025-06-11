"""
Configuration utilities for VendorUpdater_Bot
"""

import os
import logging

def get_neo4j_config():
    """
    Get Neo4j configuration from environment variables
    
    Returns:
        Dict with Neo4j connection parameters
    """
    # Default values
    default_uri = "bolt://localhost:7687"
    default_user = "neo4j"
    default_password = "password"
    
    # Get values from environment variables
    uri = os.environ.get("NEO4J_URI", default_uri)
    user = os.environ.get("NEO4J_USER", default_user)
    password = os.environ.get("NEO4J_PASSWORD", default_password)
    
    logging.debug(f"Using Neo4j configuration: URI={uri}, USER={user}")
    
    return {
        "uri": uri,
        "user": user,
        "password": password
    }