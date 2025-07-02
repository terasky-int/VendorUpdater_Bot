"""
API endpoints for VendorUpdater_Bot

This module provides API endpoints that combine vector search and graph database capabilities.
"""

import logging
from typing import Dict, Any, List, Optional

from src.optimized_search import (
    process_search_query,
    unified_search,
    graph_enhanced_ranking,
    format_search_results,
    get_vendor_products_enhanced
)

from graph_db_consolidated import (
    get_vendor_products_by_confidence,
    get_email_timeline,
    count_recent_emails,
    find_security_emails,
    CONFIDENCE_HIGH,
    CONFIDENCE_MEDIUM,
    CONFIDENCE_LOW
)

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class UnifiedAPI:
    """API endpoints for unified search and graph operations"""
    
    @staticmethod
    def unified_search(query: str, top_k: int = 5) -> Dict[str, Any]:
        """
        Perform a unified search using both vector and graph capabilities
        
        Args:
            query: Natural language query text
            top_k: Number of results to return
        
        Returns:
            Dict with search results and related entities
        """
        try:
            # Process the query to extract parameters
            processed = process_search_query(query)
            
            # Perform unified search
            results = unified_search(
                processed["query_text"],
                processed["filters"],
                processed["graph_filters"],
                top_k
            )
            
            # Apply graph-enhanced ranking
            reranked = graph_enhanced_ranking(results, processed["query_text"])
            
            # Format results for API response
            formatted = format_search_results(reranked)
            
            # Add extracted parameters to response
            formatted["extracted_parameters"] = {
                "filters": processed["filters"],
                "graph_filters": processed["graph_filters"]
            }
            
            return formatted
        
        except Exception as e:
            logging.error(f"Error in unified search: {e}")
            return {"error": f"Search error: {str(e)}"}

    @staticmethod
    def get_vendor_products(vendor: str, confidence: str = "low") -> Dict[str, Any]:
        """
        Get products offered by a vendor with confidence levels
        
        Args:
            vendor: Name of the vendor
            confidence: Minimum confidence level (high, medium, low)
        
        Returns:
            Dict with products and confidence levels
        """
        try:
            # Map string confidence to constants
            confidence_map = {
                "high": CONFIDENCE_HIGH,
                "medium": CONFIDENCE_MEDIUM,
                "low": CONFIDENCE_LOW
            }
            
            # Get products with confidence levels
            products = get_vendor_products_by_confidence(
                vendor,
                confidence_map.get(confidence, CONFIDENCE_LOW)
            )
            
            return {
                "vendor": vendor,
                "products": products,
                "confidence_level": confidence,
                "total": len(products)
            }
        
        except Exception as e:
            logging.error(f"Error getting vendor products: {e}")
            return {"error": f"Database error: {str(e)}"}

    @staticmethod
    def get_timeline(vendor: Optional[str] = None, product: Optional[str] = None, 
                    days: int = 30, limit: int = 10) -> Dict[str, Any]:
        """
        Get timeline of emails with optional filters
        
        Args:
            vendor: Filter by vendor name
            product: Filter by product name
            days: Number of days to look back
            limit: Maximum number of results to return
        
        Returns:
            Dict with emails in timeline format
        """
        try:
            timeline = get_email_timeline(vendor, product, days)
            
            return {
                "timeline": timeline[:limit],
                "total": len(timeline)
            }
        
        except Exception as e:
            logging.error(f"Error getting timeline: {e}")
            return {"error": f"Database error: {str(e)}"}

    @staticmethod
    def get_security_emails(days: int = 30) -> Dict[str, Any]:
        """
        Get security-related emails
        
        Args:
            days: Number of days to look back
        
        Returns:
            Dict with security-related emails
        """
        try:
            emails = find_security_emails(days)
            
            return {
                "security_emails": emails,
                "total": len(emails),
                "days": days
            }
        
        except Exception as e:
            logging.error(f"Error getting security emails: {e}")
            return {"error": f"Database error: {str(e)}"}

    @staticmethod
    def natural_language_query(query: str) -> Dict[str, Any]:
        """
        Process a natural language query and return structured results
        
        Args:
            query: Natural language query text
        
        Returns:
            Dict with structured answer based on query type
        """
        try:
            # Process the query
            processed = process_search_query(query)
            query_lower = query.lower()
            
            # Determine query type
            query_type = "search"  # Default
            
            if "how many" in query_lower or "count" in query_lower:
                query_type = "count"
            elif "list" in query_lower or "what products" in query_lower:
                query_type = "list"
            
            # Handle different query types
            if query_type == "count":
                # Count emails
                vendor = processed["filters"].get("vendor")
                days = processed["graph_filters"].get("days", 30)
                
                count = count_recent_emails(vendor, days)
                
                time_period = f"in the past {days} days" if days else ""
                vendor_str = f"from {vendor}" if vendor else ""
                
                answer = f"There are {count} emails {vendor_str} {time_period}."
                
                return {
                    "answer": answer.strip(),
                    "query_type": "count",
                    "parameters": {
                        "vendor": vendor,
                        "days": days
                    },
                    "data": {
                        "count": count
                    }
                }
                
            elif query_type == "list":
                # List products
                vendor = processed["filters"].get("vendor")
                
                if vendor:
                    products = get_vendor_products_enhanced(vendor)
                    
                    return {
                        "answer": f"Found {len(products)} products for {vendor}.",
                        "query_type": "list",
                        "parameters": {
                            "vendor": vendor
                        },
                        "data": {
                            "products": products
                        }
                    }
                else:
                    return {
                        "answer": "Please specify a vendor to list products.",
                        "query_type": "list",
                        "parameters": {},
                        "data": {}
                    }
                    
            else:
                # Default to search
                results = unified_search(
                    processed["query_text"],
                    processed["filters"],
                    processed["graph_filters"],
                    5
                )
                
                reranked = graph_enhanced_ranking(results, processed["query_text"])
                formatted = format_search_results(reranked)
                
                return {
                    "answer": f"Found {len(formatted['results'])} results for your query.",
                    "query_type": "search",
                    "parameters": processed,
                    "data": formatted
                }
        
        except Exception as e:
            logging.error(f"Error processing natural language query: {e}")
            return {"error": f"Processing error: {str(e)}"}