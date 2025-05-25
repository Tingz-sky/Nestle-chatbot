import os
import logging
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

# Configure logging to be less verbose
logging.getLogger('azure').setLevel(logging.WARNING)

class KeyVaultService:
    """Service to retrieve secrets from Azure Key Vault"""
    
    def __init__(self):
        """Initialize the Key Vault service"""
        self.keyvault_name = os.getenv("AZURE_KEYVAULT_NAME")
        self.keyvault_url = os.getenv("AZURE_KEYVAULT_URL")
        
        if not self.keyvault_url and self.keyvault_name:
            self.keyvault_url = f"https://{self.keyvault_name}.vault.azure.net/"
        
        self.logger = logging.getLogger("keyvault-service")
        
        # Initialize the client only if we have a URL
        self.secret_client = None
        if self.keyvault_url:
            try:
                credential = DefaultAzureCredential()
                self.secret_client = SecretClient(vault_url=self.keyvault_url, credential=credential)
            except Exception as e:
                self.logger.error(f"Failed to initialize Key Vault client: {e}")
    
    def get_secret(self, secret_name):
        """Retrieve a secret from Azure Key Vault"""
        if not self.secret_client:
            self.logger.error("Key Vault client not initialized")
            return None
            
        try:
            retrieved_secret = self.secret_client.get_secret(secret_name)
            return retrieved_secret.value
        except Exception as e:
            self.logger.error(f"Failed to retrieve secret '{secret_name}': {e}")
            return None

# Create a singleton instance
key_vault_service = KeyVaultService()

def get_secret(secret_name):
    """Helper function to get a secret from Key Vault"""
    return key_vault_service.get_secret(secret_name) 