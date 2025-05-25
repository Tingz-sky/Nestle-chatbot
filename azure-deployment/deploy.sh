#!/bin/bash

# Azure Deployment Script for Nestle Chatbot
# This script deploys the Nestle Chatbot to Azure

# Exit on error
set -e

# Load environment variables from .env file
if [ -f .env ]; then
    echo "Loading environment variables from .env file"
    export $(grep -v '^#' .env | xargs)
else
    echo "No .env file found, make sure all required environment variables are set manually"
fi

# Configuration variables
RESOURCE_GROUP="nestlechatbot-rg"
LOCATION="eastus"
APP_SERVICE_PLAN="nestlechatbot-plan"
WEBAPP_NAME="nestlechatbot-api"
SEARCH_SERVICE_NAME="nestlesearch"
SEARCH_SKU="standard"
SEARCH_INDEX_NAME="nestle-content-index"
STATIC_WEB_APP_NAME="nestlechatbot-frontend"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Helper functions
function print_section() {
    echo -e "\n${BLUE}==== $1 ====${NC}\n"
}

function print_success() {
    echo -e "${GREEN}$1${NC}"
}

function print_error() {
    echo -e "${RED}$1${NC}"
}

# Check if Azure CLI is installed
print_section "Checking prerequisites"
if ! command -v az &> /dev/null; then
    print_error "Azure CLI is not installed. Please install it first: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
    exit 1
fi
print_success "Azure CLI is installed"

# Login to Azure
print_section "Logging in to Azure"
az login
print_success "Logged in to Azure"

# Create resource group
print_section "Creating resource group"
az group create --name $RESOURCE_GROUP --location $LOCATION
print_success "Resource group created: $RESOURCE_GROUP"

# Create Azure Cognitive Search service
print_section "Creating Azure Cognitive Search service"
az search service create \
    --name $SEARCH_SERVICE_NAME \
    --resource-group $RESOURCE_GROUP \
    --sku $SEARCH_SKU \
    --location $LOCATION
print_success "Azure Cognitive Search service created: $SEARCH_SERVICE_NAME"

# Get the search service admin key
SEARCH_ADMIN_KEY=$(az search admin-key show --service-name $SEARCH_SERVICE_NAME --resource-group $RESOURCE_GROUP --query primaryKey -o tsv)

# Create Azure Cognitive Search index
print_section "Creating Azure Cognitive Search index"
az search index create \
    --name $SEARCH_INDEX_NAME \
    --service-name $SEARCH_SERVICE_NAME \
    --resource-group $RESOURCE_GROUP \
    --definition azure-deployment/search-index-schema.json
print_success "Azure Cognitive Search index created: $SEARCH_INDEX_NAME"

# Create App Service Plan
print_section "Creating App Service Plan"
az appservice plan create \
    --name $APP_SERVICE_PLAN \
    --resource-group $RESOURCE_GROUP \
    --sku B1 \
    --is-linux
print_success "App Service Plan created: $APP_SERVICE_PLAN"

# Create Web App
print_section "Creating Web App"
az webapp create \
    --name $WEBAPP_NAME \
    --resource-group $RESOURCE_GROUP \
    --plan $APP_SERVICE_PLAN \
    --runtime "PYTHON|3.10"
print_success "Web App created: $WEBAPP_NAME"

# Set environment variables for Web App
print_section "Setting environment variables for Web App"
az webapp config appsettings set \
    --name $WEBAPP_NAME \
    --resource-group $RESOURCE_GROUP \
    --settings \
    AZURE_SEARCH_ENDPOINT="https://$SEARCH_SERVICE_NAME.search.windows.net" \
    AZURE_SEARCH_KEY="$SEARCH_ADMIN_KEY" \
    AZURE_SEARCH_INDEX="$SEARCH_INDEX_NAME" \
    WEBSITES_PORT=8000
print_success "Environment variables set for Web App"

# Deploy backend code to Web App using git
print_section "Configuring deployment for Web App"
echo "This script does not automatically deploy the code."
echo "To deploy your code, run the following commands manually:"
echo "1. Configure local git deployment:"
echo "   az webapp deployment source config-local-git --name $WEBAPP_NAME --resource-group $RESOURCE_GROUP"
echo "2. Get the git repository URL:"
echo "   az webapp deployment source show --name $WEBAPP_NAME --resource-group $RESOURCE_GROUP --query repoUrl -o tsv"
echo "3. Add the remote to your local git repository:"
echo "   git remote add azure <git-url-from-previous-command>"
echo "4. Push your code to Azure:"
echo "   git push azure main"

# Create Static Web App for frontend
print_section "Creating Static Web App for frontend"
echo "To deploy the frontend, follow these steps:"
echo "1. Build the React app: cd frontend && npm run build"
echo "2. Use Azure Portal or VS Code to deploy the build folder to a Static Web App"

print_section "Deployment configuration completed"
print_success "Nestle Chatbot infrastructure has been provisioned successfully!"
print_success "Follow the steps above to complete the code deployment." 