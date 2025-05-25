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
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get secrets from Key Vault with fallback to environment variables
try:
    openai_key = get_secret("AZURE-OPENAI-KEY")
    if not openai_key:
        logger.warning("OpenAI key not found in Key Vault, falling back to environment variable")
        openai_key = os.getenv("AZURE_OPENAI_KEY")
except Exception as e:
    logger.warning(f"Error getting OpenAI key from Key Vault: {str(e)}")
    openai_key = os.getenv("AZURE_OPENAI_KEY")

try:
    search_key = get_secret("AZURE-SEARCH-KEY")
    if not search_key:
        logger.warning("Azure Search key not found in Key Vault, falling back to environment variable")
        search_key = os.getenv("AZURE_SEARCH_KEY")
except Exception as e:
    logger.warning(f"Error getting Azure Search key from Key Vault: {str(e)}")
    search_key = os.getenv("AZURE_SEARCH_KEY")

# Simple status check for environment variables
logger.info(f"AZURE_SEARCH_ENDPOINT: {os.getenv('AZURE_SEARCH_ENDPOINT')}")
logger.info(f"AZURE_SEARCH_KEY: {'Set' if search_key else 'Not set'}")
logger.info(f"AZURE_SEARCH_INDEX: {os.getenv('AZURE_SEARCH_INDEX')}")
logger.info(f"AZURE_OPENAI_KEY: {'Set' if openai_key else 'Not set'}")
logger.info(f"AZURE_OPENAI_ENDPOINT: {os.getenv('AZURE_OPENAI_ENDPOINT')}")
logger.info(f"NEO4J_URI: {os.getenv('NEO4J_URI')}")

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
try:
    openai_service = AzureOpenAIService(
        api_key=openai_key,
        endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT")
    )
except Exception as e:
    logger.error(f"Failed to initialize OpenAI service: {str(e)}")
    openai_service = None

# Initialize other services
scraper = WebScraper(base_url="https://www.madewithnestle.ca/")

try:
    search_service = AzureSearchService(
        endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
        key=search_key,
        index_name=os.getenv("AZURE_SEARCH_INDEX")
    )
except Exception as e:
    logger.error(f"Failed to initialize search service: {str(e)}")
    search_service = None

# Get Neo4j Aura password with fallback to environment variable
try:
    neo4j_password = get_secret("NEO4J-AURA-PASSWORD")
    if not neo4j_password:
        logger.warning("Failed to get Neo4j password from Key Vault, falling back to environment variable")
        neo4j_password = os.getenv("NEO4J_AURA_PASSWORD") or os.getenv("NEO4J_PASSWORD")
except Exception as e:
    logger.warning(f"Error getting Neo4j password from Key Vault: {str(e)}")
    neo4j_password = os.getenv("NEO4J_AURA_PASSWORD") or os.getenv("NEO4J_PASSWORD")

# Initialize graph service with error handling
try:
    graph_service = GraphRAGService(
        uri=os.getenv("NEO4J_URI"),
        user=os.getenv("NEO4J_USER"),
        password=neo4j_password,
        openai_service=openai_service
    )
except Exception as e:
    logger.error(f"Failed to initialize graph service: {str(e)}")
    graph_service = None

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
        
        context_data = []
        
        # First, try to find information from the graph database (structured data)
        if graph_service and graph_service.driver:
            try:
                graph_results = graph_service.query(request.query)
                if graph_results and len(graph_results) > 0:
                    context_data = graph_results
            except Exception as e:
                logger.error(f"Error querying graph database: {str(e)}")
        
        # If graph search fails, try the vector search
        if not context_data:
            try:
                if search_service and search_service.search_client:
                    search_results = search_service.search(request.query)
                    context_data = search_results
            except Exception as e:
                logger.error(f"Error querying search service: {str(e)}")
        
        # If we have context data, use OpenAI to generate a response
        if context_data:
            # Use RAG approach with OpenAI
            try:
                response_text = openai_service.generate_response(
                    query=request.query,
                    context=context_data,
                    temperature=0.7
                )
            except Exception as e:
                logger.error(f"Error generating response with OpenAI: {str(e)}")
                response_text = "I'm sorry, I'm having trouble processing your request right now. Please try again later."
            
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
        logger.error(f"Error in chat endpoint: {str(e)}")
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