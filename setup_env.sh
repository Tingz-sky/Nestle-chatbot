#!/bin/bash

# Environment setup for Nestle Chatbot

# Azure Search configuration
export AZURE_SEARCH_ENDPOINT="https://nestlesearch.search.windows.net"
export AZURE_SEARCH_INDEX="nestle-content-index"

# Azure OpenAI configuration
export AZURE_OPENAI_ENDPOINT="https://nestleopenai.openai.azure.com"
export AZURE_OPENAI_DEPLOYMENT="gpt-35-turbo"

# Azure Key Vault configuration
export AZURE_KEYVAULT_NAME="nestlechatbot-kv"
export AZURE_KEYVAULT_URL="https://nestlechatbot-kv.vault.azure.net/"

# Neo4j configuration - Local development
export NEO4J_URI="neo4j://localhost:7687"
export NEO4J_USER="neo4j"

# Neo4j configuration - Aura cloud connection (commented out)
# export NEO4J_URI="neo4j+s://e6acfbcb.databases.neo4j.io"
# export NEO4J_USER="neo4j"
# Password retrieved from Key Vault: NEO4J-AURA-PASSWORD
# export NEO4J_AURA_PASSWORD="your-password-here"

# For local development when Key Vault is not available
# export AZURE_SEARCH_KEY="your-key-here"
# export AZURE_OPENAI_KEY="your-key-here"
# export AZURE_OPENAI_DEPLOYMENT="nestle-gpt4o" 
