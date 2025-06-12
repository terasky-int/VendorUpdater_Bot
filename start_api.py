"""
Startup script for the unified API
"""

import uvicorn
import argparse
import logging

def main():
    parser = argparse.ArgumentParser(description="Start the VendorUpdater Bot API")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind the API server")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind the API server")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")
    parser.add_argument("--log-level", default="info", choices=["debug", "info", "warning", "error", "critical"], 
                        help="Logging level")
    
    args = parser.parse_args()
    
    # Configure logging
    log_level = getattr(logging, args.log_level.upper())
    logging.basicConfig(level=log_level, format="%(asctime)s - %(levelname)s - %(message)s")
    
    # Start the API server
    logging.info(f"Starting unified API server on {args.host}:{args.port}")
    uvicorn.run(
        "unified_api:app", 
        host=args.host, 
        port=args.port, 
        reload=args.reload,
        log_level=args.log_level
    )

if __name__ == "__main__":
    main()