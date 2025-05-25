import os
import json
import logging
from typing import List, Dict, Any, Optional
from azure.search.documents import SearchClient
from azure.search.documents.models import QueryType
from azure.core.credentials import AzureKeyCredential

logger = logging.getLogger(__name__)

class AzureSearchService:
    def __init__(self, endpoint: str, key: str, index_name: str):
        self.endpoint = endpoint
        self.key = key
        self.index_name = index_name
        
        # Initialize search client if credentials are provided
        if endpoint and key and index_name:
            try:
                self.search_client = SearchClient(
                    endpoint=endpoint,
                    index_name=index_name,
                    credential=AzureKeyCredential(key)
                )
                logger.info(f"Connected to Azure Search index {index_name}")
            except Exception as e:
                logger.error(f"Failed to connect to Azure Search: {str(e)}")
                self.search_client = None
        else:
            logger.warning("Azure Search credentials not provided")
            self.search_client = None
    
    def search(self, query: str, top: int = 5) -> List[Dict[str, Any]]:
        """
        Search the Azure Cognitive Search index for the given query
        """
        if not self.search_client:
            logger.warning("Search client not initialized, returning empty results")
            return []
        
        try:
            # Use standard search instead of semantic search for compatibility
            try:
                # Try standard search with QueryType.SIMPLE
                results = self.search_client.search(
                    query,
                    query_type=QueryType.SIMPLE,
                    top=top
                )
            except Exception as e:
                logger.warning(f"Error with simple query: {str(e)}")
                # Fallback to basic search without specifying query type
                results = self.search_client.search(
                    query,
                    top=top
                )
            
            # Process and format results
            formatted_results = []
            for result in results:
                formatted_result = {
                    "id": result.get("id", ""),
                    "url": result.get("url", ""),
                    "title": result.get("title", ""),
                    "content": result.get("content", ""),
                    "score": result.get("@search.score", 0)
                }
                formatted_results.append(formatted_result)
            
            return formatted_results
        except Exception as e:
            logger.error(f"Search error: {str(e)}")
            return []
    
    def refresh_index(self) -> bool:
        """
        Refresh the search index with the latest scraped data
        """
        if not self.search_client:
            logger.warning("Search client not initialized, cannot refresh index")
            return False
        
        try:
            # Load scraped data
            with open('data/scraped_data.json', 'r') as f:
                data = json.load(f)
            
            # Prepare documents for indexing
            documents = []
            for i, item in enumerate(data):
                doc = {
                    "id": f"doc-{i}",
                    "url": item.get("url", ""),
                    "title": item.get("title", ""),
                    "content": item.get("content", "")
                }
                
                # Add table content if available
                if "tables" in item and item["tables"]:
                    table_content = []
                    for table in item["tables"]:
                        table_content.append(" ".join([str(cell) for row in table["data"] for cell in row.values()]))
                    doc["tableContent"] = " ".join(table_content)
                
                documents.append(doc)
            
            # Upload documents to index in batches
            batch_size = 100
            for i in range(0, len(documents), batch_size):
                batch = documents[i:i + batch_size]
                self.search_client.upload_documents(documents=batch)
                logger.info(f"Uploaded batch {i//batch_size + 1} to search index")
            
            logger.info(f"Successfully refreshed index with {len(documents)} documents")
            return True
        
        except Exception as e:
            logger.error(f"Error refreshing index: {str(e)}")
            return False 