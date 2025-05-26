import streamlit as st
import pandas as pd
from src import llm_utils

st.set_page_config(page_title="ChromaDB Email Inspector", layout="wide")
st.title("📬 ChromaDB Email Inspector")

# Load ChromaDB collection
collection = llm_utils.get_chroma_collection()
st.success("Connected to ChromaDB collection")

# Fetch data
with st.spinner("Fetching data from vector DB..."):
    results = collection.get(include=["documents", "metadatas"])

# Build DataFrame
raw_df = pd.DataFrame({
    "text": results["documents"],
    "metadata": results["metadatas"]
})

# Flatten metadata
meta_df = pd.json_normalize(raw_df["metadata"])
final_df = pd.concat([meta_df, raw_df["text"]], axis=1)

# Display filter
email_ids = final_df["email_id"].dropna().unique()
selected_email = st.selectbox("Select email ID to inspect", sorted(email_ids))

filtered_df = final_df[final_df["email_id"] == selected_email].sort_values("chunk_index")

st.write(f"Showing {len(filtered_df)} chunks for email ID: `{selected_email}`")
st.dataframe(filtered_df[["chunk_index", "vendor", "product", "type", "date", "text"]], use_container_width=True)

# Expand to show full text per chunk
st.markdown("---")
st.subheader("🧩 Full Chunk Viewer")
for _, row in filtered_df.iterrows():
    with st.expander(f"Chunk {row['chunk_index']} — {row.get('product', 'Unknown')} | {row.get('type', '')}"):
        st.write(row["text"])
