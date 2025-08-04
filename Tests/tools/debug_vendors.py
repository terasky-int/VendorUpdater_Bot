"""
Debug script to see what vendors are actually in ChromaDB
"""

import os
import sys
from collections import Counter

# Add parent directories to path and change working directory
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.append(project_root)
os.chdir(project_root)

from src import llm_utils

def debug_vendors():
    collection = llm_utils.get_chroma_collection()
    all_data = collection.get()
    
    vendors = []
    for metadata in all_data["metadatas"]:
        vendor = metadata.get('vendor', '').strip()
        if vendor:
            vendors.append(vendor)
    
    vendor_counts = Counter(vendors)
    
    print("=== Vendors in ChromaDB ===")
    for vendor, count in vendor_counts.most_common():
        print(f"{vendor}: {count} emails")
    
    print(f"\nTotal unique vendors: {len(vendor_counts)}")
    print(f"Total emails: {len(vendors)}")

if __name__ == "__main__":
    debug_vendors()