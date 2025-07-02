"""
Enhanced Natural Language Query Processing for VendorUpdater_Bot
Provides intelligent query understanding for conversational search
"""
import re
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from src import llm_utils
from graph_db_consolidated import run_graph_query

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class NLQueryProcessor:
    """Enhanced natural language query processor"""
    
    def __init__(self):
        self.vendor_synonyms = {
            "hashicorp": ["hashicorp", "hashi", "terraform", "vault"],
            "palo alto": ["palo alto", "paloalto", "pan", "prisma"],
            "amazon": ["amazon", "aws", "amazon web services"],
            "microsoft": ["microsoft", "ms", "azure"],
            "google": ["google", "gcp", "google cloud"]
        }
        
        self.type_synonyms = {
            "security": ["security", "vulnerability", "cve", "patch", "alert", "threat"],
            "marketing": ["marketing", "promo", "event", "webinar", "announcement"],
            "technical": ["technical", "update", "release", "documentation", "whitepaper"]
        }
        
        self.time_patterns = {
            "recent": 7,
            "last week": 7,
            "past week": 7,
            "last month": 30,
            "past month": 30,
            "yesterday": 1,
            "today": 0
        }
    
    def process_query(self, query: str) -> Dict[str, Any]:
        """Process natural language query and extract structured parameters"""
        query_lower = query.lower().strip()
        
        # Determine query intent
        intent = self._classify_intent(query_lower)
        
        # Extract entities
        vendor = self._extract_vendor(query_lower)
        product = self._extract_product(query_lower)
        email_type = self._extract_type(query_lower)
        time_filter = self._extract_time_filter(query_lower)
        
        # Extract search terms
        search_terms = self._extract_search_terms(query_lower, vendor, product, email_type)
        
        return {
            "intent": intent,
            "search_terms": search_terms,
            "filters": {
                "vendor": vendor,
                "product": product,
                "type": email_type
            },
            "time_filter": time_filter,
            "original_query": query
        }
    
    def _classify_intent(self, query: str) -> str:
        """Classify the intent of the query"""
        if any(word in query for word in ["how many", "count", "number of"]):
            return "count"
        elif any(word in query for word in ["list", "show", "what", "which"]):
            return "list"
        elif any(word in query for word in ["find", "search", "get", "tell me about"]):
            return "search"
        elif any(word in query for word in ["recent", "latest", "new"]):
            return "recent"
        else:
            return "search"  # default
    
    def _extract_vendor(self, query: str) -> Optional[str]:
        """Extract vendor from query using synonyms"""
        for vendor, synonyms in self.vendor_synonyms.items():
            for synonym in synonyms:
                if synonym in query:
                    return vendor
        return None
    
    def _extract_product(self, query: str) -> Optional[str]:
        """Extract product mentions from query"""
        # Common products
        products = ["vault", "terraform", "prisma", "cortex", "bedrock", "sagemaker"]
        for product in products:
            if product in query:
                return product
        return None
    
    def _extract_type(self, query: str) -> Optional[str]:
        """Extract email type using synonyms"""
        for email_type, synonyms in self.type_synonyms.items():
            for synonym in synonyms:
                if synonym in query:
                    return email_type
        return None
    
    def _extract_time_filter(self, query: str) -> Optional[int]:
        """Extract time-based filters"""
        for pattern, days in self.time_patterns.items():
            if pattern in query:
                return days
        
        # Extract specific number of days
        match = re.search(r"past (\d+) days?", query)
        if match:
            return int(match.group(1))
        
        match = re.search(r"last (\d+) days?", query)
        if match:
            return int(match.group(1))
        
        return None
    
    def _extract_search_terms(self, query: str, vendor: str, product: str, email_type: str) -> str:
        """Extract core search terms by removing extracted entities"""
        # Remove extracted entities from query
        clean_query = query
        
        if vendor:
            for synonym in self.vendor_synonyms.get(vendor, []):
                clean_query = clean_query.replace(synonym, "")
        
        if product:
            clean_query = clean_query.replace(product, "")
        
        if email_type:
            for synonym in self.type_synonyms.get(email_type, []):
                clean_query = clean_query.replace(synonym, "")
        
        # Remove common query words
        stop_words = ["show", "me", "find", "get", "tell", "about", "from", "recent", "latest", "new"]
        words = clean_query.split()
        filtered_words = [w for w in words if w not in stop_words and len(w) > 2]
        
        return " ".join(filtered_words).strip()

def process_natural_language_query(query: str) -> Dict[str, Any]:
    """Main function to process natural language queries"""
    processor = NLQueryProcessor()
    processed = processor.process_query(query)
    
    # Generate appropriate response based on intent
    if processed["intent"] == "count":
        return _handle_count_query(processed)
    elif processed["intent"] == "list":
        return _handle_list_query(processed)
    elif processed["intent"] == "recent":
        return _handle_recent_query(processed)
    else:
        return _handle_search_query(processed)

def _handle_count_query(processed: Dict[str, Any]) -> Dict[str, Any]:
    """Handle count-based queries"""
    vendor = processed["filters"]["vendor"]
    days = processed["time_filter"] or 30
    
    # Build Cypher query
    if vendor:
        cypher = f"""
        MATCH (v:Vendor {{name: '{vendor}'}})<-[:FROM]-(e:Email)
        WHERE e.date >= date() - duration({{days: {days}}})
        RETURN count(e) AS count
        """
    else:
        cypher = f"""
        MATCH (e:Email)
        WHERE e.date >= date() - duration({{days: {days}}})
        RETURN count(e) AS count
        """
    
    result = run_graph_query(cypher)
    count = result[0]["count"] if result else 0
    
    vendor_str = f"from {vendor}" if vendor else ""
    time_str = f"in the past {days} days" if days else ""
    
    return {
        "intent": "count",
        "answer": f"There are {count} emails {vendor_str} {time_str}".strip(),
        "count": count,
        "parameters": processed
    }

def _handle_list_query(processed: Dict[str, Any]) -> Dict[str, Any]:
    """Handle list-based queries"""
    vendor = processed["filters"]["vendor"]
    
    if "vendor" in processed["original_query"]:
        # List vendors
        cypher = "MATCH (v:Vendor) RETURN v.name AS name ORDER BY v.name"
        result = run_graph_query(cypher)
        items = [r["name"] for r in result] if result else []
        
        return {
            "intent": "list",
            "answer": f"Available vendors ({len(items)}): {', '.join(items[:10])}{'...' if len(items) > 10 else ''}",
            "items": items,
            "parameters": processed
        }
    
    elif "product" in processed["original_query"]:
        # List products
        if vendor:
            cypher = f"""
            MATCH (v:Vendor {{name: '{vendor}'}})-[:OFFERS]->(p:Product)
            RETURN p.name AS name ORDER BY p.name
            """
        else:
            cypher = "MATCH (p:Product) RETURN p.name AS name ORDER BY p.name LIMIT 20"
        
        result = run_graph_query(cypher)
        items = [r["name"] for r in result] if result else []
        
        vendor_str = f"from {vendor}" if vendor else ""
        return {
            "intent": "list",
            "answer": f"Available products {vendor_str} ({len(items)}): {', '.join(items)}",
            "items": items,
            "parameters": processed
        }
    
    else:
        # List emails
        vendor_filter = f"MATCH (v:Vendor {{name: '{vendor}'}})<-[:FROM]-(e:Email)" if vendor else "MATCH (e:Email)"
        cypher = f"""
        {vendor_filter}
        RETURN e.subject AS subject, e.date AS date
        ORDER BY e.date DESC LIMIT 10
        """
        
        result = run_graph_query(cypher)
        items = result if result else []
        
        return {
            "intent": "list",
            "answer": f"Recent emails {f'from {vendor}' if vendor else ''} ({len(items)} shown)",
            "items": items,
            "parameters": processed
        }

def _handle_recent_query(processed: Dict[str, Any]) -> Dict[str, Any]:
    """Handle recent/latest queries"""
    vendor = processed["filters"]["vendor"]
    email_type = processed["filters"]["type"]
    days = processed["time_filter"] or 7
    
    # Build query conditions
    conditions = []
    if vendor:
        conditions.append(f"v.name = '{vendor}'")
    if email_type:
        conditions.append(f"e.type = '{email_type}'")
    
    where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
    
    cypher = f"""
    MATCH (v:Vendor)<-[:FROM]-(e:Email)
    {where_clause}
    RETURN e.subject AS subject, e.date AS date, v.name AS vendor
    ORDER BY e.date DESC LIMIT 5
    """
    
    result = run_graph_query(cypher)
    items = result if result else []
    
    return {
        "intent": "recent",
        "answer": f"Recent {email_type or 'emails'} {f'from {vendor}' if vendor else ''} ({len(items)} found)",
        "items": items,
        "parameters": processed
    }

def _handle_search_query(processed: Dict[str, Any]) -> Dict[str, Any]:
    """Handle general search queries"""
    from src.unified_search import unified_search
    
    # Use unified search with extracted parameters
    filters = {k: v for k, v in processed["filters"].items() if v is not None}
    
    # Add time filter if present
    if processed["time_filter"] is not None:
        filters["days"] = processed["time_filter"]
    
    # Perform search
    search_terms = processed["search_terms"] or processed["original_query"]
    results = unified_search(search_terms, filters, {}, top_k=5)
    
    return {
        "intent": "search",
        "answer": f"Found {len(results)} results for your query",
        "results": results,
        "parameters": processed
    }