import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import streamlit as st
import pandas as pd
from src import llm_utils
from src.hybrid_search import hybrid_search

# Set page title
st.set_page_config(page_title="VendorUpdater ChromaDB Inspector", layout="wide")

# Title
st.title("VendorUpdater ChromaDB Inspector")

# Connect to ChromaDB
@st.cache_resource
def get_collection():
    return llm_utils.get_chroma_collection()

collection = get_collection()

# Get collection info
count = collection.count()
st.write(f"Total documents in collection: {count}")

# Sidebar for search
st.sidebar.header("Search")
query = st.sidebar.text_input("Search query")
vendor_filter = st.sidebar.text_input("Vendor filter (optional)")
product_filter = st.sidebar.text_input("Product filter (optional)")
type_filter = st.sidebar.text_input("Type filter (optional)")
top_k = st.sidebar.slider("Number of results", 1, 20, 5)

# Build metadata filters
metadata_filters = {}
if vendor_filter:
    metadata_filters["vendor"] = vendor_filter
if product_filter:
    metadata_filters["product"] = product_filter
if type_filter:
    metadata_filters["type"] = type_filter

# Search button
if st.sidebar.button("Search") and query:
    with st.spinner("Searching..."):
        results = hybrid_search(query, metadata_filters if metadata_filters else None, top_k)
        
        if results["documents"]:
            st.header(f"Search Results for '{query}'")
            
            # Create a DataFrame for results
            result_data = []
            for i, (doc, meta) in enumerate(zip(results["documents"], results["metadatas"])):
                result_data.append({
                    "Rank": i+1,
                    "Score": round(results["distances"][i], 3),
                    "Text": doc[:200] + "..." if len(doc) > 200 else doc,
                    "Vendor": meta.get("vendor", ""),
                    "Product": meta.get("product", ""),
                    "Type": meta.get("type", ""),
                    "Date": meta.get("date", ""),
                    "Email ID": meta.get("email_id", ""),
                    "Chunk Index": meta.get("chunk_index", "")
                })
            
            df = pd.DataFrame(result_data)
            st.dataframe(df)
        else:
            st.warning("No results found.")

# Explore collection
st.sidebar.header("Explore Collection")
if st.sidebar.button("Show Sample"):
    with st.spinner("Loading sample..."):
        sample = collection.get(limit=5)
        
        st.header("Sample Documents")
        
        # Create a DataFrame for sample
        sample_data = []
        for i, (doc, meta) in enumerate(zip(sample["documents"], sample["metadatas"])):
            sample_data.append({
                "ID": sample["ids"][i],
                "Text": doc[:200] + "..." if len(doc) > 200 else doc,
                "Vendor": meta.get("vendor", ""),
                "Product": meta.get("product", ""),
                "Type": meta.get("type", ""),
                "Date": meta.get("date", ""),
                "Email ID": meta.get("email_id", ""),
                "Chunk Index": meta.get("chunk_index", "")
            })
        
        df = pd.DataFrame(sample_data)
        st.dataframe(df)

# Show unique metadata values
st.sidebar.header("Metadata Analysis")
if st.sidebar.button("Show Metadata"):
    with st.spinner("Analyzing metadata..."):
        all_data = collection.get()
        
        vendors = set(m.get("vendor", "unknown") for m in all_data["metadatas"])
        products = set(m.get("product", "unknown") for m in all_data["metadatas"])
        types = set(m.get("type", "unknown") for m in all_data["metadatas"])
        
        st.header("Unique Metadata Values")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.subheader("Vendors")
            for vendor in sorted(vendors):
                st.write(f"- {vendor}")
        
        with col2:
            st.subheader("Products")
            for product in sorted(products):
                st.write(f"- {product}")
        
        with col3:
            st.subheader("Types")
            for type_ in sorted(types):
                st.write(f"- {type_}")

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("VendorUpdater ChromaDB Inspector")
st.sidebar.markdown("© 2025")