from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import json
import time
import logging
from dotenv import load_dotenv
import re
import neo4j

from services.web_scraper import WebScraper
from services.search_service import AzureSearchService
from services.graph_service import GraphRAGService
from services.openai_service import AzureOpenAIService
from services.keyvault_service import get_secret
from services.conversation_service import ConversationService

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

# Initialize conversation service
conversation_service = ConversationService()

class ChatRequest(BaseModel):
    query: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    references: List[Dict[str, str]] = []
    session_id: str

# New models for knowledge graph operations
class NodeData(BaseModel):
    title: str
    content: Optional[str] = ""
    url: Optional[str] = ""
    type: str = "Entity"

class NodeDeleteRequest(BaseModel):
    url: str

class RelationshipData(BaseModel):
    source_url: str
    target_url: str
    rel_type: str
    properties: Optional[Dict[str, Any]] = None

class RelationshipDeleteRequest(BaseModel):
    source_url: str
    target_url: str
    rel_type: str

class GraphQueryRequest(BaseModel):
    cypher_query: str

@app.get("/")
async def root():
    return {"message": "Welcome to the Nestle Chatbot API"}

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        # Generate a session ID if not provided
        session_id = request.session_id or f"session_{int(time.time())}"
        
        # Get current user query
        user_query = request.query
        
        # Check if it's an existing session and if the query contains reference terms
        reference_terms = ["it", "this", "that", "these", "those", "they", "them", "its", "their", "this product"]
        has_reference = any(ref in user_query.lower().split() for ref in reference_terms)
        
        # If contains reference terms and has session history, try to enhance the query
        search_query = user_query
        if has_reference and session_id in conversation_service.sessions:
            # Get conversation history
            chat_history = conversation_service.get_conversation_history(session_id)
            
            # If there's history, try to find entities that might be referenced
            if chat_history and len(chat_history) >= 2:
                # Use recent assistant replies to enhance context
                recent_assistant_msgs = [msg for msg in chat_history if msg["type"] == "ai"]
                
                if recent_assistant_msgs:
                    # Extract potential product names mentioned in the most recent assistant reply
                    last_assistant_msg = recent_assistant_msgs[-1]["content"]
                    first_paragraph = last_assistant_msg.split('\n\n')[0] if '\n\n' in last_assistant_msg else last_assistant_msg
                    
                    # Enhance query to include context information
                    if first_paragraph and len(first_paragraph) > 10:
                        logger.info(f"Enhancing query with context from previous conversation")
                        search_query = f"{user_query} (referring to previous topic: {first_paragraph})"
        
        context_data = []
        
        # First, try to find information from the graph database (structured data)
        if graph_service and graph_service.driver:
            try:
                graph_results = graph_service.query(search_query)
                if graph_results and len(graph_results) > 0:
                    context_data = graph_results
            except Exception as e:
                logger.error(f"Error querying graph database: {str(e)}")
        
        # If graph search fails, try the vector search
        if not context_data:
            try:
                if search_service and search_service.search_client:
                    search_results = search_service.search(search_query)
                    context_data = search_results
            except Exception as e:
                logger.error(f"Error querying search service: {str(e)}")
        
        # If we have context data, use OpenAI to generate a response
        if context_data:
            # Save user message to conversation history
            conversation_service.add_user_message(session_id, user_query)  # Save original query, not enhanced query
            
            # Get conversation history for the session
            chat_history = conversation_service.get_conversation_history(session_id)
            
            # Use RAG approach with OpenAI and conversation history
            try:
                # If chat history exists, use it for context
                if chat_history and len(chat_history) > 1:  # More than just the current message
                    response_text = openai_service.generate_response_with_history(
                        query=user_query,  # Use original query
                        context=context_data,
                        chat_history=chat_history[:-1],  # Exclude the last message which we just added
                        temperature=0.7
                    )
                else:
                    # For first message, use the standard response generator
                    response_text = openai_service.generate_response(
                        query=user_query,
                        context=context_data,
                        temperature=0.7
                    )
            except Exception as e:
                logger.error(f"Error generating response with OpenAI: {str(e)}")
                response_text = "I'm sorry, I'm having trouble processing your request right now. Please try again later."
            
            # Save AI response to conversation history
            conversation_service.add_ai_message(session_id, response_text)
            
            # Extract references for attribution with deduplication
            seen_urls = set()
            references = []
            
            for result in context_data:
                if "title" in result and "url" in result:
                    url = result.get("url", "")
                    # Only add URLs we haven't seen yet
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        references.append({
                            "title": result.get("title", ""),
                            "url": url
                        })
        else:
            # Fallback response
            conversation_service.add_user_message(session_id, user_query)
            response_text = "I'm sorry, I couldn't find specific information about that. Please try asking another question about Nestle products or services."
            conversation_service.add_ai_message(session_id, response_text)
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

# New endpoints for knowledge graph management

@app.get("/api/graph/nodes")
async def get_nodes():
    """Get all nodes from the knowledge graph"""
    if not graph_service or not graph_service.driver:
        raise HTTPException(status_code=503, detail="Graph database service not available")
    
    try:
        # Create a Cypher query to get all nodes - modified to include all node types
        cypher_query = """
        MATCH (n)
        RETURN n.title as title, n.content as content, n.url as url, n.type as type, labels(n)[0] as label
        LIMIT 100
        """
        
        with graph_service.driver.session() as session:
            result = session.run(cypher_query)
            nodes = [record.data() for record in result]
        
        return nodes
    except Exception as e:
        logger.error(f"Error retrieving nodes: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve nodes: {str(e)}")

@app.get("/api/graph/relationships")
async def get_relationships():
    """Get all relationships from the knowledge graph"""
    if not graph_service or not graph_service.driver:
        raise HTTPException(status_code=503, detail="Graph database service not available")
    
    try:
        # Create a Cypher query to get all relationships - modified to include all node types
        cypher_query = """
        MATCH (source)-[r]->(target)
        RETURN source.url as source_url, target.url as target_url, 
               source.title as source_title, target.title as target_title,
               type(r) as rel_type
        LIMIT 100
        """
        
        with graph_service.driver.session() as session:
            result = session.run(cypher_query)
            relationships = [record.data() for record in result]
        
        return relationships
    except Exception as e:
        logger.error(f"Error retrieving relationships: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve relationships: {str(e)}")

@app.post("/api/graph/node")
async def add_node(node_data: NodeData):
    """Add a new node to the knowledge graph"""
    if not graph_service or not graph_service.driver:
        raise HTTPException(status_code=503, detail="Graph database service not available")
    
    try:
        result = graph_service.add_node(node_data.dict())
        
        if result:
            return {"message": "Node added successfully", "url": node_data.url}
        else:
            raise HTTPException(status_code=500, detail="Failed to add node")
    except Exception as e:
        logger.error(f"Error adding node: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to add node: {str(e)}")

@app.delete("/api/graph/node")
async def delete_node(node_data: NodeDeleteRequest):
    """Delete a node from the knowledge graph and all its relationships"""
    if not graph_service or not graph_service.driver:
        raise HTTPException(status_code=503, detail="Graph database service not available")
    
    try:
        # Create a Cypher query to delete the node and all its relationships
        cypher_query = """
        MATCH (n {url: $url})
        DETACH DELETE n
        RETURN count(n) as deleted_count
        """
        
        with graph_service.driver.session() as session:
            result = session.run(cypher_query, url=node_data.url)
            record = result.single()
            
            if record and record["deleted_count"] > 0:
                return {"message": "Node deleted successfully", "count": record["deleted_count"]}
            else:
                raise HTTPException(status_code=404, detail="Node not found")
    except neo4j.exceptions.ClientError as e:
        logger.error(f"Neo4j client error: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Invalid query: {str(e)}")
    except Exception as e:
        logger.error(f"Error deleting node: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete node: {str(e)}")

@app.post("/api/graph/relationship")
async def add_relationship(relationship_data: RelationshipData):
    """Add a new relationship between nodes in the knowledge graph"""
    if not graph_service or not graph_service.driver:
        raise HTTPException(status_code=503, detail="Graph database service not available")
    
    try:
        result = graph_service.add_relationship(
            relationship_data.source_url,
            relationship_data.target_url,
            relationship_data.rel_type,
            relationship_data.properties
        )
        
        if result:
            return {"message": "Relationship added successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to add relationship")
    except Exception as e:
        logger.error(f"Error adding relationship: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to add relationship: {str(e)}")

@app.delete("/api/graph/relationship")
async def delete_relationship(relationship_data: RelationshipDeleteRequest):
    """Delete a relationship between nodes in the knowledge graph"""
    if not graph_service or not graph_service.driver:
        raise HTTPException(status_code=503, detail="Graph database service not available")
    
    try:
        # We need to use a different approach because Neo4j doesn't support parameter substitution for relationship types
        # Create a Cypher query to delete the relationship based on the type
        rel_type = relationship_data.rel_type
        
        # Sanitize the relationship type to prevent injection
        if not re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', rel_type):
            raise HTTPException(status_code=400, detail="Invalid relationship type format")
        
        cypher_query = f"""
        MATCH (source {{url: $source_url}})-[r:{rel_type}]->(target {{url: $target_url}})
        DELETE r
        RETURN count(r) as deleted_count
        """
        
        with graph_service.driver.session() as session:
            result = session.run(
                cypher_query, 
                source_url=relationship_data.source_url, 
                target_url=relationship_data.target_url
            )
            record = result.single()
            
            if record and record["deleted_count"] > 0:
                return {"message": f"Relationship deleted successfully", "count": record["deleted_count"]}
            else:
                raise HTTPException(status_code=404, detail="Relationship not found")
    except neo4j.exceptions.ClientError as e:
        logger.error(f"Neo4j client error: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Invalid query: {str(e)}")
    except Exception as e:
        logger.error(f"Error deleting relationship: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete relationship: {str(e)}")

@app.post("/api/graph/query")
async def run_custom_query(request: GraphQueryRequest):
    """Run a custom Cypher query on the knowledge graph"""
    if not graph_service or not graph_service.driver:
        raise HTTPException(status_code=503, detail="Graph database service not available")
    
    try:
        with graph_service.driver.session() as session:
            result = session.run(request.cypher_query)
            data = [record.data() for record in result]
        
        return {"results": data}
    except Exception as e:
        logger.error(f"Error executing custom query: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to execute query: {str(e)}")

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

@app.delete("/api/conversation/{session_id}")
async def clear_conversation(session_id: str):
    """Clear the conversation history for a specific session"""
    try:
        conversation_service.clear_memory(session_id)
        return {"message": f"Conversation cleared for session {session_id}"}
    except Exception as e:
        logger.error(f"Error clearing conversation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to clear conversation: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 