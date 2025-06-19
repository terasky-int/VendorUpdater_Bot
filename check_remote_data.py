#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.llm_utils import get_chroma_collection

def check_remote_data():
    """Check what data exists in remote ChromaDB"""
    try:
        collection = get_chroma_collection()
        
        print(f"Collection: {collection.name}")
        print(f"Total documents: {collection.count()}")
        
        # Get all unique vendors
        results = collection.get()
        vendors = set()
        types = set()
        
        if results['metadatas']:
            for metadata in results['metadatas']:
                if metadata.get('vendor'):
                    vendors.add(metadata['vendor'])
                if metadata.get('type'):
                    if isinstance(metadata['type'], list):
                        types.update(metadata['type'])
                    else:
                        types.add(metadata['type'])
        
        print(f"\nUnique vendors: {sorted(vendors)}")
        print(f"Unique types: {sorted(types)}")
        
        # Show recent documents
        print(f"\nAll document IDs:")
        for i, doc_id in enumerate(results['ids'][:10]):  # Show first 10
            metadata = results['metadatas'][i] if results['metadatas'] else {}
            print(f"  {doc_id} - {metadata.get('vendor', 'N/A')} - {metadata.get('date', 'N/A')}")
        
        if len(results['ids']) > 10:
            print(f"  ... and {len(results['ids']) - 10} more documents")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_remote_data()