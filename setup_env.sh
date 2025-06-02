#!/bin/bash

# Environment setup for Nestle Chatbot

# Azure Search configuration
export AZURE_SEARCH_ENDPOINT="https://nestlesearch.search.windows.net"
export AZURE_SEARCH_INDEX="nestle-content-index"

# Azure OpenAI configuration
export AZURE_OPENAI_ENDPOINT="https://nestleopenai.openai.azure.com"
export AZURE_OPENAI_DEPLOYMENT="nestle-gpt4o"

# Azure Key Vault configuration
export AZURE_KEYVAULT_NAME="nestlechatbot-kv"
export AZURE_KEYVAULT_URL="https://nestlechatbot-kv.vault.azure.net/"

# Neo4j Aura configuration
export NEO4J_URI="neo4j+s://e6acfbcb.databases.neo4j.io"
export NEO4J_USER="neo4j"
# NOTE: Neo4j Aura password is not included here for security reasons
# Please email tianze.zhang@mail.utoronto.ca to obtain the password
