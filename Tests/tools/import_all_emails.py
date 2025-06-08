"""
Script to import all emails from ChromaDB to Neo4j
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from graph_db import import_all_emails

if __name__ == "__main__":
    print("Importing all emails from ChromaDB to Neo4j...")
    success = import_all_emails()
    if success:
        print("✅ Import completed successfully")
    else:
        print("❌ Import failed")