"""
Database manager for storing and retrieving scraped data
"""
import os
import uuid
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings

class ChromaDBManager:
    """Class for managing ChromaDB operations"""
    
    def __init__(self, persist_directory: str = "./chroma_db"):
        """
        Initialize the ChromaDB manager
        
        Args:
            persist_directory: Directory to persist the database
        """
        self.persist_directory = persist_directory
        os.makedirs(persist_directory, exist_ok=True)
        
        self.client = chromadb.PersistentClient(path=persist_directory)
    
    def create_collection(self, collection_name: str) -> Any:
        """
        Create a new collection or get existing one
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            ChromaDB collection
        """
        try:
            return self.client.get_or_create_collection(name=collection_name)
        except Exception as e:
            raise Exception(f"Error creating collection: {str(e)}")
    
    def add_documents(self, 
                     collection_name: str, 
                     documents: List[str], 
                     metadatas: Optional[List[Dict[str, Any]]] = None,
                     ids: Optional[List[str]] = None) -> None:
        """
        Add documents to a collection
        
        Args:
            collection_name: Name of the collection
            documents: List of document texts
            metadatas: List of metadata dictionaries
            ids: List of document IDs
        """
        collection = self.create_collection(collection_name)
        
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in range(len(documents))]
        
        if metadatas is None:
            metadatas = [{} for _ in range(len(documents))]
        
        try:
            collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
        except Exception as e:
            raise Exception(f"Error adding documents to collection: {str(e)}")
    
    def query_collection(self, 
                        collection_name: str, 
                        query_text: str, 
                        n_results: int = 5) -> Dict[str, Any]:
        """
        Query a collection for similar documents
        
        Args:
            collection_name: Name of the collection
            query_text: Query text
            n_results: Number of results to return
            
        Returns:
            Query results
        """
        collection = self.create_collection(collection_name)
        
        try:
            results = collection.query(
                query_texts=[query_text],
                n_results=n_results
            )
            return results
        except Exception as e:
            raise Exception(f"Error querying collection: {str(e)}")
    
    def get_all_collections(self) -> List[str]:
        """
        Get all collection names
        
        Returns:
            List of collection names
        """
        try:
            return self.client.list_collections()
        except Exception as e:
            raise Exception(f"Error listing collections: {str(e)}")
    
    def delete_collection(self, collection_name: str) -> None:
        """
        Delete a collection
        
        Args:
            collection_name: Name of the collection
        """
        try:
            self.client.delete_collection(name=collection_name)
        except Exception as e:
            raise Exception(f"Error deleting collection: {str(e)}")