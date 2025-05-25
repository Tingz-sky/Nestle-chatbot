# Azure Deployment Guide for Nestle Chatbot

This guide provides detailed steps to deploy the Nestle Chatbot application to Azure cloud services.

## Prerequisites

1. **Azure Account**: You need an active Azure subscription
2. **Azure CLI**: Install the [Azure CLI](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli)
3. **Git**: Make sure Git is installed and configured
4. **Local Setup**: Ensure your local project is ready for deployment with all code committed

## Automated Deployment

For convenience, we provide a deployment script that automates most of the Azure resource creation process:

```bash
# Make the script executable
chmod +x azure-deployment/deploy.sh

# Run the deployment script
./azure-deployment/deploy.sh
```

The script will:
1. Create a resource group
2. Create an Azure Cognitive Search service
3. Create the search index
4. Create an App Service Plan
5. Create a Web App for the backend
6. Configure environment variables

After running the script, you will need to manually:
1. Deploy the backend code to the Web App
2. Deploy the frontend to Azure Static Web Apps

## Manual Deployment

If you prefer to deploy manually, follow these steps:

### 1. Set up Azure Resources

```bash
# Login to Azure
az login

# Create Resource Group
az group create --name nestlechatbot-rg --location eastus

# Create Azure Cognitive Search service
az search service create --name nestlesearch --resource-group nestlechatbot-rg --sku standard --location eastus

# Get the admin key
SEARCH_ADMIN_KEY=$(az search admin-key show --service-name nestlesearch --resource-group nestlechatbot-rg --query primaryKey -o tsv)

# Create Search Index
az search index create --name nestle-content-index --service-name nestlesearch --resource-group nestlechatbot-rg --definition azure-deployment/search-index-schema.json

# Create App Service Plan
az appservice plan create --name nestlechatbot-plan --resource-group nestlechatbot-rg --sku B1 --is-linux

# Create Web App
az webapp create --name nestlechatbot-api --resource-group nestlechatbot-rg --plan nestlechatbot-plan --runtime "PYTHON|3.10"

# Configure environment variables
az webapp config appsettings set --name nestlechatbot-api --resource-group nestlechatbot-rg --settings \
  AZURE_SEARCH_ENDPOINT="https://nestlesearch.search.windows.net" \
  AZURE_SEARCH_KEY="$SEARCH_ADMIN_KEY" \
  AZURE_SEARCH_INDEX="nestle-content-index" \
  WEBSITES_PORT=8000
```

### 2. Deploy Backend Code

```bash
# Configure local git deployment
az webapp deployment source config-local-git --name nestlechatbot-api --resource-group nestlechatbot-rg

# Get the git URL
GIT_URL=$(az webapp deployment source show --name nestlechatbot-api --resource-group nestlechatbot-rg --query repoUrl -o tsv)

# Add remote to your git repo
git remote add azure $GIT_URL

# Push your code
git push azure main
```

### 3. Deploy Frontend

For the frontend React application:

1. Build the production version:
   ```bash
   cd frontend
   npm install
   npm run build
   ```

2. Deploy to Azure Static Web Apps:
   - Use the Azure Portal or Azure Static Web Apps extension in VS Code
   - Select the `build` directory as the app location
   - Configure the API URL to point to your backend Web App

## Environment Variables

The following environment variables must be correctly set in your Azure Web App:

- `AZURE_SEARCH_ENDPOINT` - URL for your Cognitive Search service
- `AZURE_SEARCH_KEY` - API key for Cognitive Search
- `AZURE_SEARCH_INDEX` - Name of your search index
- `NEO4J_URI` - URI for Neo4j database (optional)
- `NEO4J_USER` - Neo4j username (optional)
- `NEO4J_PASSWORD` - Neo4j password (optional)

## Troubleshooting

- **Backend Deployment Issues**: Check the logs in the Azure portal
  ```bash
  az webapp log tail --name nestlechatbot-api --resource-group nestlechatbot-rg
  ```

- **Search Service Issues**: Verify search service is running and accessible
  ```bash
  az search service show --name nestlesearch --resource-group nestlechatbot-rg
  ```

- **Frontend Connectivity**: Ensure CORS is properly configured on the backend

## Monitoring and Scaling

- **Backend Scaling**: Adjust the App Service Plan as needed
  ```bash
  az appservice plan update --name nestlechatbot-plan --resource-group nestlechatbot-rg --sku S1
  ```

- **Search Service Scaling**: Adjust the Search Service tier if needed
  ```bash
  az search service update --name nestlesearch --resource-group nestlechatbot-rg --partition-count 2 --replica-count 2
  ```

- **Application Insights**: Add Application Insights for monitoring
  ```bash
  az monitor app-insights component create --app nestlechatbot-insights --location eastus --resource-group nestlechatbot-rg --application-type web
  ``` 