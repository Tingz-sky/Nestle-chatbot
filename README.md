# Nestle AI Chatbot

A modern conversational AI chatbot for the Nestle website, leveraging Azure OpenAI, Cognitive Search, and Knowledge Graph technology.

## Live Demo

Access the deployed chatbot here: [Nestle AI Chatbot](https://happy-plant-09497fa0f.6.azurestaticapps.net)

## Table of Contents

- [Technology Stack](#technology-stack)
- [Features](#features)
- [Implementation Approach](#implementation-approach)
- [Cloud Deployment](#cloud-deployment)
- [Local Setup](#local-setup)
- [Azure Resource Setup](#azure-resource-setup)
- [Project Structure](#project-structure)
- [Known Limitations](#known-limitations)
- [Additional Features](#additional-features)

## Technology Stack

### Backend
- Python 3.10+
- FastAPI
- Azure OpenAI Service (GPT-3.5/GPT-4)
- Azure Cognitive Search
- Neo4j Graph Database (Neo4j Aura)
- LangChain for orchestration

### Frontend
- React.js
- Styled Components
- Axios for API communication

### Deployment
- Azure App Service
- Azure Static Web Apps
- Azure Key Vault for secure secrets management

## Features

- **Conversational AI**: Natural language interaction using Azure OpenAI
- **Knowledge Graph**: Graph-based representation of Nestle product relationships
- **Semantic Search**: Find relevant information across Nestle content
- **Knowledge Management**: Interface for managing the knowledge graph
- **Responsive Design**: Works on mobile and desktop devices

## Implementation Approach

This chatbot implements a Graph-based Retrieval Augmented Generation (GraphRAG) architecture that enhances traditional RAG with structured knowledge representation. Here's how the system works:

### 1. Web Scraping and Data Collection
- The system uses a custom web scraper built with Selenium and BeautifulSoup to extract content from the Made with Nestle website
- The scraper navigates through product pages, recipes, and information pages to collect comprehensive data
- Content is processed, cleaned, and stored for further use

### 2. Knowledge Graph Construction
- Information extracted from the website is organized into a graph structure using Neo4j
- Entities (products, ingredients, recipes) are represented as nodes
- Relationships between entities (contains, mentions, related_to) are captured as edges
- This approach preserves semantic relationships between different pieces of information

### 3. Multi-step Retrieval Process
The chatbot uses a sophisticated retrieval process:

1. **Graph-Based Retrieval**: When a user asks a question, the system first attempts to find relevant information in the knowledge graph
   - For structured queries (e.g., "What ingredients are in KitKat?"), the graph provides precise answers
   - The system uses natural language understanding to generate appropriate Cypher queries

2. **Vector Search Fallback**: If graph retrieval doesn't yield sufficient results, the system falls back to vector search
   - Content is indexed in Azure Cognitive Search with vector embeddings
   - Semantic search capabilities find relevant documents even when exact keywords aren't present

### 4. Contextual Response Generation
- Retrieved information is passed to Azure OpenAI for response generation
- The system maintains conversation context, allowing for follow-up questions
- Response formatting includes proper attribution and source references

### 5. Interactive Knowledge Management
- A web interface allows authorized users to:
  - View and explore the knowledge graph
  - Add new nodes (entities) and relationships
  - Run custom queries to extract specific information
  - Update existing information

### GraphRAG vs. Traditional RAG
The graph-based approach offers several advantages:
- Preserves structural relationships between entities
- Enables more precise answers to specific queries
- Provides better handling of complex, multi-hop queries
- Allows for reasoning over the knowledge base

### Security and Scalability
- Azure Key Vault securely stores all sensitive credentials
- The architecture is designed to scale with increasing content and user load
- System components are decoupled for easier maintenance and updates

This implementation aligns with modern AI best practices by combining structured knowledge representation with advanced language models, resulting in a more accurate and context-aware chatbot experience.

## Cloud Deployment

The Nestle AI Chatbot is fully deployed on Microsoft Azure, utilizing several managed services to ensure reliability, scalability, and security. This section outlines the current deployment architecture and provides guidance for deploying similar solutions.

### Deployed Azure Resources

The chatbot is deployed using the following Azure resources:

1. **Resource Group**: `nestlechatbot-rg` (East US)
   - Centralized management of all chatbot resources

2. **Azure OpenAI Service**: `nestleopenai` (East US)
   - Service Tier: Standard (S0)
   - Custom Subdomain: nestleopenai.openai.azure.com
   - Model Deployment: GPT-3.5 Turbo for conversational AI capabilities

3. **Azure Cognitive Search**: `nestlechatbot-search` (Central US)
   - Tier: Free
   - Configuration: 1 replica, 1 partition
   - Vector search capability for semantic document retrieval

4. **Azure App Service**: `nestlechatbot-api` (Canada Central)
   - Hosting the FastAPI backend
   - Runtime: Python 3.10
   - HTTPS Only: Enabled
   - CORS configured for static web app frontend
   - Command: `cd backend && gunicorn --bind=0.0.0.0 --timeout 600 --worker-class uvicorn.workers.UvicornWorker main:app`

5. **Azure Static Web App**: `nestlechatbot-frontend` (East US 2)
   - Hosting the React frontend
   - Tier: Free
   - Default URL: happy-plant-09497fa0f.6.azurestaticapps.net
   - Connected to GitHub repository for CI/CD

6. **Azure Key Vault**: `nestlechatbot-kv` (East US)
   - Securely storing sensitive credentials (API keys, database passwords)
   - Managed identity integration with App Service

### CI/CD Pipeline

The project uses GitHub Actions for automated deployment:

1. **Backend Pipeline**: `.github/workflows/main_nestlechatbot-api.yml`
   - Triggers on push to main branch
   - Python dependencies installation
   - Unit tests execution
   - Deployment to Azure App Service

2. **Frontend Pipeline**: `.github/workflows/azure-static-web-apps-happy-plant-09497fa0f.yml`
   - Triggers on push to main branch or pull request
   - Node.js setup and dependency installation
   - Build process with environment variables
   - Deployment to Azure Static Web Apps

### Deployment Steps

To deploy a similar chatbot application to Azure:

1. **Set up Azure Resources**:
   ```bash
   # Run the included setup script
   python setup_azure_resources.py
   
   # Or manually create resources via Azure Portal or CLI
   ```

2. **Configure GitHub Secrets**:
   - `AZURE_CREDENTIALS`: Service principal credentials for deployment
   - `AZURE_WEBAPP_PUBLISH_PROFILE`: Publish profile for App Service
   - `AZURE_STATIC_WEB_APPS_API_TOKEN`: Deployment token for Static Web App

3. **Deploy Backend**:
   ```bash
   # Initial deployment (subsequent deployments handled by GitHub Actions)
   az webapp deployment source config-local-git --name nestlechatbot-api --resource-group nestlechatbot-rg
   git remote add azure <git-url-from-previous-command>
   git push azure main
   ```

4. **Deploy Frontend**:
   ```bash
   # Build React app locally
   cd frontend
   npm run build
   
   # Deploy to Static Web App (initial deployment)
   az staticwebapp deploy --source-location ./build --name nestlechatbot-frontend --resource-group nestlechatbot-rg
   ```

### Monitoring and Maintenance

The deployed application can be monitored using:

1. **Azure Application Insights**:
   - Real-time metrics on performance and usage
   - Error tracking and diagnostics

2. **Azure Log Analytics**:
   - Centralized logging for all components
   - Custom queries for specific scenarios

3. **Azure Monitor Alerts**:
   - Proactive notification of issues
   - Automated scaling based on usage patterns

### Environment Configuration

The production environment is configured with:

1. **CORS Settings**:
   - App Service is configured to allow requests only from the Static Web App domain
   - Headers properly set for secure cross-origin communication

2. **Security Measures**:
   - HTTPS enforced for all communications
   - Managed identities used for service-to-service authentication
   - Key Vault for sensitive credential storage

3. **Performance Optimization**:
   - CDN integration for static content delivery
   - Appropriate caching policies
   - Asynchronous processing for long-running operations

### Best Practices

For optimal cloud deployment:

1. **Use Infrastructure as Code**: Maintain deployment templates (ARM, Terraform, or Bicep) for reproducibility
2. **Implement Staging Environments**: Test changes in staging before production deployment
3. **Version Control Configuration**: Keep environment-specific configurations in version control
4. **Regular Backups**: Schedule regular backups of the Neo4j database and other stateful components
5. **Cost Monitoring**: Set up budgets and alerts to monitor resource consumption
6. **Security Scans**: Regularly scan for vulnerabilities and apply security patches

By following this deployment approach, the Nestle AI Chatbot maintains high availability, security, and performance while minimizing operational overhead.

## Local Setup

### Prerequisites

- Anaconda or Miniconda
- Node.js 18+ and npm
- Git
- Azure subscription (for cloud resources)

### Step 1: Clone the Repository

```bash
git clone https://github.com/Tingz-sky/Nestle-chatbot.git
cd Nestle-chatbot
```

### Step 2: Set Up Conda Environment

1. Create and activate a Conda environment:

```bash
conda env create -f environment.yml
conda activate nestle-ai
```

If the environment file is not available, create one manually:

```bash
conda create -n nestle-ai python=3.10
conda activate nestle-ai
pip install -r requirements.txt
```

2. Set up environment variables:

Create a `.env` file in the project root with the following variables:

```
AZURE_OPENAI_ENDPOINT=https://nestleopenai.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=nestle-gpt4o
AZURE_OPENAI_KEY=<your-openai-key>

AZURE_SEARCH_ENDPOINT=https://nestlechatbot-search.search.windows.net
AZURE_SEARCH_KEY=<your-search-key>
AZURE_SEARCH_INDEX=nestle-content-index

NEO4J_URI=neo4j+s://e6acfbcb.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=<neo4j-password>
```

**Important Note**: The Neo4j Aura password is not included in this repository for security reasons. Please email tianze.zhang@mail.utoronto.ca to obtain the password for accessing the knowledge graph database.

Alternatively, source the provided environment setup file:

```bash
source setup_env.sh  # On Windows: source setup_env.bat
```

Note that you will still need to set the Neo4j password after sourcing this file:

```bash
export NEO4J_PASSWORD=<password-from-email>
```

### Step 3: Set Up Frontend

1. Navigate to the frontend directory:

```bash
cd frontend
```

2. Install dependencies:

```bash
npm install
```

### Step 4: Run the Application

1. Start the backend server (from the project root):

```bash
python run.py --backend
```

2. In a new terminal, start the frontend development server:

```bash
python run.py --frontend
```

Alternatively, you can start the frontend directly:

```bash
cd frontend
npm start
```

3. Access the application in your browser at http://localhost:3000

## Azure Resource Setup

This project includes a script to automatically provision all required Azure resources:

```bash
python setup_azure_resources.py
```

### Prerequisites for Azure Setup

1. Install the Azure CLI if you haven't already:
   - **Windows**: Download from [Microsoft's website](https://aka.ms/installazurecli)
   - **macOS**: `brew install azure-cli`
   - **Linux**: `curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash`

2. Login to your Azure account:
   ```bash
   az login
   ```

3. If you have multiple subscriptions, select the one you want to use:
   ```bash
   az account set --subscription <subscription-id>
   ```

### Running the Setup Script

The setup script will create:
- Resource Group: `nestlechatbot-rg`
- Azure OpenAI Service: `nestleopenai`
- Azure Cognitive Search: `nestlechatbot-search`
- Azure Key Vault: `nestlechatbot-kv`
- App Service Plan: `nestlechatbot-plan`
- Web App: `nestlechatbot-api`
- Static Web App: `nestlechatbot-frontend`

After running the script, you'll receive:
1. A generated `setup_env.sh` file with environment variables
2. Azure resource access details
3. Instructions for next steps

### Manual Azure Configuration

If you prefer to configure resources manually:

1. Create an Azure OpenAI service in your Azure portal
2. Deploy a model (e.g., GPT-4) and note the deployment name
3. Create an Azure Cognitive Search service
4. Create a search index with the schema defined in `azure-deployment/search-index-schema.json`
5. Create a Key Vault to store your secrets
6. Update your environment variables with the appropriate keys and endpoints

### Neo4j Aura Access

The project uses a Neo4j Aura database for the knowledge graph. For evaluation purposes:

1. The Neo4j URI and username are already configured in the setup files
2. The password is stored securely and not included in the repository
3. **To obtain the password, please email tianze.zhang@mail.utoronto.ca**
4. Once obtained, set it as an environment variable: `export NEO4J_PASSWORD=<provided-password>`

## Project Structure

```
nestle-chatbot/
├── backend/           # FastAPI backend application
├── frontend/          # React frontend application
├── azure-deployment/  # Azure deployment configuration
├── run.py             # Application entry point
├── requirements.txt   # Python dependencies
├── environment.yml    # Conda environment specification
└── setup_env.sh       # Environment setup script
```

## Known Limitations

- The chatbot requires Azure OpenAI and Cognitive Search services to function properly
- Local development requires setting up environment variables with valid Azure service credentials
- The knowledge graph requires access to the Neo4j Aura database (password available upon request via email)
- Queries are limited to Nestle product information contained in the knowledge base
- Azure OpenAI service quotas may limit the number of requests you can make

## Additional Features

- **Knowledge Graph Manager**: Visual interface for managing the product knowledge graph
- **Contextual Conversations**: The chatbot maintains context throughout the conversation
- **Custom Queries**: Support for advanced graph queries through the UI
- **CORS Support**: Configured for cross-origin requests
- **Error Handling**: Robust error handling and user feedback 