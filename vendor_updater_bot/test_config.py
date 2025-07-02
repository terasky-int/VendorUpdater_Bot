#!/usr/bin/env python3
"""Test configuration loading for vendor_updater_bot"""

from src.llm_utils import load_config

def test_config():
    try:
        config = load_config()
        print("✅ Config loaded successfully")
        
        # Test key ingestion settings
        email_server = config.get("email", {}).get("imap_server", "Not found")
        print(f"📧 Email server: {email_server}")
        
        vector_store = config.get("vector_store", {}).get("collection_name", "Not found")
        print(f"🗄️ Vector store collection: {vector_store}")
        
        debug_enabled = config.get("debug", {}).get("enabled", "Not found")
        print(f"🐛 Debug enabled: {debug_enabled}")
        
        # Check that RAG settings are NOT present (moved to TeraskyRag)
        rag_settings = config.get("rag")
        if rag_settings:
            print("⚠️ WARNING: RAG settings found in ingestion config (should be in TeraskyRag)")
        else:
            print("✅ RAG settings correctly absent from ingestion config")
            
        return True
        
    except Exception as e:
        print(f"❌ Config loading failed: {e}")
        return False

if __name__ == "__main__":
    test_config()