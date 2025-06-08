"""
Graph API for VendorUpdater_Bot
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import uvicorn
import logging
from graph_db import (
    get_vendor_products, 
    get_related_vendors, 
    get_email_timeline,
    run_graph_query,
    mock_graph_data,
    count_vendor_emails,
    count_recent_emails,
    find_security_emails
)

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

app = FastAPI(title="Vendor Email Graph API")

class GraphQueryRequest(BaseModel):
    query: str
    params: Optional[Dict[str, Any]] = None

@app.get("/vendors")
async def list_vendors():
    """Get all vendors"""
    try:
        result = run_graph_query("MATCH (v:Vendor) RETURN v.name AS vendor")
        if result is None:
            # Use mock data if Neo4j is not available
            return {"vendors": ["hashicorp", "google", "paloaltonetworks"]}
        return {"vendors": [r["vendor"] for r in result]}
    except Exception as e:
        logging.error(f"Error listing vendors: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/products/{vendor}")
async def vendor_products(vendor: str):
    """Get products for a specific vendor"""
    try:
        result = get_vendor_products(vendor)
        if result is None:
            # Use mock data if Neo4j is not available
            mock_data = mock_graph_data()
            return {"products": [r["product"] for r in mock_data["vendor_products"]]}
        return {"products": [r["product"] for r in result]}
    except Exception as e:
        logging.error(f"Error getting vendor products: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/vendors/{product}")
async def product_vendors(product: str):
    """Get vendors for a specific product"""
    try:
        result = get_related_vendors(product)
        if result is None:
            # Use mock data if Neo4j is not available
            mock_data = mock_graph_data()
            return {"vendors": [r["vendor"] for r in mock_data["related_vendors"]]}
        return {"vendors": [r["vendor"] for r in result]}
    except Exception as e:
        logging.error(f"Error getting product vendors: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/timeline")
async def email_timeline(vendor: Optional[str] = None, product: Optional[str] = None, days: int = 30):
    """Get timeline of emails for a vendor or product"""
    try:
        result = get_email_timeline(vendor, product, days)
        if result is None:
            # Use mock data if Neo4j is not available
            mock_data = mock_graph_data()
            return {"timeline": mock_data["email_timeline"]}
        return {"timeline": result}
    except Exception as e:
        logging.error(f"Error getting email timeline: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analytics/count/{vendor}")
async def count_emails(vendor: str):
    """Count emails from a specific vendor"""
    try:
        count = count_vendor_emails(vendor)
        return {"vendor": vendor, "email_count": count}
    except Exception as e:
        logging.error(f"Error counting vendor emails: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analytics/recent")
async def recent_emails(vendor: Optional[str] = None, days: int = 7):
    """Count recent emails from a vendor"""
    try:
        count = count_recent_emails(vendor, days)
        return {"vendor": vendor or "all", "days": days, "email_count": count}
    except Exception as e:
        logging.error(f"Error counting recent emails: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analytics/security")
async def security_emails(days: int = 30):
    """Find security-related emails"""
    try:
        emails = find_security_emails(days)
        return {"days": days, "emails": emails}
    except Exception as e:
        logging.error(f"Error finding security emails: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query")
async def custom_query(request: GraphQueryRequest):
    """Run a custom Cypher query"""
    try:
        result = run_graph_query(request.query, request.params)
        if result is None:
            # Return empty result if Neo4j is not available
            return {"results": []}
        return {"results": result}
    except Exception as e:
        logging.error(f"Error running custom query: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)