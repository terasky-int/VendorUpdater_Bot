"""
DEPRECATED: This file is no longer used. 
Please use src/unified_search.py instead.

This file is kept for reference purposes only.
"""

import sys
import os
import logging
from typing import Dict, List, Optional, Any

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.unified_search import (
    process_search_query,
    unified_search,
    graph_enhanced_ranking,
    format_search_results,
    get_vendor_products_enhanced
)

logging.warning("This module is deprecated. Please use src.unified_search instead.")