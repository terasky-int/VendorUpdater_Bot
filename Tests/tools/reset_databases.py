#!/usr/bin/env python3
"""
Database Reset Tool - Clears ChromaDB collections and Neo4j database
"""

import os
import sys
import yaml
import chromadb

try:
    from py2neo import Graph
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False

def load_config():
    """Load configuration from config.yaml"""
    config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'config.yaml')
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def reset_chromadb(config):
    """Reset ChromaDB collections"""
    print("Resetting ChromaDB...")
    
    vector_config = config['vector_store']
    
    if vector_config.get('use_remote', False):
        # Remote ChromaDB
        client = chromadb.HttpClient(
            host=vector_config['remote_host'],
            port=vector_config['remote_port']
        )
    else:
        # Local ChromaDB
        client = chromadb.PersistentClient(path=vector_config['persist_directory'])
    
    # Delete all collections
    collections = client.list_collections()
    for collection in collections:
        client.delete_collection(collection.name)
        print(f"Deleted collection: {collection.name}")
    
    print(f"ChromaDB reset complete. Deleted {len(collections)} collections.")

def reset_neo4j(config):
    """Reset Neo4j database"""
    if not NEO4J_AVAILABLE:
        print("py2neo not available (should be installed from requirements.txt)")
        return
        
    print("Resetting Neo4j...")
    
    # Handle malformed YAML config with = instead of :
    uri = 'bolt://aipg.dudelabz.com:7687'
    user = 'neo4j'
    password = os.getenv('NEO4J_PASSWORD')
    
    if not password:
        print("Error: NEO4J_PASSWORD environment variable not set")
        return
    
    graph = Graph(uri, auth=(user, password))
    
    # Delete all nodes and relationships
    graph.run("MATCH (n) DETACH DELETE n")
    print("Deleted all nodes and relationships")
    
    # Get count to verify
    result = graph.run("MATCH (n) RETURN count(n) as count")
    count = result.evaluate()
    print(f"Neo4j reset complete. Remaining nodes: {count}")

def main():
    """Main function"""
    try:
        config = load_config()
        
        print("=== Database Reset Tool ===")
        print("This will delete ALL data from ChromaDB and Neo4j")
        
        confirm = input("Are you sure? (yes/no): ").lower()
        if confirm != 'yes':
            print("Reset cancelled.")
            return
        
        reset_chromadb(config)
        reset_neo4j(config)
        
        print("\n=== Reset Complete ===")
        print("All databases have been cleared.")
        
    except Exception as e:
        print(f"Error during reset: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()