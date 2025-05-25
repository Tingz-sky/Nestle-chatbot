import os
import sys
import logging
import subprocess
import argparse
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("nestle-chatbot")

# Reduce Azure SDK logging verbosity
logging.getLogger('azure').setLevel(logging.WARNING)

def check_env_variables():
    """Check if required environment variables are set"""
    required_vars = [
        "AZURE_SEARCH_ENDPOINT", 
        "AZURE_SEARCH_INDEX",
        "AZURE_KEYVAULT_NAME"
    ]
    
    # Try to load environment variables from setup_env.sh
    try:
        with open('setup_env.sh', 'r') as f:
            for line in f:
                if line.startswith('export '):
                    var_def = line.strip().replace('export ', '')
                    if '=' in var_def:
                        key, value = var_def.split('=', 1)
                        os.environ[key] = value.strip('"').strip("'")
        logger.info("Loaded environment variables from setup_env.sh")
    except Exception as e:
        logger.warning(f"Could not load from setup_env.sh: {e}")
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.warning(f"Missing environment variables: {', '.join(missing_vars)}")
        logger.warning("Some functionality may be limited.")
    else:
        logger.info("All required environment variables are set.")
    
    # Fetch secrets from Key Vault and set as environment variables
    try:
        # Import here to avoid circular imports
        sys.path.append(os.path.join(os.getcwd(), 'backend'))
        from services.keyvault_service import get_secret
        
        # Get Azure Search Key
        search_key = get_secret("AZURE-SEARCH-KEY")
        if search_key:
            os.environ["AZURE_SEARCH_KEY"] = search_key
            logger.info("Retrieved Azure Search Key from Key Vault")
        
        # Get Neo4j Password
        neo4j_password = get_secret("NEO4J-PASSWORD")
        if neo4j_password:
            os.environ["NEO4J_PASSWORD"] = neo4j_password
            logger.info("Retrieved Neo4j Password from Key Vault")
        
        # Get Azure OpenAI Key
        openai_key = get_secret("AZURE-OPENAI-KEY")
        if openai_key:
            os.environ["AZURE_OPENAI_KEY"] = openai_key
            logger.info("Retrieved Azure OpenAI Key from Key Vault")
    except Exception as e:
        logger.error(f"Failed to retrieve secrets from Key Vault: {e}")
        logger.warning("Using fallback method or missing secrets")

def start_backend():
    """Start the FastAPI backend server"""
    try:
        logger.info("Starting backend server...")
        os.chdir("backend")
        
        # Add current directory to Python path
        sys.path.append(os.getcwd())
        
        # Set environment variable
        os.environ["PYTHONPATH"] = os.getcwd()
        
        # Ensure environment variables are passed to subprocess
        env = os.environ.copy()
        
        subprocess.run(
            ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"],
            check=True,
            env=env
        )
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to start backend server: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Backend server stopped.")
        os.chdir("..")  # Return to original directory

def start_frontend():
    """Start the React frontend development server"""
    try:
        logger.info("Starting frontend development server...")
        os.chdir("frontend")
        
        # Check if node_modules exists
        if not Path("node_modules").exists():
            logger.info("Installing frontend dependencies...")
            subprocess.run(["npm", "install"], check=True)
        
        subprocess.run(["npm", "start"], check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to start frontend: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Frontend server stopped.")

def scrape_data():
    """Run the web scraper to update data"""
    try:
        logger.info("Starting web scraper...")
        os.chdir("backend")
        sys.path.append(os.getcwd())
        
        from services.web_scraper import WebScraper
        
        scraper = WebScraper(base_url="https://www.madewithnestle.ca/")
        data = scraper.scrape_website()
        
        logger.info(f"Scraped {len(data)} pages successfully.")
        
        os.chdir("..")
    except Exception as e:
        logger.error(f"Failed to run web scraper: {e}")
        sys.exit(1)

def update_search_index():
    """Update the Azure Search index with scraped data"""
    try:
        logger.info("Updating search index...")
        os.chdir("backend")
        sys.path.append(os.getcwd())
        
        from services.search_service import AzureSearchService
        
        service = AzureSearchService(
            endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
            key=os.getenv("AZURE_SEARCH_KEY"),
            index_name=os.getenv("AZURE_SEARCH_INDEX")
        )
        
        result = service.refresh_index()
        
        if result:
            logger.info("Search index updated successfully.")
        else:
            logger.error("Failed to update search index.")
            
        os.chdir("..")
    except Exception as e:
        logger.error(f"Failed to update search index: {e}")
        sys.exit(1)

def build_knowledge_graph():
    """Build the knowledge graph from scraped data"""
    try:
        logger.info("Building knowledge graph...")
        import json
        
        os.chdir("backend")
        sys.path.append(os.getcwd())
        
        from services.graph_service import GraphRAGService
        
        data_path = '../data/scraped_data.json'
        if not os.path.exists(data_path):
            data_path = 'data/scraped_data.json'
            if not os.path.exists(data_path):
                if os.path.exists('../data/scraped_data.json'):
                    import shutil
                    os.makedirs('data', exist_ok=True)
                    shutil.copy('../data/scraped_data.json', 'data/scraped_data.json')
                    data_path = 'data/scraped_data.json'
        
        try:
            with open(data_path, 'r') as f:
                data = json.load(f)
        except FileNotFoundError:
            logger.error(f"Cannot find scraped data file at {data_path}")
            logger.info("Using empty data set")
            data = []
        
        service = GraphRAGService(
            uri=os.getenv("NEO4J_URI"),
            user=os.getenv("NEO4J_USER"),
            password=os.getenv("NEO4J_PASSWORD")
        )
        
        result = service.build_knowledge_graph(data)
        
        if result:
            logger.info("Knowledge graph built successfully.")
        else:
            logger.error("Failed to build knowledge graph.")
            
        os.chdir("..")
    except Exception as e:
        logger.error(f"Failed to build knowledge graph: {str(e)}")
        sys.exit(1)

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Nestle Chatbot CLI")
    
    # Define command line arguments
    parser.add_argument("--backend", action="store_true", help="Start the backend server")
    parser.add_argument("--frontend", action="store_true", help="Start the frontend development server")
    parser.add_argument("--scrape", action="store_true", help="Run the web scraper")
    parser.add_argument("--update-index", action="store_true", help="Update the search index")
    parser.add_argument("--build-graph", action="store_true", help="Build the knowledge graph")
    
    args = parser.parse_args()
    
    # Check environment variables
    check_env_variables()
    
    # Process arguments
    if args.scrape:
        scrape_data()
    
    if args.update_index:
        update_search_index()
    
    if args.build_graph:
        build_knowledge_graph()
    
    if args.backend:
        start_backend()
    
    if args.frontend:
        start_frontend()
    
    # If no arguments provided, print help
    if not any(vars(args).values()):
        parser.print_help()

if __name__ == "__main__":
    main() 