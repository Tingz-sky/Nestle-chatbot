from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import json
import time
import logging
from dotenv import load_dotenv

from services.web_scraper import WebScraper
from services.search_service import AzureSearchService
from services.graph_service import GraphRAGService
from services.openai_service import AzureOpenAIService
from services.keyvault_service import get_secret

# Configure logging
logging.getLogger('azure').setLevel(logging.WARNING)

# Load environment variables
load_dotenv()

# Simple status check for environment variables
print(f"AZURE_SEARCH_ENDPOINT: {os.getenv('AZURE_SEARCH_ENDPOINT')}")
print(f"AZURE_SEARCH_KEY: {'Set' if os.getenv('AZURE_SEARCH_KEY') else 'Not set'}")
print(f"AZURE_SEARCH_INDEX: {os.getenv('AZURE_SEARCH_INDEX')}")
print(f"AZURE_OPENAI_KEY: {'Set' if os.getenv('AZURE_OPENAI_KEY') else 'Not set'}")
print(f"AZURE_OPENAI_ENDPOINT: {os.getenv('AZURE_OPENAI_ENDPOINT')}")
print(f"NEO4J_URI: {os.getenv('NEO4J_URI')}")

app = FastAPI(title="Nestle Chatbot API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, specify the actual frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize OpenAI service
openai_service = AzureOpenAIService(
    api_key=os.getenv("AZURE_OPENAI_KEY"),
    endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT")
)

# Initialize other services
scraper = WebScraper(base_url="https://www.madewithnestle.ca/")
search_service = AzureSearchService(
    endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
    key=os.getenv("AZURE_SEARCH_KEY"),
    index_name=os.getenv("AZURE_SEARCH_INDEX")
)

# 获取Neo4j Aura密码
neo4j_password = get_secret("NEO4J-AURA-PASSWORD")

graph_service = GraphRAGService(
    uri=os.getenv("NEO4J_URI"),
    user=os.getenv("NEO4J_USER"),
    password=neo4j_password,  # 使用从Key Vault获取的Aura密码
    openai_service=openai_service  # Pass OpenAI service to graph service
)

class ChatRequest(BaseModel):
    query: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    references: List[Dict[str, str]] = []
    session_id: str

@app.get("/")
async def root():
    return {"message": "Welcome to the Nestle Chatbot API"}

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        # Generate a session ID if not provided
        session_id = request.session_id or f"session_{int(time.time())}"
        
        # First, try to find information from the graph database (structured data)
        graph_results = graph_service.query(request.query)
        
        # If graph search fails, try the vector search
        if not graph_results or len(graph_results) == 0:
            search_results = search_service.search(request.query)
            context_data = search_results
        else:
            context_data = graph_results
        
        # If we have context data, use OpenAI to generate a response
        if context_data:
            # Use RAG approach with OpenAI
            response_text = openai_service.generate_response(
                query=request.query,
                context=context_data,
                temperature=0.7
            )
            
            # Extract references for attribution
            references = [
                {"title": result.get("title", ""), "url": result.get("url", "")}
                for result in context_data
                if "title" in result and "url" in result
            ]
        else:
            # Fallback response
            response_text = "I'm sorry, I couldn't find specific information about that. Please try asking another question about Nestle products or services."
            references = []
            
        return ChatResponse(
            response=response_text,
            references=references,
            session_id=session_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

@app.post("/api/refresh-content")
async def refresh_content():
    """Endpoint to manually trigger content refreshing from the Nestle website"""
    try:
        # Scrape website content
        data = scraper.scrape_website()
        
        # Build knowledge graph
        graph_service.build_knowledge_graph(data)
        
        # Refresh search index
        search_service.refresh_index()
        
        return {"message": f"Content refreshed successfully with {len(data)} pages"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to refresh content: {str(e)}")

# Add a simple endpoint to check the status of the services
@app.get("/api/status")
async def status():
    """Check the status of all services"""
    status = {
        "search_service": search_service.search_client is not None,
        "graph_service": graph_service.driver is not None,
        "openai_service": openai_service is not None
    }
    return status

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 