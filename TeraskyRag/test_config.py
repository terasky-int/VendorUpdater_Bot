#!/usr/bin/env python3
"""Test configuration loading for TeraskyRag"""

from src.llm_utils import load_config

def test_config():
    try:
        config = load_config()
        print("✅ Config loaded successfully")
        
        # Test key RAG settings
        vector_store = config.get("vector_store", {}).get("collection_name", "Not found")
        print(f"🗄️ Vector store collection: {vector_store}")
        
        neo4j_uri = config.get("neo4j", {}).get("uri", "Not found")
        print(f"📊 Neo4j URI: {neo4j_uri}")
        
        rag_model = config.get("rag", {}).get("answer_model", "Not found")
        print(f"🤖 RAG answer model: {rag_model}")
        
        bedrock_region = config.get("bedrock", {}).get("region", "Not found")
        print(f"☁️ Bedrock region: {bedrock_region}")
        
        # Check that email settings are NOT present (moved to vendor_updater_bot)
        email_settings = config.get("email")
        if email_settings:
            print("⚠️ WARNING: Email settings found in RAG config (should be in vendor_updater_bot)")
        else:
            print("✅ Email settings correctly absent from RAG config")
            
        return True
        
    except Exception as e:
        print(f"❌ Config loading failed: {e}")
        return False

if __name__ == "__main__":
    test_config()