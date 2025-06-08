import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import pandas as pd
import streamlit as st
from src import llm_utils

# Set page title
st.set_page_config(page_title="VendorUpdater DB Inspector", layout="wide")

# Title
st.title("VendorUpdater Database Inspector")

# Connect to ChromaDB
@st.cache_resource
def get_collection():
    return llm_utils.get_chroma_collection()

collection = get_collection()

# Get all data
@st.cache_data
def get_all_data():
    return collection.get()

all_data = get_all_data()

# Convert to DataFrame
data = []
for i, (doc, meta, id_) in enumerate(zip(all_data["documents"], all_data["metadatas"], all_data["ids"])):
    data.append({
        "ID": id_,
        "Text": doc[:100] + "..." if len(doc) > 100 else doc,
        "Vendor": meta.get("vendor", ""),
        "Product": meta.get("product", ""),
        "Type": meta.get("type", ""),
        "Date": meta.get("date", ""),
        "Email ID": meta.get("email_id", ""),
        "Chunk Index": meta.get("chunk_index", "")
    })

df = pd.DataFrame(data)

# Sidebar filters
st.sidebar.header("Filters")

# Vendor filter
vendors = ["All"] + sorted(df["Vendor"].unique().tolist())
selected_vendor = st.sidebar.selectbox("Vendor", vendors)

# Product filter
products = ["All"] + sorted(df["Product"].unique().tolist())
selected_product = st.sidebar.selectbox("Product", products)

# Type filter
types = ["All"] + sorted(df["Type"].unique().tolist())
selected_type = st.sidebar.selectbox("Type", types)

# Apply filters
filtered_df = df.copy()

if selected_vendor != "All":
    filtered_df = filtered_df[filtered_df["Vendor"] == selected_vendor]

if selected_product != "All":
    filtered_df = filtered_df[filtered_df["Product"] == selected_product]

if selected_type != "All":
    filtered_df = filtered_df[filtered_df["Type"] == selected_type]

# Show results
st.write(f"Showing {len(filtered_df)} of {len(df)} documents")
st.dataframe(filtered_df)

# Show statistics
st.header("Statistics")

col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("Vendors")
    vendor_counts = df["Vendor"].value_counts().reset_index()
    vendor_counts.columns = ["Vendor", "Count"]
    st.dataframe(vendor_counts)

with col2:
    st.subheader("Products")
    product_counts = df["Product"].value_counts().reset_index()
    product_counts.columns = ["Product", "Count"]
    st.dataframe(product_counts)

with col3:
    st.subheader("Types")
    type_counts = df["Type"].value_counts().reset_index()
    type_counts.columns = ["Type", "Count"]
    st.dataframe(type_counts)

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("VendorUpdater DB Inspector")
st.sidebar.markdown("© 2025")