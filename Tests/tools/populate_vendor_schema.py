"""
Populate vendor nodes with enhanced schema (domains and aliases)
"""

import os
import sys
import logging
import pandas as pd

# Add parent directories to path and change working directory
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.append(project_root)
os.chdir(project_root)

from py2neo import Graph

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def populate_vendor_schema(excel_file):
    """Populate Neo4j vendor nodes with enhanced schema"""
    try:
        # Connect to Neo4j
        graph = Graph("bolt://aipg.dudelabz.com:7687", auth=("neo4j", "ZZCrap123"))
        
        # Read enriched Excel file
        df = pd.read_excel(excel_file)
        logging.info(f"Loading {len(df)} vendors from {excel_file}")
        
        # Update each vendor node
        for _, row in df.iterrows():
            vendor_name = row['name']
            domains = str(row.get('associated_domains', '')) if pd.notna(row.get('associated_domains')) else ''
            aliases = str(row.get('aliases', '')) if pd.notna(row.get('aliases')) else ''
            description = str(row.get('description', '')) if pd.notna(row.get('description')) else ''
            
            # Update or create vendor node with enhanced properties
            query = """
            MERGE (v:Vendor {name: $name})
            SET v.description = $description,
                v.associated_domains = $domains,
                v.aliases = $aliases,
                v.source = 'enhanced_schema'
            RETURN v
            """
            
            result = graph.run(query, {
                'name': vendor_name,
                'description': description,
                'domains': domains,
                'aliases': aliases
            }).data()
            
            if result:
                logging.info(f"Updated vendor: {vendor_name}")
                if domains:
                    logging.info(f"  Domains: {domains}")
                if aliases:
                    logging.info(f"  Aliases: {aliases}")
            else:
                logging.warning(f"Failed to update vendor: {vendor_name}")
        
        # Verify the updates
        verify_query = """
        MATCH (v:Vendor)
        WHERE v.associated_domains IS NOT NULL AND v.associated_domains <> ''
        RETURN v.name AS name, v.associated_domains AS domains, v.aliases AS aliases
        ORDER BY v.name
        """
        
        results = graph.run(verify_query).data()
        
        print("\n=== Updated Vendors ===")
        for result in results:
            print(f"{result['name']}:")
            if result['domains']:
                print(f"  Domains: {result['domains']}")
            if result['aliases']:
                print(f"  Aliases: {result['aliases']}")
        
        logging.info(f"Successfully updated {len(results)} vendors with enhanced schema")
        return True
        
    except Exception as e:
        logging.error(f"Failed to populate vendor schema: {e}")
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Populate Neo4j with enhanced vendor schema")
    parser.add_argument("excel_file", help="Enriched Excel file path")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.excel_file):
        print(f"Error: Excel file not found: {args.excel_file}")
        exit(1)
    
    success = populate_vendor_schema(args.excel_file)
    
    if success:
        print("✅ Vendor schema populated successfully")
    else:
        print("❌ Failed to populate vendor schema")