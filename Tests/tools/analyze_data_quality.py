"""
Analyze data quality in ChromaDB and Neo4j to identify potential issues
"""

import os
import sys
import logging
from collections import Counter
from datetime import datetime

# Add the parent directory to the path so we can import modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Import required modules
from src import llm_utils
from graph_db_consolidated import connect_to_graph, run_graph_query

def analyze_chroma_data():
    """Analyze ChromaDB data quality"""
    try:
        # Connect to ChromaDB
        collection = llm_utils.get_chroma_collection()
        logging.info(f"Connected to ChromaDB collection: {collection.name}")
        
        # Get all data
        all_data = collection.get()
        
        # Check for missing metadata fields
        missing_fields = {
            "vendor": 0,
            "product": 0,
            "type": 0,
            "date": 0,
            "email_id": 0
        }
        
        for meta in all_data["metadatas"]:
            for field in missing_fields:
                if field not in meta or not meta[field] or meta[field] == "unknown":
                    missing_fields[field] += 1
        
        # Check for duplicate email_ids
        email_ids = [meta.get("email_id") for meta in all_data["metadatas"] if "email_id" in meta]
        email_id_counts = Counter(email_ids)
        duplicate_email_ids = {email_id: count for email_id, count in email_id_counts.items() if count > 1}
        
        # Check for empty documents
        empty_docs = sum(1 for doc in all_data["documents"] if not doc or len(doc.strip()) < 10)
        
        # Check for inconsistent metadata within same email_id
        inconsistent_metadata = {}
        email_metadata = {}
        
        for i, meta in enumerate(all_data["metadatas"]):
            email_id = meta.get("email_id")
            if not email_id:
                continue
                
            if email_id not in email_metadata:
                email_metadata[email_id] = {
                    "vendor": set(),
                    "product": set(),
                    "type": set(),
                    "date": set()
                }
            
            # Add values to sets
            for field in ["vendor", "type", "date"]:
                if field in meta and meta[field]:
                    email_metadata[email_id][field].add(meta[field])
            
            # Handle product field which might be comma-separated
            if "product" in meta and meta["product"]:
                if isinstance(meta["product"], str) and "," in meta["product"]:
                    for p in meta["product"].split(","):
                        email_metadata[email_id]["product"].add(p.strip())
                else:
                    email_metadata[email_id]["product"].add(meta["product"])
        
        # Find inconsistencies
        for email_id, fields in email_metadata.items():
            inconsistent = {}
            for field, values in fields.items():
                if len(values) > 1 and field != "product":  # Products can be multiple
                    inconsistent[field] = list(values)
            
            if inconsistent:
                inconsistent_metadata[email_id] = inconsistent
        
        # Print results
        print("\n=== ChromaDB Data Quality Analysis ===")
        print(f"Total documents: {len(all_data['documents'])}")
        
        print("\nMissing metadata fields:")
        for field, count in missing_fields.items():
            percentage = (count / len(all_data["metadatas"])) * 100 if all_data["metadatas"] else 0
            print(f"- {field}: {count} ({percentage:.1f}%)")
        
        print("\nEmpty or very short documents:")
        percentage = (empty_docs / len(all_data["documents"])) * 100 if all_data["documents"] else 0
        print(f"- Count: {empty_docs} ({percentage:.1f}%)")
        
        print("\nDuplicate email_ids:")
        if duplicate_email_ids:
            for email_id, count in duplicate_email_ids.items():
                print(f"- {email_id}: {count} occurrences")
        else:
            print("- None found")
        
        print("\nInconsistent metadata within same email_id:")
        if inconsistent_metadata:
            for email_id, fields in inconsistent_metadata.items():
                print(f"- {email_id}:")
                for field, values in fields.items():
                    print(f"  - {field}: {values}")
        else:
            print("- None found")
        
        return {
            "total_documents": len(all_data["documents"]),
            "missing_fields": missing_fields,
            "empty_docs": empty_docs,
            "duplicate_email_ids": duplicate_email_ids,
            "inconsistent_metadata": inconsistent_metadata
        }
    
    except Exception as e:
        logging.error(f"Error analyzing ChromaDB data: {e}")
        return None

def analyze_neo4j_data():
    """Analyze Neo4j data quality"""
    try:
        # Connect to Neo4j
        graph = connect_to_graph()
        if not graph:
            logging.error("Failed to connect to Neo4j")
            return None
        
        # Check for orphaned nodes (no relationships)
        orphaned_query = """
        MATCH (n)
        WHERE NOT (n)--()
        RETURN labels(n) AS type, count(n) AS count
        """
        orphaned_result = run_graph_query(orphaned_query)
        
        # Check for emails without vendor
        no_vendor_query = """
        MATCH (e:Email)
        WHERE NOT (e)-[:FROM]->(:Vendor)
        RETURN count(e) AS count
        """
        no_vendor_result = run_graph_query(no_vendor_query)
        
        # Check for emails without product
        no_product_query = """
        MATCH (e:Email)
        WHERE NOT (e)-[:ABOUT]->(:Product)
        RETURN count(e) AS count
        """
        no_product_result = run_graph_query(no_product_query)
        
        # Check for vendors without products
        vendors_no_products_query = """
        MATCH (v:Vendor)
        WHERE NOT (v)-[:OFFERS]->(:Product)
        RETURN v.name AS vendor
        """
        vendors_no_products_result = run_graph_query(vendors_no_products_query)
        
        # Check for products without vendors
        products_no_vendors_query = """
        MATCH (p:Product)
        WHERE NOT (p)<-[:OFFERS]-(:Vendor)
        RETURN p.name AS product
        """
        products_no_vendors_result = run_graph_query(products_no_vendors_query)
        
        # Print results
        print("\n=== Neo4j Data Quality Analysis ===")
        
        print("\nOrphaned nodes (no relationships):")
        if orphaned_result:
            for result in orphaned_result:
                print(f"- {', '.join(result['type'])}: {result['count']}")
        else:
            print("- None found")
        
        print("\nEmails without vendor:")
        if no_vendor_result:
            print(f"- Count: {no_vendor_result[0]['count']}")
        else:
            print("- None found")
        
        print("\nEmails without product:")
        if no_product_result:
            print(f"- Count: {no_product_result[0]['count']}")
        else:
            print("- None found")
        
        print("\nVendors without products:")
        if vendors_no_products_result:
            for result in vendors_no_products_result:
                print(f"- {result['vendor']}")
        else:
            print("- None found")
        
        print("\nProducts without vendors:")
        if products_no_vendors_result:
            for result in products_no_vendors_result:
                print(f"- {result['product']}")
        else:
            print("- None found")
        
        return {
            "orphaned_nodes": orphaned_result,
            "emails_without_vendor": no_vendor_result[0]['count'] if no_vendor_result else 0,
            "emails_without_product": no_product_result[0]['count'] if no_product_result else 0,
            "vendors_without_products": [r['vendor'] for r in vendors_no_products_result] if vendors_no_products_result else [],
            "products_without_vendors": [r['product'] for r in products_no_vendors_result] if products_no_vendors_result else []
        }
    
    except Exception as e:
        logging.error(f"Error analyzing Neo4j data: {e}")
        return None

def check_data_consistency():
    """Check consistency between ChromaDB and Neo4j"""
    try:
        # Connect to ChromaDB
        collection = llm_utils.get_chroma_collection()
        all_data = collection.get()
        
        # Get email IDs from ChromaDB
        chroma_email_ids = set()
        for meta in all_data["metadatas"]:
            if "email_id" in meta and meta["email_id"]:
                chroma_email_ids.add(meta["email_id"])
        
        # Get email IDs from Neo4j
        email_query = """
        MATCH (e:Email)
        RETURN e.id AS email_id
        """
        email_result = run_graph_query(email_query)
        neo4j_email_ids = set(r["email_id"] for r in email_result) if email_result else set()
        
        # Find differences
        only_in_chroma = chroma_email_ids - neo4j_email_ids
        only_in_neo4j = neo4j_email_ids - chroma_email_ids
        
        # Print results
        print("\n=== Data Consistency Check ===")
        print(f"Emails in ChromaDB: {len(chroma_email_ids)}")
        print(f"Emails in Neo4j: {len(neo4j_email_ids)}")
        
        print("\nEmails only in ChromaDB:")
        if only_in_chroma:
            for email_id in only_in_chroma:
                print(f"- {email_id}")
        else:
            print("- None found")
        
        print("\nEmails only in Neo4j:")
        if only_in_neo4j:
            for email_id in only_in_neo4j:
                print(f"- {email_id}")
        else:
            print("- None found")
        
        return {
            "chroma_email_count": len(chroma_email_ids),
            "neo4j_email_count": len(neo4j_email_ids),
            "only_in_chroma": list(only_in_chroma),
            "only_in_neo4j": list(only_in_neo4j)
        }
    
    except Exception as e:
        logging.error(f"Error checking data consistency: {e}")
        return None

if __name__ == "__main__":
    logging.info("Starting data quality analysis")
    
    # Analyze ChromaDB data
    chroma_analysis = analyze_chroma_data()
    
    # Analyze Neo4j data
    neo4j_analysis = analyze_neo4j_data()
    
    # Check data consistency
    consistency_check = check_data_consistency()
    
    logging.info("Data quality analysis complete")