import json
import os
import re
from typing import Dict, Any, List, Optional, Tuple

class ProductService:
    """Service for handling product information and purchase links"""
    
    def __init__(self):
        """Initialize product service and load product data"""
        self.products_data = self._load_products_data()
        # Create product name to product info mapping for fast lookup
        self.product_map = {
            product["name"].lower(): product 
            for product in self.products_data.get("products", [])
        }
        # Create a set of standard product names for fast matching
        self.standard_product_names = set(self.product_map.keys())
        # Create a dictionary mapping normalized names to standard names
        self.normalized_to_standard = self._create_normalized_mapping()
        
    def _load_products_data(self) -> Dict[str, Any]:
        """Load product data from file"""
        try:
            file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'mock_amazon_links.json')
            with open(file_path, 'r', encoding='utf-8') as file:
                return json.load(file)
        except Exception as e:
            print(f"Error loading product data: {e}")
            # Return empty data as fallback
            return {"products": []}
    
    def _create_normalized_mapping(self) -> Dict[str, str]:
        """Create a mapping from normalized product names to standard product names"""
        normalized_map = {}
        for standard_name in self.standard_product_names:
            # Create normalized version (lowercase, no spaces, no special chars)
            normalized = re.sub(r'[^a-z0-9]', '', standard_name.lower())
            normalized_map[normalized] = standard_name
                
        return normalized_map
    
    def normalize_product_name(self, product_query: str, openai_service=None) -> Optional[str]:
        """
        Normalize product name using LLM if available, otherwise use simple matching
        
        Args:
            product_query: Product name or query text
            openai_service: Optional OpenAI service for LLM-based normalization
            
        Returns:
            Normalized product name or None if not found
        """
        if not product_query:
            return None
            
        # Try LLM-based normalization if available
        if openai_service:
            try:
                prompt = f"""
                Identify the Nestle product mentioned in the following query:
                "{product_query}"
                
                Return ONLY the standard product name from this list, with no additional text:
                {', '.join(sorted(list(self.standard_product_names)))}
                
                If no product is mentioned or if you're unsure, return "None".
                """
                
                result = openai_service.get_completion(prompt)
                
                # Clean up the result
                result = result.strip().lower()
                if result == "none":
                    return None
                
                # Check if the result is a valid product name
                if result in self.standard_product_names:
                    return result
                    
                # If not, try to match with normalized names
                normalized_result = re.sub(r'[^a-z0-9]', '', result)
                if normalized_result in self.normalized_to_standard:
                    return self.normalized_to_standard[normalized_result]
            except Exception as e:
                print(f"Error in LLM normalization: {e}")
                # Fall back to simple normalization
        
        # Simple normalization as fallback
        query_normalized = re.sub(r'[^a-z0-9]', '', product_query.lower())
        
        # Direct match with normalized map
        if query_normalized in self.normalized_to_standard:
            return self.normalized_to_standard[query_normalized]
            
        # Check if any part of the query matches a product name
        for word in product_query.lower().split():
            word_normalized = re.sub(r'[^a-z0-9]', '', word)
            if word_normalized in self.normalized_to_standard:
                return self.normalized_to_standard[word_normalized]
                
        # Try partial matching
        for norm_name, std_name in self.normalized_to_standard.items():
            if norm_name in query_normalized or query_normalized in norm_name:
                return std_name
                
        return None
    
    def find_product(self, product_name: str, openai_service=None) -> Optional[Dict[str, Any]]:
        """
        Find product information
        
        Args:
            product_name: Product name
            openai_service: Optional OpenAI service for LLM-based normalization
            
        Returns:
            Product information or None (if not found)
        """
        if not product_name:
            return None
            
        # Try to normalize the product name
        normalized_name = self.normalize_product_name(product_name, openai_service)
        
        # If we got a normalized name, use it to look up the product
        if normalized_name and normalized_name in self.product_map:
            return self.product_map[normalized_name]
            
        # Fallback to direct lookup
        product_name_lower = product_name.lower()
        if product_name_lower in self.product_map:
            return self.product_map[product_name_lower]
            
        return None
        
    def get_purchase_link(self, product_name: str, openai_service=None) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
        """
        Get Amazon purchase link for a product
        
        Args:
            product_name: Product name
            openai_service: Optional OpenAI service for LLM-based normalization
            
        Returns:
            Tuple: (purchase link, full product info) or (None, None) if not found
        """
        product_info = self.find_product(product_name, openai_service)
        if not product_info:
            return None, None
            
        return product_info.get("amazon_link"), product_info
        
    def get_all_products(self) -> List[Dict[str, Any]]:
        """
        Get all product information
        
        Returns:
            List of product information
        """
        return self.products_data.get("products", []) 