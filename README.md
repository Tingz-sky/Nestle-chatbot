# Nestle AI Chatbot

A modern conversational AI chatbot for the Nestle website, leveraging Azure OpenAI, Cognitive Search, and Knowledge Graph technology.

## Live Demo

Access the deployed chatbot here: [Nestle AI Chatbot](https://happy-plant-09497fa0f.6.azurestaticapps.net)

## Table of Contents

- [Technology Stack](#technology-stack)
- [Implementation Approach](#implementation-approach)
- [Local Setup](#local-setup)
- [Azure Deployment](#azure-deployment)
- [Project Structure](#project-structure)
- [Known Limitations](#known-limitations)
- [Additional Features](#additional-features)

## Technology Stack

### Backend
- Python 3.10+
- FastAPI
- Azure OpenAI Service
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

## Implementation Approach

This chatbot implements a Graph-based Retrieval Augmented Generation (GraphRAG) architecture that enhances traditional RAG with structured knowledge representation. Here's how the system works:

### 1. Web Scraping and Data Collection
- The system uses a custom web scraper built with Selenium and BeautifulSoup to extract content from the Made with Nestle website
- The scraper navigates through product pages, recipes, and information pages to collect comprehensive data
- Content is processed, cleaned, and stored for further use

### 2. Knowledge Graph Construction
- Information extracted from the website is organized into a graph structure using Neo4j
- Entities are represented as nodes
- Relationships between entities are captured as edges
- This approach preserves semantic relationships between different pieces of information

### 3. Multi-step Retrieval Process
The chatbot uses a sophisticated retrieval process:

1. **Graph-Based Retrieval**: When a user asks a question, the system first attempts to find relevant information in the knowledge graph
   - For structured queries, the graph provides precise answers
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
  - Add new nodes and relationships
  - Run custom queries to extract specific information
  - Update existing information

### Security and Scalability
- Azure Key Vault securely stores all sensitive credentials
- The architecture is designed to scale with increasing content and user load
- System components are decoupled for easier maintenance and updates

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

## Azure Deployment

The Nestle AI Chatbot is deployed on Microsoft Azure using several managed services. This section covers both deployment architecture and setup instructions.

### Deployed Azure Resources

The chatbot utilizes the following Azure resources:

1. **Resource Group**: `nestlechatbot-rg` (East US)
   - Central management for all project resources
   - Simplifies resource administration and billing

2. **Azure OpenAI Service**: `nestleopenai` (East US)
   - Provides advanced language understanding and generation
   - Supports conversation context and natural responses

3. **Azure Cognitive Search**: `nestlechatbot-search` (Central US)
   - Vector search for semantic understanding
   - Full-text search capabilities for content retrieval

4. **Azure App Service**: `nestlechatbot-api` (Canada Central)
   - Hosts the FastAPI backend application
   - Managed platform with automatic scaling

5. **Azure Static Web App**: `nestlechatbot-frontend` (East US 2)
   - Hosts the React frontend application
   - Integrated CDN for fast content delivery

6. **Azure Key Vault**: `nestlechatbot-kv` (East US)
   - Secure credential storage and management
   - Integrates with other Azure services for authentication

### Deployment Options

#### Option 1: Automatic Setup

This project includes a script to automatically provision all required Azure resources:

```bash
# Run the included setup script
python setup_azure_resources.py
```

The script creates all necessary resources and generates a `setup_env.sh` file with environment variables.

#### Option 2: Manual Configuration

If you prefer to configure resources manually:

1. Create an Azure OpenAI service in your Azure portal
2. Deploy a model and note the deployment name
3. Create an Azure Cognitive Search service
4. Create a search index with the schema defined in `azure-deployment/search-index-schema.json`
5. Create a Key Vault to store your secrets
6. Create an App Service for the backend
7. Create a Static Web App for the frontend

### CI/CD Pipeline

The project uses GitHub Actions for automated deployment:

1. **Backend Pipeline**
   - Triggers on push to main branch
   - Python dependencies installation
   - Unit tests execution
   - Deployment to Azure App Service

2. **Frontend Pipeline**
   - Triggers on push to main branch or pull request
   - Node.js setup and dependency installation
   - Build process with environment variables
   - Deployment to Azure Static Web Apps

### GitHub Configuration

Configure the following GitHub secrets for automated deployment:
- `AZURE_CREDENTIALS`: Service principal credentials
- `AZURE_WEBAPP_PUBLISH_PROFILE`: App Service publish profile
- `AZURE_STATIC_WEB_APPS_API_TOKEN`: Static Web App deployment token

### Neo4j Aura Access

The project uses a Neo4j Aura database for the knowledge graph:

1. The Neo4j URI and username are already configured in the setup files
2. The password is stored securely and not included in the repository
3. **To obtain the password, please email tianze.zhang@mail.utoronto.ca**
4. Once obtained, set it as an environment variable: `export NEO4J_PASSWORD=<provided-password>`

## Project Structure

```
nestle-chatbot/
├── backend/           # FastAPI backend application
│   ├── main.py        # Main application entry point
│   ├── services/      # Service modules for different functionalities
│   └── models/        # Data models and schemas
├── frontend/          # React frontend application
│   ├── src/           # Source code
│   ├── public/        # Static assets
│   └── package.json   # Dependencies and scripts
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