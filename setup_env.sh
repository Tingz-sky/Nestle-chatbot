#!/bin/bash

# Azure Key Vault configuration
export AZURE_KEYVAULT_NAME="nestlechatbot-kv"
export AZURE_KEYVAULT_URL="https://nestlechatbot-kv.vault.azure.net/"

# Azure Search configuration (endpoint and index name can stay, but key will be retrieved from Key Vault)
export AZURE_SEARCH_ENDPOINT="https://nestlechatbot-search.search.windows.net"
export AZURE_SEARCH_INDEX="nestle-content-index"

# Neo4j configuration
export NEO4J_URI="bolt://localhost:7687"
export NEO4J_USER="neo4j"

# Azure OpenAI configuration (endpoints can stay, but keys will be retrieved from Key Vault)
export AZURE_OPENAI_ENDPOINT="https://nestleopenai.openai.azure.com/"
export AZURE_OPENAI_DEPLOYMENT="nestle-gpt4o" 
