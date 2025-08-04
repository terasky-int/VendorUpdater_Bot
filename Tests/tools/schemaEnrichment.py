"""
Schema Enrichment Tool - Automatically enrich vendor Excel with domains and aliases
"""

import os
import sys
import pandas as pd
import logging
from collections import defaultdict, Counter
import re
from email.utils import parseaddr

# Store original working directory before changing
original_cwd = os.getcwd()

# Add parent directories to path and change working directory
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.append(project_root)
os.chdir(project_root)  # Change to project root for config access

from src import llm_utils
from graph_db_consolidated import connect_to_graph, run_graph_query

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class SchemaEnricher:
    def __init__(self):
        self.chroma_collection = llm_utils.get_chroma_collection()
        # Hardcoded Neo4j connection for testing
        try:
            from py2neo import Graph
            self.graph = Graph("bolt://aipg.dudelabz.com:7687", auth=("neo4j", "ZZCrap123"))
            # Test connection
            self.graph.run("RETURN 1 AS test").data()
            logging.info("Connected to Neo4j successfully")
        except Exception as e:
            logging.warning(f"Neo4j connection failed: {e}")
            self.graph = None
        
    def extract_domain_from_email(self, email_str):
        """Extract domain from email address"""
        try:
            _, email = parseaddr(email_str)
            if '@' in email:
                return email.split('@')[1].lower()
        except:
            pass
        return None
    
    def get_email_data(self):
        """Get email data from Neo4j or ChromaDB fallback"""
        # Try Neo4j first
        if self.graph:
            try:
                query = """
                MATCH (e:VendorEmail)-[:SENT_BY]->(v:Vendor)
                RETURN e.vendor AS detected_vendor, v.name AS actual_vendor, 
                       e.sender AS sender, e.id AS email_id
                """
                
                results = self.graph.run(query).data()
                if results:
                    emails = []
                    for result in results:
                        email_data = {
                            'vendor': result['actual_vendor'].lower(),
                            'detected_vendor': result['detected_vendor'],
                            'sender': result['sender'],
                            'email_id': result['email_id']
                        }
                        emails.append(email_data)
                    
                    logging.info(f"Retrieved {len(emails)} emails from Neo4j")
                    return emails
            except Exception as e:
                logging.warning(f"Neo4j query failed, falling back to ChromaDB: {e}")
        
        # Fallback to ChromaDB
        try:
            all_data = self.chroma_collection.get()
            emails = []
            
            for i, metadata in enumerate(all_data["metadatas"]):
                email_data = {
                    'vendor': metadata.get('vendor', '').lower(),
                    'detected_vendor': metadata.get('vendor', ''),
                    'sender': metadata.get('sender', ''),
                    'email_id': metadata.get('email_id', ''),
                    'text': all_data["documents"][i] if i < len(all_data["documents"]) else ''
                }
                emails.append(email_data)
            
            logging.info(f"Retrieved {len(emails)} emails from ChromaDB")
            return emails
        except Exception as e:
            logging.error(f"Failed to get email data from both sources: {e}")
            return []
    
    def analyze_vendor_patterns(self, vendor_name, emails):
        """Analyze patterns for a specific vendor"""
        vendor_lower = vendor_name.lower()
        vendor_emails = [e for e in emails if vendor_lower in e['vendor'].lower()]
        
        # Extract domains
        domains = []
        for email in vendor_emails:
            domain = self.extract_domain_from_email(email['sender'])
            if domain:
                domains.append(domain)
        
        # Count domain frequency
        domain_counts = Counter(domains)
        top_domains = [domain for domain, count in domain_counts.most_common(3)]
        
        # Generate aliases using multiple strategies
        aliases = set()
        
        # Strategy 1: Extract from detected vendor variations
        for email in vendor_emails:
            detected_vendor = email.get('detected_vendor', '')
            if detected_vendor and detected_vendor.lower() != vendor_lower:
                aliases.add(detected_vendor.lower())
        
        # Strategy 2: Extract company name variations from email text (if available)
        vendor_words = vendor_name.lower().split()
        for email in vendor_emails[:5]:  # Sample first 5 emails
            text_lower = email.get('text', '').lower()
            if text_lower:  # Only if text is available
                # Look for variations of vendor name
                for word in vendor_words:
                    if len(word) > 3:  # Skip short words
                        pattern = rf'\b{re.escape(word)}[a-z]*\b'
                        matches = re.findall(pattern, text_lower)
                        for match in matches:
                            if match != word and len(match) > 3:
                                aliases.add(match)
        
        # Strategy 3: Domain-based aliases
        for domain in top_domains:
            if '.' in domain:
                company_part = domain.split('.')[0]
                if company_part != vendor_lower and len(company_part) > 3:
                    aliases.add(company_part)
        
        # Clean and filter aliases
        aliases = [alias for alias in aliases if alias and len(alias) > 2]
        aliases = list(set(aliases))[:5]  # Limit to top 5
        
        return {
            'domains': top_domains,
            'aliases': aliases,
            'email_count': len(vendor_emails)
        }
    
    def enrich_excel(self, input_file, output_file=None):
        """Enrich Excel file with domains and aliases"""
        try:
            # Read Excel file
            df = pd.read_excel(input_file)
            # Convert columns to string type to avoid dtype warnings
            df['associated_domains'] = df['associated_domains'].astype('object')
            df['aliases'] = df['aliases'].astype('object')
            logging.info(f"Loaded {len(df)} vendors from Excel")
            
            # Get email data
            emails = self.get_email_data()
            if not emails:
                logging.error("No email data available for analysis")
                return False
            
            # Enrich each vendor
            for idx, row in df.iterrows():
                vendor_name = row['name']
                logging.info(f"Analyzing vendor: {vendor_name}")
                
                # Skip if already has data
                if pd.notna(row.get('associated_domains')) and row['associated_domains']:
                    logging.info(f"Skipping {vendor_name} - already has domains")
                    continue
                
                # Analyze patterns
                analysis = self.analyze_vendor_patterns(vendor_name, emails)
                
                # Update DataFrame
                if analysis['domains']:
                    df.at[idx, 'associated_domains'] = ','.join(analysis['domains'])
                
                if analysis['aliases']:
                    df.at[idx, 'aliases'] = ','.join(analysis['aliases'])
                
                logging.info(f"Enriched {vendor_name}: {analysis['email_count']} emails, "
                           f"{len(analysis['domains'])} domains, {len(analysis['aliases'])} aliases")
            
            # Save enriched file
            if not output_file:
                output_file = input_file.replace('.xlsx', '_enriched.xlsx')
            
            try:
                df.to_excel(output_file, index=False)
                logging.info(f"Saved enriched data to: {output_file}")
            except PermissionError:
                # Try alternative filename if file is locked
                import time
                alt_output = output_file.replace('.xlsx', f'_{int(time.time())}.xlsx')
                df.to_excel(alt_output, index=False)
                logging.info(f"Original file locked, saved to: {alt_output}")
                output_file = alt_output
            
            # Print summary
            self.print_summary(df)
            return True
            
        except Exception as e:
            logging.error(f"Failed to enrich Excel: {e}")
            return False
    
    def print_summary(self, df):
        """Print enrichment summary"""
        print("\n=== Enrichment Summary ===")
        for _, row in df.iterrows():
            print(f"\n{row['name']}:")
            if pd.notna(row.get('associated_domains')) and row['associated_domains']:
                print(f"  Domains: {row['associated_domains']}")
            if pd.notna(row.get('aliases')) and row['aliases']:
                print(f"  Aliases: {row['aliases']}")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Enrich vendor schema with domains and aliases")
    parser.add_argument("input_file", help="Input Excel file path")
    parser.add_argument("--output", help="Output Excel file path (optional)")
    
    args = parser.parse_args()
    
    # Handle relative paths from original working directory
    input_file = args.input_file if os.path.isabs(args.input_file) else os.path.join(original_cwd, args.input_file)
    
    if not os.path.exists(input_file):
        print(f"Error: Input file not found: {input_file}")
        return
    
    enricher = SchemaEnricher()
    success = enricher.enrich_excel(input_file, args.output)
    
    if success:
        print("✅ Schema enrichment completed successfully")
    else:
        print("❌ Schema enrichment failed")

if __name__ == "__main__":
    main()