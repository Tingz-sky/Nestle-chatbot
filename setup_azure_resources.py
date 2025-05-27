#!/usr/bin/env python3
"""
Nestle AI Chatbot - Azure Resources Setup Script
This script sets up all required Azure resources for the Nestle AI Chatbot project.
"""

import os
import sys
import argparse
import subprocess
import json
import time
import random
import string
from datetime import datetime

# Configuration
DEFAULT_LOCATION = "eastus"
RESOURCE_GROUP_NAME = "nestlechatbot-rg"
OPENAI_NAME = "nestleopenai"
SEARCH_NAME = "nestlechatbot-search"
KEYVAULT_NAME = "nestlechatbot-kv"
APP_SERVICE_PLAN = "nestlechatbot-plan"
WEBAPP_NAME = "nestlechatbot-api"
STATIC_WEB_APP_NAME = "nestlechatbot-frontend"
SEARCH_INDEX_NAME = "nestle-content-index"

# Colors for output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_step(message):
    """Print a step message with formatting"""
    print(f"\n{Colors.BLUE}{Colors.BOLD}=== {message} ==={Colors.ENDC}\n")

def print_success(message):
    """Print a success message with formatting"""
    print(f"{Colors.GREEN}✓ {message}{Colors.ENDC}")

def print_error(message):
    """Print an error message with formatting"""
    print(f"{Colors.RED}✗ {message}{Colors.ENDC}")

def print_warning(message):
    """Print a warning message with formatting"""
    print(f"{Colors.YELLOW}! {message}{Colors.ENDC}")

def run_command(command, check=True, capture_output=False):
    """Run a shell command and handle errors"""
    try:
        if capture_output:
            result = subprocess.run(command, shell=True, check=check, capture_output=True, text=True)
            return result
        else:
            subprocess.run(command, shell=True, check=check)
            return None
    except subprocess.CalledProcessError as e:
        print_error(f"Command failed: {e}")
        if not check:
            return None
        sys.exit(1)

def check_az_cli():
    """Check if Azure CLI is installed and user is logged in"""
    print_step("Checking Azure CLI")
    
    # Check if Azure CLI is installed
    try:
        subprocess.run(["az", "--version"], capture_output=True, check=True)
        print_success("Azure CLI is installed")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print_error("Azure CLI is not installed. Please install it: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli")
        sys.exit(1)
    
    # Check if user is logged in
    result = subprocess.run("az account show", shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print_warning("You are not logged in to Azure CLI")
        print("Please run 'az login' manually and then run this script again")
        sys.exit(1)
    else:
        account_info = json.loads(result.stdout)
        print_success(f"Logged in as: {account_info.get('user', {}).get('name')} (Subscription: {account_info.get('name')})")

def create_resource_group(location):
    """Create a resource group"""
    print_step(f"Creating resource group: {RESOURCE_GROUP_NAME}")
    
    # Check if resource group exists
    result = run_command(f"az group show --name {RESOURCE_GROUP_NAME}", check=False, capture_output=True)
    if result.returncode == 0:
        print_success(f"Resource group {RESOURCE_GROUP_NAME} already exists")
        return
    
    # Create resource group
    run_command(f"az group create --name {RESOURCE_GROUP_NAME} --location {location}")
    print_success(f"Resource group {RESOURCE_GROUP_NAME} created successfully")

def create_openai_service(location):
    """Create Azure OpenAI service"""
    print_step(f"Creating Azure OpenAI service: {OPENAI_NAME}")
    
    # Check if OpenAI service exists
    result = run_command(f"az cognitiveservices account show --name {OPENAI_NAME} --resource-group {RESOURCE_GROUP_NAME}", check=False, capture_output=True)
    if result.returncode == 0:
        print_success(f"OpenAI service {OPENAI_NAME} already exists")
    else:
        # Create OpenAI service
        run_command(f"az cognitiveservices account create --name {OPENAI_NAME} "
                    f"--resource-group {RESOURCE_GROUP_NAME} "
                    f"--location {location} "
                    f"--kind OpenAI "
                    f"--sku Standard "
                    f"--custom-domain {OPENAI_NAME}")
        print_success(f"OpenAI service {OPENAI_NAME} created successfully")
    
    # Create deployments
    print_step("Creating OpenAI deployments")
    
    # Create GPT-3.5 Turbo deployment
    deployment_name = "nestle-gpt35"
    deployment_check = run_command(f"az cognitiveservices account deployment show "
                                 f"--name {OPENAI_NAME} "
                                 f"--resource-group {RESOURCE_GROUP_NAME} "
                                 f"--deployment-name {deployment_name}", check=False, capture_output=True)
    
    if deployment_check.returncode == 0:
        print_success(f"Deployment {deployment_name} already exists")
    else:
        run_command(f"az cognitiveservices account deployment create "
                    f"--name {OPENAI_NAME} "
                    f"--resource-group {RESOURCE_GROUP_NAME} "
                    f"--deployment-name {deployment_name} "
                    f"--model-name gpt-35-turbo "
                    f"--model-version 0125 "
                    f"--model-format OpenAI "
                    f"--sku-capacity 100 "
                    f"--sku-name Standard")
        print_success(f"Deployment {deployment_name} created successfully")
    
    # Get the API key
    result = run_command(f"az cognitiveservices account keys list "
                       f"--name {OPENAI_NAME} "
                       f"--resource-group {RESOURCE_GROUP_NAME}", capture_output=True)
    keys = json.loads(result.stdout)
    openai_key = keys["key1"]
    
    return {
        "endpoint": f"https://{OPENAI_NAME}.openai.azure.com/",
        "key": openai_key,
        "deployment": deployment_name
    }

def create_search_service(location):
    """Create Azure Cognitive Search service"""
    print_step(f"Creating Azure Cognitive Search service: {SEARCH_NAME}")
    
    # Check if Search service exists
    result = run_command(f"az search service show --name {SEARCH_NAME} --resource-group {RESOURCE_GROUP_NAME}", check=False, capture_output=True)
    if result.returncode == 0:
        print_success(f"Search service {SEARCH_NAME} already exists")
    else:
        # Create Search service
        # Note: Search services might not be available in all regions, so we use a specific region where it's known to be available
        search_location = "centralus"  # Search services are commonly available in this region
        run_command(f"az search service create "
                  f"--name {SEARCH_NAME} "
                  f"--resource-group {RESOURCE_GROUP_NAME} "
                  f"--sku Standard "
                  f"--partition-count 1 "
                  f"--replica-count 1 "
                  f"--location {search_location}")
        print_success(f"Search service {SEARCH_NAME} created successfully")
    
    # Get the API key
    result = run_command(f"az search admin-key show "
                       f"--service-name {SEARCH_NAME} "
                       f"--resource-group {RESOURCE_GROUP_NAME}", capture_output=True)
    keys = json.loads(result.stdout)
    search_key = keys["primaryKey"]
    
    # Create search index schema
    with open("azure-deployment/search-index-schema.json", "w") as f:
        f.write("""
{
  "name": "nestle-content-index",
  "fields": [
    {
      "name": "id",
      "type": "Edm.String",
      "key": true,
      "searchable": false
    },
    {
      "name": "title",
      "type": "Edm.String",
      "searchable": true,
      "retrievable": true,
      "sortable": true,
      "filterable": true,
      "facetable": false
    },
    {
      "name": "content",
      "type": "Edm.String",
      "searchable": true,
      "retrievable": true,
      "sortable": false,
      "filterable": false,
      "facetable": false
    },
    {
      "name": "url",
      "type": "Edm.String",
      "searchable": false,
      "retrievable": true,
      "sortable": false,
      "filterable": true,
      "facetable": false
    },
    {
      "name": "vectorContent",
      "type": "Collection(Edm.Single)",
      "searchable": true,
      "retrievable": true,
      "dimensions": 1536,
      "vectorSearchConfiguration": "vectorConfig"
    }
  ],
  "vectorSearch": {
    "algorithmConfigurations": [
      {
        "name": "vectorConfig",
        "kind": "hnsw"
      }
    ]
  },
  "semantic": {
    "configurations": [
      {
        "name": "semanticConfig",
        "prioritizedFields": {
          "titleField": {
            "fieldName": "title"
          },
          "contentFields": [
            {
              "fieldName": "content"
            }
          ]
        }
      }
    ]
  }
}
""")
    
    # Create the search index (if it doesn't exist, the API will create it)
    try:
        run_command(f"az search index create "
                  f"--name {SEARCH_INDEX_NAME} "
                  f"--service-name {SEARCH_NAME} "
                  f"--resource-group {RESOURCE_GROUP_NAME} "
                  f"--definition @azure-deployment/search-index-schema.json")
        print_success(f"Search index {SEARCH_INDEX_NAME} created successfully")
    except:
        print_warning(f"Could not create search index. You may need to create it manually.")
    
    return {
        "endpoint": f"https://{SEARCH_NAME}.search.windows.net",
        "key": search_key,
        "index": SEARCH_INDEX_NAME
    }

def create_key_vault(location):
    """Create Azure Key Vault"""
    print_step(f"Creating Azure Key Vault: {KEYVAULT_NAME}")
    
    # Check if Key Vault exists
    result = run_command(f"az keyvault show --name {KEYVAULT_NAME}", check=False, capture_output=True)
    if result.returncode == 0:
        print_success(f"Key Vault {KEYVAULT_NAME} already exists")
    else:
        # Create Key Vault
        run_command(f"az keyvault create "
                  f"--name {KEYVAULT_NAME} "
                  f"--resource-group {RESOURCE_GROUP_NAME} "
                  f"--location {location} "
                  f"--enable-rbac-authorization true")
        print_success(f"Key Vault {KEYVAULT_NAME} created successfully")

        # Set access policy for the current user
        result = run_command("az account show", capture_output=True)
        account_info = json.loads(result.stdout)
        user_object_id = account_info.get("user", {}).get("name")
        
        if user_object_id:
            try:
                # Assign the Key Vault Administrator role to the current user
                run_command(f"az role assignment create "
                          f"--assignee \"{user_object_id}\" "
                          f"--role \"Key Vault Administrator\" "
                          f"--scope \"/subscriptions/{account_info['id']}/resourceGroups/{RESOURCE_GROUP_NAME}/providers/Microsoft.KeyVault/vaults/{KEYVAULT_NAME}\"")
                print_success(f"Assigned Key Vault Administrator role to {user_object_id}")
            except:
                print_warning("Could not assign Key Vault Administrator role. You may need to assign it manually.")
    
    return {
        "name": KEYVAULT_NAME,
        "url": f"https://{KEYVAULT_NAME}.vault.azure.net/"
    }

def create_app_service(location):
    """Create App Service Plan and Web App"""
    print_step(f"Creating App Service Plan: {APP_SERVICE_PLAN}")
    
    # Check if App Service Plan exists
    result = run_command(f"az appservice plan show --name {APP_SERVICE_PLAN} --resource-group {RESOURCE_GROUP_NAME}", check=False, capture_output=True)
    if result.returncode == 0:
        print_success(f"App Service Plan {APP_SERVICE_PLAN} already exists")
    else:
        # Create App Service Plan
        run_command(f"az appservice plan create "
                  f"--name {APP_SERVICE_PLAN} "
                  f"--resource-group {RESOURCE_GROUP_NAME} "
                  f"--sku B1 "
                  f"--is-linux")
        print_success(f"App Service Plan {APP_SERVICE_PLAN} created successfully")
    
    print_step(f"Creating Web App: {WEBAPP_NAME}")
    
    # Check if Web App exists
    result = run_command(f"az webapp show --name {WEBAPP_NAME} --resource-group {RESOURCE_GROUP_NAME}", check=False, capture_output=True)
    if result.returncode == 0:
        print_success(f"Web App {WEBAPP_NAME} already exists")
    else:
        # Create Web App
        run_command(f"az webapp create "
                  f"--name {WEBAPP_NAME} "
                  f"--resource-group {RESOURCE_GROUP_NAME} "
                  f"--plan {APP_SERVICE_PLAN} "
                  f"--runtime \"PYTHON|3.10\"")
        print_success(f"Web App {WEBAPP_NAME} created successfully")
    
    # Get the web app URL
    result = run_command(f"az webapp show --name {WEBAPP_NAME} --resource-group {RESOURCE_GROUP_NAME} --query defaultHostName", capture_output=True)
    hostname = json.loads(result.stdout)
    
    return {
        "name": WEBAPP_NAME,
        "url": f"https://{hostname}"
    }

def create_static_web_app(location):
    """Create Static Web App for frontend"""
    print_step(f"Creating Static Web App: {STATIC_WEB_APP_NAME}")
    
    # Check if Static Web App exists
    result = run_command(f"az staticwebapp show --name {STATIC_WEB_APP_NAME} --resource-group {RESOURCE_GROUP_NAME}", check=False, capture_output=True)
    if result.returncode == 0:
        print_success(f"Static Web App {STATIC_WEB_APP_NAME} already exists")
    else:
        # Create Static Web App
        # Note: This creates a basic Static Web App without GitHub integration
        run_command(f"az staticwebapp create "
                  f"--name {STATIC_WEB_APP_NAME} "
                  f"--resource-group {RESOURCE_GROUP_NAME} "
                  f"--location {location} "
                  f"--sku Free")
        print_success(f"Static Web App {STATIC_WEB_APP_NAME} created successfully")
    
    # Get the Static Web App URL and deployment token
    result = run_command(f"az staticwebapp show --name {STATIC_WEB_APP_NAME} --resource-group {RESOURCE_GROUP_NAME}", capture_output=True)
    static_app_info = json.loads(result.stdout)
    
    # Get deployment token
    token_result = run_command(f"az staticwebapp secrets list --name {STATIC_WEB_APP_NAME} --resource-group {RESOURCE_GROUP_NAME}", capture_output=True)
    token_info = json.loads(token_result.stdout)
    
    return {
        "name": STATIC_WEB_APP_NAME,
        "url": static_app_info.get("defaultHostname", ""),
        "token": token_info.get("properties", {}).get("apiKey", "")
    }

def store_secrets_in_key_vault(secrets):
    """Store secrets in Key Vault"""
    print_step("Storing secrets in Key Vault")
    
    # Store OpenAI key
    run_command(f"az keyvault secret set --vault-name {KEYVAULT_NAME} --name \"AZURE-OPENAI-KEY\" --value \"{secrets['openai']['key']}\"")
    print_success("Stored OpenAI key in Key Vault")
    
    # Store Search key
    run_command(f"az keyvault secret set --vault-name {KEYVAULT_NAME} --name \"AZURE-SEARCH-KEY\" --value \"{secrets['search']['key']}\"")
    print_success("Stored Search key in Key Vault")
    
    # Add a placeholder password for Neo4j
    neo4j_password = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
    run_command(f"az keyvault secret set --vault-name {KEYVAULT_NAME} --name \"NEO4J-PASSWORD\" --value \"{neo4j_password}\"")
    print_success("Stored Neo4j password placeholder in Key Vault")
    
    # Add a placeholder password for Neo4j Aura
    run_command(f"az keyvault secret set --vault-name {KEYVAULT_NAME} --name \"NEO4J-AURA-PASSWORD\" --value \"{neo4j_password}\"")
    print_success("Stored Neo4j Aura password placeholder in Key Vault")

def configure_web_app(secrets):
    """Configure Web App settings"""
    print_step("Configuring Web App settings")
    
    # Set environment variables
    run_command(f"az webapp config appsettings set "
              f"--name {WEBAPP_NAME} "
              f"--resource-group {RESOURCE_GROUP_NAME} "
              f"--settings "
              f"AZURE_SEARCH_ENDPOINT=\"{secrets['search']['endpoint']}\" "
              f"AZURE_SEARCH_KEY=\"{secrets['search']['key']}\" "
              f"AZURE_SEARCH_INDEX=\"{secrets['search']['index']}\" "
              f"AZURE_OPENAI_ENDPOINT=\"{secrets['openai']['endpoint']}\" "
              f"AZURE_OPENAI_KEY=\"{secrets['openai']['key']}\" "
              f"AZURE_OPENAI_DEPLOYMENT=\"{secrets['openai']['deployment']}\" "
              f"AZURE_KEYVAULT_NAME=\"{secrets['keyvault']['name']}\" "
              f"AZURE_KEYVAULT_URL=\"{secrets['keyvault']['url']}\" "
              f"WEBSITES_PORT=\"8000\"")
    
    print_success("Web App settings configured successfully")

def generate_setup_env_file(secrets):
    """Generate setup_env.sh file"""
    print_step("Generating setup_env.sh file")
    
    content = f"""#!/bin/bash

# Environment setup for Nestle Chatbot

# Azure Search configuration
export AZURE_SEARCH_ENDPOINT="{secrets['search']['endpoint']}"
export AZURE_SEARCH_INDEX="{secrets['search']['index']}"

# Azure OpenAI configuration
export AZURE_OPENAI_ENDPOINT="{secrets['openai']['endpoint']}"
export AZURE_OPENAI_DEPLOYMENT="{secrets['openai']['deployment']}"

# Azure Key Vault configuration
export AZURE_KEYVAULT_NAME="{secrets['keyvault']['name']}"
export AZURE_KEYVAULT_URL="{secrets['keyvault']['url']}"

# Neo4j configuration - Local development
export NEO4J_URI="neo4j://localhost:7687"
export NEO4J_USER="neo4j"

# Neo4j configuration - Aura cloud connection (commented out)
# export NEO4J_URI="neo4j+s://YOUR_AURA_ID.databases.neo4j.io"
# export NEO4J_USER="neo4j"
# Password retrieved from Key Vault: NEO4J-AURA-PASSWORD
# export NEO4J_AURA_PASSWORD="your-password-here"

# For local development when Key Vault is not available
# export AZURE_SEARCH_KEY="{secrets['search']['key']}"
# export AZURE_OPENAI_KEY="{secrets['openai']['key']}"
"""
    
    # Write to file
    with open("setup_env.sh", "w") as f:
        f.write(content)
    
    # Make it executable
    os.chmod("setup_env.sh", 0o755)
    
    print_success("Generated setup_env.sh file successfully")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Set up Azure resources for Nestle AI Chatbot")
    parser.add_argument("--location", default=DEFAULT_LOCATION, help=f"Azure region location (default: {DEFAULT_LOCATION})")
    args = parser.parse_args()
    
    # Create azure-deployment directory if it doesn't exist
    os.makedirs("azure-deployment", exist_ok=True)
    
    # Check if Azure CLI is installed and user is logged in
    check_az_cli()
    
    # Create resource group
    create_resource_group(args.location)
    
    # Create Azure resources
    openai_info = create_openai_service(args.location)
    search_info = create_search_service(args.location)
    keyvault_info = create_key_vault(args.location)
    webapp_info = create_app_service(args.location)
    staticwebapp_info = create_static_web_app(args.location)
    
    # Collect all secrets
    secrets = {
        "openai": openai_info,
        "search": search_info,
        "keyvault": keyvault_info,
        "webapp": webapp_info,
        "staticwebapp": staticwebapp_info
    }
    
    # Store secrets in Key Vault
    store_secrets_in_key_vault(secrets)
    
    # Configure Web App
    configure_web_app(secrets)
    
    # Generate setup_env.sh file
    generate_setup_env_file(secrets)
    
    print_step("Setup Complete")
    print(f"""
{Colors.GREEN}{Colors.BOLD}All Azure resources have been created successfully!{Colors.ENDC}

{Colors.BLUE}Resource Group:{Colors.ENDC} {RESOURCE_GROUP_NAME}
{Colors.BLUE}OpenAI Service:{Colors.ENDC} {OPENAI_NAME}
{Colors.BLUE}Search Service:{Colors.ENDC} {SEARCH_NAME}
{Colors.BLUE}Key Vault:{Colors.ENDC} {KEYVAULT_NAME}
{Colors.BLUE}Web App:{Colors.ENDC} {webapp_info['url']}
{Colors.BLUE}Static Web App:{Colors.ENDC} https://{staticwebapp_info['url']}

{Colors.YELLOW}Next steps:{Colors.ENDC}
1. Review the generated setup_env.sh file
2. Source the environment variables: source setup_env.sh
3. Set up your Neo4j database (local or Aura)
4. Deploy your code to the Web App:
   - cd backend
   - az webapp up --name {WEBAPP_NAME} --resource-group {RESOURCE_GROUP_NAME} --runtime "PYTHON:3.10"
5. Deploy your frontend to the Static Web App using the deployment token or GitHub integration
""")

if __name__ == "__main__":
    main() 