"""
Export data from ChromaDB and Neo4j to CSV files for easy inspection
"""

import os
import sys
import csv
import json
import logging
from datetime import datetime

# Add the parent directory to the path so we can import modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Import required modules
from src import llm_utils
from graph_db_consolidated import connect_to_graph, run_graph_query

def export_chroma_data(output_dir="exports"):
    """Export ChromaDB data to CSV"""
    try:
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Get current timestamp for filenames
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Connect to ChromaDB
        collection = llm_utils.get_chroma_collection()
        logging.info(f"Connected to ChromaDB collection: {collection.name}")
        
        # Get all data (without embeddings)
        all_data = collection.get()
        
        # Export metadata to CSV
        csv_path = os.path.join(output_dir, f"chroma_metadata_{timestamp}.csv")
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            if all_data["metadatas"]:
                # Get all possible keys from all metadata dictionaries
                fieldnames = set()
                for meta in all_data["metadatas"]:
                    fieldnames.update(meta.keys())
                fieldnames = ["id"] + sorted(list(fieldnames))  # Add ID field first
                
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                # Write each row
                for i, meta in enumerate(all_data["metadatas"]):
                    row = meta.copy()  # Copy metadata
                    row["id"] = all_data["ids"][i]  # Add ID
                    writer.writerow(row)
        
        # Export documents to a separate file (first 200 chars only)
        docs_path = os.path.join(output_dir, f"chroma_documents_{timestamp}.csv")
        with open(docs_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["id", "document_preview"])
            
            for i, doc in enumerate(all_data["documents"]):
                preview = doc[:200] + "..." if len(doc) > 200 else doc
                writer.writerow([all_data["ids"][i], preview])
        
        logging.info(f"Exported {len(all_data['ids'])} ChromaDB records to {csv_path} and {docs_path}")
        return csv_path, docs_path
    
    except Exception as e:
        logging.error(f"Error exporting ChromaDB data: {e}")
        return None, None

def export_neo4j_data(output_dir="exports"):
    """Export Neo4j data to CSV"""
    try:
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Get current timestamp for filenames
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Connect to Neo4j
        graph = connect_to_graph()
        if not graph:
            logging.error("Failed to connect to Neo4j")
            return None
        
        # Export nodes
        nodes_path = os.path.join(output_dir, f"neo4j_nodes_{timestamp}.csv")
        
        # Get all nodes
        nodes_query = """
        MATCH (n)
        RETURN labels(n) AS labels, n AS properties
        """
        nodes_result = run_graph_query(nodes_query)
        
        if nodes_result:
            with open(nodes_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["node_type", "properties"])
                
                for node in nodes_result:
                    # Convert node labels to string
                    node_type = ", ".join(node["labels"])
                    # Convert properties to JSON string
                    props_json = json.dumps(node["properties"])
                    writer.writerow([node_type, props_json])
        
        # Export relationships
        rels_path = os.path.join(output_dir, f"neo4j_relationships_{timestamp}.csv")
        
        # Get all relationships
        rels_query = """
        MATCH (a)-[r]->(b)
        RETURN type(r) AS type, 
               labels(a)[0] AS source_type, 
               CASE 
                 WHEN labels(a)[0] = 'Vendor' THEN a.name
                 WHEN labels(a)[0] = 'Product' THEN a.name
                 WHEN labels(a)[0] = 'Email' THEN a.id
                 ELSE 'unknown'
               END AS source_name,
               labels(b)[0] AS target_type, 
               CASE 
                 WHEN labels(b)[0] = 'Vendor' THEN b.name
                 WHEN labels(b)[0] = 'Product' THEN b.name
                 WHEN labels(b)[0] = 'Email' THEN b.id
                 ELSE 'unknown'
               END AS target_name,
               properties(r) AS properties
        """
        rels_result = run_graph_query(rels_query)
        
        if rels_result:
            with open(rels_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["relationship_type", "source_type", "source_name", "target_type", "target_name", "properties"])
                
                for rel in rels_result:
                    # Convert properties to JSON string
                    props_json = json.dumps(rel["properties"])
                    writer.writerow([
                        rel["type"], 
                        rel["source_type"], 
                        rel["source_name"], 
                        rel["target_type"], 
                        rel["target_name"],
                        props_json
                    ])
        
        logging.info(f"Exported Neo4j data: {len(nodes_result) if nodes_result else 0} nodes and {len(rels_result) if rels_result else 0} relationships")
        return nodes_path, rels_path
    
    except Exception as e:
        logging.error(f"Error exporting Neo4j data: {e}")
        return None, None

def export_summary():
    """Export summary statistics"""
    try:
        # Create output directory if it doesn't exist
        output_dir = "exports"
        os.makedirs(output_dir, exist_ok=True)
        
        # Get current timestamp for filenames
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        summary_path = os.path.join(output_dir, f"data_summary_{timestamp}.txt")
        
        with open(summary_path, 'w', encoding='utf-8') as f:
            # ChromaDB summary
            collection = llm_utils.get_chroma_collection()
            count = collection.count()
            f.write(f"ChromaDB Summary:\n")
            f.write(f"- Collection name: {collection.name}\n")
            f.write(f"- Document count: {count}\n\n")
            
            # Get unique metadata values
            if count > 0:
                all_data = collection.get()
                # Extract unique vendors
                vendors = set(m.get("vendor", "unknown") for m in all_data["metadatas"])
                
                # Extract unique products - handle comma-separated values
                products = set()
                for m in all_data["metadatas"]:
                    product_value = m.get("product", "unknown")
                    if isinstance(product_value, str) and "," in product_value:
                        for p in product_value.split(","):
                            products.add(p.strip())
                    else:
                        products.add(product_value)
                
                # Extract unique types - handle comma-separated values
                types = set()
                for m in all_data["metadatas"]:
                    type_value = m.get("type", "unknown")
                    if isinstance(type_value, str) and "," in type_value:
                        for t in type_value.split(","):
                            types.add(t.strip())
                    else:
                        types.add(type_value)
                
                f.write(f"- Unique vendors: {len(vendors)}\n")
                f.write("  " + ", ".join(sorted(vendors)) + "\n\n")
                
                f.write(f"- Unique products: {len(products)}\n")
                f.write("  " + ", ".join(sorted(products)) + "\n\n")
                
                f.write(f"- Unique types: {len(types)}\n")
                f.write("  " + ", ".join(sorted(types)) + "\n\n")
            
            # Neo4j summary
            f.write(f"Neo4j Summary:\n")
            
            # Get node counts by type
            nodes_query = """
            MATCH (n)
            WITH labels(n) AS label, count(n) AS count
            RETURN label, count
            ORDER BY count DESC
            """
            nodes_result = run_graph_query(nodes_query)
            
            if nodes_result:
                f.write("- Node counts:\n")
                for item in nodes_result:
                    f.write(f"  {', '.join(item['label'])}: {item['count']}\n")
                f.write("\n")
            
            # Get relationship counts by type
            rels_query = """
            MATCH ()-[r]->()
            WITH type(r) AS relationship_type, count(r) AS count
            RETURN relationship_type, count
            ORDER BY count DESC
            """
            rels_result = run_graph_query(rels_query)
            
            if rels_result:
                f.write("- Relationship counts:\n")
                for item in rels_result:
                    f.write(f"  {item['relationship_type']}: {item['count']}\n")
        
        logging.info(f"Exported data summary to {summary_path}")
        return summary_path
    
    except Exception as e:
        logging.error(f"Error exporting summary: {e}")
        return None

if __name__ == "__main__":
    logging.info("Starting data export")
    
    # Export ChromaDB data
    chroma_meta_path, chroma_docs_path = export_chroma_data()
    
    # Export Neo4j data
    neo4j_nodes_path, neo4j_rels_path = export_neo4j_data()
    
    # Export summary
    summary_path = export_summary()
    
    logging.info("Data export complete")
    logging.info(f"Files exported:")
    if chroma_meta_path:
        logging.info(f"- ChromaDB metadata: {chroma_meta_path}")
    if chroma_docs_path:
        logging.info(f"- ChromaDB documents: {chroma_docs_path}")
    if neo4j_nodes_path:
        logging.info(f"- Neo4j nodes: {neo4j_nodes_path}")
    if neo4j_rels_path:
        logging.info(f"- Neo4j relationships: {neo4j_rels_path}")
    if summary_path:
        logging.info(f"- Summary: {summary_path}")