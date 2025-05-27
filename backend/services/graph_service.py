import logging
from typing import List, Dict, Any, Optional
import neo4j
from neo4j import GraphDatabase
import json
import re

logger = logging.getLogger(__name__)

class GraphRAGService:
    def __init__(self, uri: str, user: str, password: str, openai_service=None):
        self.uri = uri
        self.user = user
        self.password = password
        self.openai_service = openai_service  # OpenAI service instance
        
        # Initialize Neo4j driver if credentials are provided
        if uri and user and password:
            try:
                self.driver = GraphDatabase.driver(uri, auth=(user, password))
                # Verify connection
                with self.driver.session() as session:
                    result = session.run("RETURN 1")
                    result.single()
                logger.info(f"Connected to Neo4j database at {uri}")
            except Exception as e:
                logger.error(f"Failed to connect to Neo4j: {str(e)}")
                self.driver = None
        else:
            logger.warning("Neo4j credentials not provided")
            self.driver = None
    
    def query(self, query_text: str) -> List[Dict[str, Any]]:
        """
        Query the knowledge graph based on the user's question
        """
        if not self.driver:
            logger.warning("Neo4j driver not initialized, returning empty results")
            return []
        
        try:
            # If OpenAI service is available, use it to generate a Cypher query
            if self.openai_service:
                try:
                    cypher_query = self.openai_service.generate_cypher_query(query_text)
                    logger.info(f"Generated Cypher query: {cypher_query}")
                    
                    # If the query contains parameters, extract them
                    params = {"query": query_text}
                    param_matches = re.findall(r'\$(\w+)', cypher_query)
                    for param in param_matches:
                        if param != 'query':
                            params[param] = self._extract_entity_value(query_text, param)
                    
                    # Execute the generated query
                    with self.driver.session() as session:
                        result = session.run(cypher_query, params)
                        records = [record.data() for record in result]
                    
                    if records:
                        return records
                except Exception as e:
                    logger.error(f"Error executing generated Cypher query: {str(e)}")
            
            # Fallback to keyword-based search if OpenAI query fails or is not available
            keywords = self._extract_keywords(query_text)
            
            # Define the Cypher query to search for relevant nodes
            cypher_query = """
            MATCH (n:Content)
            WHERE any(keyword IN $keywords WHERE toLower(n.title) CONTAINS toLower(keyword)
                  OR toLower(n.content) CONTAINS toLower(keyword))
            RETURN n.title as title, n.content as content, n.url as url
            ORDER BY size([keyword IN $keywords WHERE toLower(n.title) CONTAINS toLower(keyword)]) +
                     size([keyword IN $keywords WHERE toLower(n.content) CONTAINS toLower(keyword)]) DESC
            LIMIT 5
            """
            
            # Execute the query with error handling
            try:
                with self.driver.session() as session:
                    result = session.run(cypher_query, keywords=keywords)
                    records = [record.data() for record in result]
                return records
            except neo4j.exceptions.ServiceUnavailable:
                logger.error("Neo4j service unavailable. Check if Neo4j is running.")
                return []
            except Exception as e:
                logger.error(f"Error executing Neo4j query: {str(e)}")
                return []
        
        except Exception as e:
            logger.error(f"Error querying knowledge graph: {str(e)}")
            return []
    
    def add_node(self, node_data: Dict[str, Any]) -> bool:
        """Add a new node to the knowledge graph"""
        if not self.driver:
            logger.warning("Neo4j driver not initialized, cannot add node")
            return False
        
        try:
            # Extract node properties
            title = node_data.get("title", "")
            content = node_data.get("content", "")
            url = node_data.get("url", "")
            node_type = node_data.get("type", "Entity")
            
            # If URL is empty and this is an Entity, generate one based on title
            if not url and node_type == "Entity":
                url = f"entity:{title.replace(' ', '')}"
            
            # Create appropriate label based on type
            if node_type == "Entity" or node_type == "Product" or node_type == "Category" or node_type == "Recipe" or node_type == "Ingredient":
                label = node_type
            else:
                label = "Content"  # Default label for Page type and others
            
            # Create Cypher query with dynamic label
            cypher_query = f"""
            MERGE (n:{label} {{url: $url}})
            SET n.title = $title,
                n.content = $content,
                n.type = $node_type,
                n.updated = timestamp()
            RETURN n
            """
            
            # Execute the query
            with self.driver.session() as session:
                result = session.run(
                    cypher_query, 
                    title=title, 
                    content=content, 
                    url=url, 
                    node_type=node_type
                )
                return result.single() is not None
        
        except Exception as e:
            logger.error(f"Error adding node to graph: {str(e)}")
            return False
    
    def add_relationship(self, source_url: str, target_url: str, rel_type: str, properties: Dict[str, Any] = None) -> bool:
        """Add a relationship between two nodes"""
        if not self.driver:
            logger.warning("Neo4j driver not initialized, cannot add relationship")
            return False
        
        if not properties:
            properties = {}
        
        try:
            # Create Cypher query - updated to match any node type
            cypher_query = """
            MATCH (source {url: $source_url})
            MATCH (target {url: $target_url})
            MERGE (source)-[r:%s]->(target)
            """ % rel_type
            
            # Add properties if provided
            if properties:
                set_clauses = []
                for key in properties:
                    set_clauses.append(f"r.{key} = ${key}")
                
                if set_clauses:
                    cypher_query += "SET " + ", ".join(set_clauses)
            
            cypher_query += "\nRETURN r"
            
            # Execute the query
            with self.driver.session() as session:
                params = {"source_url": source_url, "target_url": target_url, **properties}
                result = session.run(cypher_query, **params)
                return result.single() is not None
        
        except Exception as e:
            logger.error(f"Error adding relationship to graph: {str(e)}")
            return False
    
    def build_knowledge_graph(self, data: List[Dict[str, Any]]) -> bool:
        """Build the knowledge graph from scraped data"""
        if not self.driver:
            logger.warning("Neo4j driver not initialized, cannot build knowledge graph")
            return False
        
        try:
            # Clear existing data (optional)
            self._clear_graph()
            
            # Add nodes
            for item in data:
                # Add the page as a node
                self.add_node({
                    "title": item.get("title", ""),
                    "content": item.get("content", ""),
                    "url": item.get("url", ""),
                    "type": "Page"
                })
                
                # Process entities from the page and add relationships
                # Try to use OpenAI for entity extraction if available
                if self.openai_service:
                    entities = self._extract_entities_with_openai(item.get("content", ""))
                else:
                    entities = self._extract_entities(item.get("content", ""))
                
                for entity in entities:
                    # Add entity node
                    entity_url = f"entity:{entity}"
                    self.add_node({
                        "title": entity,
                        "content": "",
                        "url": entity_url,
                        "type": "Entity"
                    })
                    
                    # Add relationship from page to entity
                    self.add_relationship(
                        item.get("url", ""),
                        entity_url,
                        "MENTIONS",
                        {"count": 1}
                    )
                
                # Create relationships between pages based on URLs
                for other_item in data:
                    if item != other_item and item.get("url", "") in other_item.get("content", ""):
                        self.add_relationship(
                            other_item.get("url", ""),
                            item.get("url", ""),
                            "LINKS_TO",
                            {"type": "hyperlink"}
                        )
            
            return True
        
        except Exception as e:
            logger.error(f"Error building knowledge graph: {str(e)}")
            return False
    
    def _extract_keywords(self, text: str) -> List[str]:
        """
        Extract keywords from the input text
        This is a simplified implementation - a more sophisticated approach
        would use NLP techniques
        """
        # Remove common stopwords
        stopwords = {"a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for", "with", "by"}
        words = text.lower().split()
        keywords = [word for word in words if word not in stopwords and len(word) > 2]
        
        return keywords
    
    def _extract_entities(self, text: str) -> List[str]:
        """
        Extract entities from the text
        This is a simplified implementation - a real implementation would
        use NER (Named Entity Recognition) from an NLP library
        """
        # For demo purposes, we'll just use some product categories and terms related to Nestle
        nestle_products = [
            "KitKat", "Nescafe", "Nesquik", "Coffee", "Chocolate", "Water", "Milk", 
            "Recipe", "Nutrition", "Sustainability", "Cocoa", "AERO", "SMARTIES",
            "QUALITY STREET", "BOOST", "Coffee-mate"
        ]
        
        found_entities = []
        for product in nestle_products:
            if product.lower() in text.lower():
                found_entities.append(product)
        
        return found_entities
    
    def _extract_entities_with_openai(self, text: str) -> List[str]:
        """
        Use OpenAI to extract entities from text
        """
        if not self.openai_service:
            return self._extract_entities(text)
        
        try:
            # Truncate text if too long
            max_length = 1000
            if len(text) > max_length:
                text = text[:max_length] + "..."
            
            # Create a prompt for entity extraction
            system_message = "You are an expert in extracting product and brand entities from text. Extract Nestle-related entities only."
            user_message = f"Extract all Nestle product names, brand names, and key concepts from this text. Return them as a JSON array of strings:\n\n{text}"
            
            # Call OpenAI
            response = self.openai_service.generate_response(
                query=user_message,
                context=[],
                temperature=0.3,
                max_tokens=200
            )
            
            # Try to parse JSON response
            try:
                # Extract JSON array from the response
                match = re.search(r'\[.*\]', response, re.DOTALL)
                if match:
                    json_str = match.group(0)
                    entities = json.loads(json_str)
                    return entities
                else:
                    # Fallback to simple extraction
                    return self._extract_entities(text)
            except json.JSONDecodeError:
                return self._extract_entities(text)
                
        except Exception as e:
            logger.error(f"Error extracting entities with OpenAI: {str(e)}")
            return self._extract_entities(text)
    
    def _extract_entity_value(self, text: str, param_name: str) -> str:
        """Extract a specific entity value from text based on parameter name"""
        # This is a simplified implementation
        # In a real system, you would use more sophisticated NLP techniques
        lower_text = text.lower()
        param_name = param_name.lower()
        
        if "product" in param_name:
            products = ["kitkat", "nescafe", "nesquik", "aero", "smarties", "boost"]
            for product in products:
                if product in lower_text:
                    return product
        
        if "category" in param_name:
            categories = ["chocolate", "coffee", "milk", "water", "nutrition"]
            for category in categories:
                if category in lower_text:
                    return category
                    
        # Default value - just return the param name
        return param_name
    
    def _clear_graph(self):
        """Clear all data from the graph"""
        if not self.driver:
            return
            
        try:
            with self.driver.session() as session:
                session.run("MATCH (n) DETACH DELETE n")
            logger.info("Cleared all data from Neo4j graph")
        except Exception as e:
            logger.error(f"Error clearing graph: {str(e)}")
    
    def close(self):
        """Close the Neo4j driver connection"""
        if self.driver:
            self.driver.close() 