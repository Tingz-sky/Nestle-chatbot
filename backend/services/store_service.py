import json
import math
import os
import re
from typing import List, Dict, Any, Optional

# Maximum search distance in kilometers
MAX_SEARCH_DISTANCE = 20

class StoreService:
    """Service for handling store queries and geolocation features"""
    
    def __init__(self):
        """Initialize store service, load store data"""
        self.stores_data = self._load_stores_data()
        # Create a standardized product map for easier matching
        self.store_products_map = self._create_store_products_map()
        
    def _load_stores_data(self) -> Dict[str, Any]:
        """Load store data from file"""
        try:
            file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'mock_stores.json')
            with open(file_path, 'r', encoding='utf-8') as file:
                return json.load(file)
        except Exception as e:
            print(f"Error loading stores data: {e}")
            # Return empty data as fallback
            return {"stores": []}
            
    def _create_store_products_map(self) -> Dict[int, List[str]]:
        """Create a map of store IDs to standardized product names"""
        store_map = {}
        for store in self.stores_data.get("stores", []):
            store_id = store.get("id")
            if store_id:
                # Create a standardized list of product names
                standardized_products = set()
                for product in store.get("products", []):
                    # Add the original product name
                    standardized_products.add(product)
                    
                    # Convert to lowercase for case-insensitive matching
                    product_lower = product.lower()
                    standardized_products.add(product_lower)
                    
                    # Add product without spaces and special characters
                    normalized = re.sub(r'[^a-z0-9]', '', product_lower)
                    standardized_products.add(normalized)
                    
                    # Add common variations
                    if product == "KitKat":
                        standardized_products.add("kit kat")
                        standardized_products.add("kitkat")
                    elif product == "Nescafé":
                        standardized_products.add("nescafe")
                    elif product == "Nestlé Pure Life":
                        standardized_products.add("pure life")
                        standardized_products.add("nestlepurelife")
                    elif product == "MAGGI":
                        standardized_products.add("maggi")
                    elif product == "After Eight":
                        standardized_products.add("after 8")
                        standardized_products.add("aftereight")
                    elif product == "Häagen-Dazs":
                        standardized_products.add("haagen dazs")
                        standardized_products.add("haagen-dazs")
                        standardized_products.add("haagendazs")
                    
                store_map[store_id] = list(standardized_products)
        return store_map
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate distance between two points using Haversine formula (in kilometers)
        """
        # Earth radius in kilometers
        R = 6371.0
        
        # Convert latitude and longitude to radians
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        # Differences in coordinates
        dlon = lon2_rad - lon1_rad
        dlat = lat2_rad - lat1_rad
        
        # Haversine formula
        a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distance = R * c
        
        return distance
    
    def _product_match(self, product_name: str, store_products: List[str]) -> bool:
        """
        Check if a store carries a product using simplified matching
        
        Args:
            product_name: Product to search for
            store_products: List of products carried by the store
            
        Returns:
            True if the store carries the product, False otherwise
        """
        if not product_name:
            return True  # No product specified, match all stores
            
        # Convert to lowercase for case-insensitive matching
        product_name_lower = product_name.lower()
        
        # Handle common product name variations
        product_mappings = {
            "pure life": "nestlé pure life",
            "nestle pure life": "nestlé pure life",
            "nestle": "nestlé",
            "nescafe": "nescafé",
            "haagen-dazs": "häagen-dazs",
            "haagendazs": "häagen-dazs",
            "haagen dazs": "häagen-dazs",
            "kit kat": "kitkat",
            "after 8": "after eight",
            "after-eight": "after eight"
        }
        
        # Check if we need to standardize the product name
        for old_name, new_name in product_mappings.items():
            if old_name in product_name_lower:
                product_name_lower = new_name
                break
        
        # Convert store products to lowercase for comparison
        store_products_lower = [p.lower() for p in store_products]
        
        # Check for exact match first
        if product_name_lower in store_products_lower:
            return True
            
        # Try normalized matching (remove spaces and special characters)
        product_normalized = re.sub(r'[^a-z0-9]', '', product_name_lower)
        
        # Normalize store products for comparison
        store_products_normalized = [re.sub(r'[^a-z0-9]', '', p.lower()) for p in store_products]
        
        if product_normalized in store_products_normalized:
            return True
            
        # Try partial matching
        for store_product in store_products_normalized:
            # Check if one contains the other
            if product_normalized in store_product or store_product in product_normalized:
                return True
                
        return False
    
    def find_nearby_stores(self, latitude: float, longitude: float, product: Optional[str] = None, max_distance: float = MAX_SEARCH_DISTANCE, limit: int = 3) -> List[Dict[str, Any]]:
        """
        Find stores near a specified location
        
        Args:
            latitude: User location latitude
            longitude: User location longitude
            product: Optional, filter to only return stores with a specific product
            max_distance: Maximum search distance (kilometers)
            limit: Maximum number of results to return
            
        Returns:
            List of nearby stores with distance information
        """
        nearby_stores = []
        
        for store in self.stores_data.get("stores", []):
            # Calculate distance
            distance = self._calculate_distance(
                latitude, longitude, 
                store["latitude"], store["longitude"]
            )
            
            # Check if within maximum distance
            if distance <= max_distance:
                # If product specified, check if store has it
                if product and not self._product_match(product, store.get("products", [])):
                    continue
                    
                # Create a copy of store info, add distance
                store_info = store.copy()
                store_info["distance"] = round(distance, 2)
                nearby_stores.append(store_info)
        
        # Sort by distance
        nearby_stores.sort(key=lambda x: x["distance"])
        
        # Limit number of results
        return nearby_stores[:limit]
    
    def get_product_stores(self, product_name: str, latitude: Optional[float] = None, longitude: Optional[float] = None) -> List[Dict[str, Any]]:
        """
        Get stores that sell a specific product
        
        Args:
            product_name: Product name
            latitude: Optional, user location latitude
            longitude: Optional, user location longitude
            
        Returns:
            List of stores selling the product, sorted by distance if location provided
        """
        if latitude is not None and longitude is not None:
            # If location provided, use nearby stores query
            return self.find_nearby_stores(latitude, longitude, product_name)
        else:
            # Otherwise return all stores with the product (no distance info)
            return [
                store for store in self.stores_data.get("stores", [])
                if self._product_match(product_name, store.get("products", []))
            ] 