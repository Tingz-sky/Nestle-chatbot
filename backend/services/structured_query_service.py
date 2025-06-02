import re
from typing import Dict, Any, Optional, List
import logging
from services.product_metadata import get_product_metadata

logger = logging.getLogger(__name__)

class StructuredQueryService:
    """Service for handling structured queries about products"""
    
    def __init__(self):
        """Initialize with product metadata"""
        self.product_metadata = get_product_metadata()
        # Create normalized versions of category and brand names for better matching
        self._create_normalized_mappings()
        
    def _initialize_product_metadata(self) -> Dict[str, Any]:
        """
        Initialize product metadata with categories and counts
        
        Returns:
            Dictionary containing product metadata
        """
        # This method is no longer used, but kept for reference
        return get_product_metadata()
    
    def _create_normalized_mappings(self):
        """Create normalized mappings for better matching of categories and brands"""
        # Create normalized category mapping
        self.normalized_categories = {}
        for category in self.product_metadata["categories"]:
            normalized = re.sub(r'[^a-z0-9]', '', category.lower())
            self.normalized_categories[normalized] = category
            
        # Create normalized brand mapping
        self.normalized_brands = {}
        for brand in self.product_metadata["brands"]:
            normalized = re.sub(r'[^a-z0-9]', '', brand.lower())
            self.normalized_brands[normalized] = brand
            
        # Add common variations
        self.normalized_categories['coffees'] = 'coffee'
        self.normalized_categories['chocolates'] = 'chocolate'
        self.normalized_categories['waters'] = 'water'
        self.normalized_categories['icecream'] = 'ice cream'
        self.normalized_categories['icecreams'] = 'ice cream'
        
        self.normalized_brands['nestlé'] = 'nestle'
        self.normalized_brands['nestleproducts'] = 'nestle'
        self.normalized_brands['nestléproducts'] = 'nestle'
        self.normalized_brands['haagendazs'] = 'haagen-dazs'
        self.normalized_brands['sanpellegrino'] = 'san pellegrino'
        
    def handle_query(self, query: str) -> Optional[str]:
        """
        Handle a structured query about products
        
        Args:
            query: The user's query text
            
        Returns:
            Response string if query can be handled, None otherwise
        """
        # Convert query to lowercase for easier matching
        query_lower = query.lower()
        
        try:
            # Check if this is a count query
            if self._is_count_query(query_lower):
                return self._handle_count_query(query_lower)
                
            # Check if this is a list query
            if self._is_list_query(query_lower):
                return self._handle_list_query(query_lower)
                
            # Not a structured query we can handle
            return None
        except Exception as e:
            logger.error(f"Error handling structured query: {e}")
            return None
        
    def _is_count_query(self, query: str) -> bool:
        """Check if the query is asking for a count"""
        count_patterns = [
            r"how many",
            r"number of",
            r"total number",
            r"count of",
            r"amount of",
            r"how much",
            r"quantity of"
        ]
        
        # Check if query contains product/category related terms
        product_terms = [
            r"product",
            r"item",
            r"brand",
            r"category"
        ]
        
        has_count_pattern = any(re.search(pattern, query) for pattern in count_patterns)
        has_product_term = any(re.search(pattern, query) for pattern in product_terms)
        
        # Special case for "how many X are there" pattern
        if re.search(r"how many .+ (are|is) (there|listed|available|offered)", query):
            return True
            
        return has_count_pattern and has_product_term
        
    def _is_list_query(self, query: str) -> bool:
        """Check if the query is asking for a list of products"""
        list_patterns = [
            r"list (all|the)",
            r"what (are|is) (all|the)",
            r"show (all|the|me)",
            r"tell me (all|the)",
            r"what .* (products|brands)",
            r"which .* (products|brands)"
        ]
        
        return any(re.search(pattern, query) for pattern in list_patterns)
        
    def _extract_category_from_query(self, query: str) -> Optional[str]:
        """Extract category from query using normalized mapping"""
        # First try direct matching
        for category in self.product_metadata["categories"]:
            if category in query:
                return category
                
        # Try normalized matching
        query_normalized = re.sub(r'[^a-z0-9]', '', query)
        for norm_cat, category in self.normalized_categories.items():
            if norm_cat in query_normalized:
                return category
                
        return None
        
    def _extract_brand_from_query(self, query: str) -> Optional[str]:
        """Extract brand from query using normalized mapping"""
        # First try direct matching
        for brand in self.product_metadata["brands"]:
            if brand in query:
                return brand
                
        # Try normalized matching
        query_normalized = re.sub(r'[^a-z0-9]', '', query)
        for norm_brand, brand in self.normalized_brands.items():
            if norm_brand in query_normalized:
                return brand
                
        return None
        
    def _handle_count_query(self, query: str) -> str:
        """Handle queries asking for product counts"""
        # Check if asking about total products
        total_product_patterns = [
            r"(all|total).*(products|items)",
            r"nestl[eé].*(products|items)",
            r"(products|items).*(site|listed|available|offered|total)"
        ]
        
        is_total_query = any(re.search(pattern, query) for pattern in total_product_patterns)
        
        if is_total_query:
            if "site" in query or "listed" in query:
                return f"There are {self.product_metadata['total_count']} Nestlé products listed on our site."
            return f"Nestlé offers {self.product_metadata['total_count']} products in our database."
            
        # Check if asking about specific category
        category = self._extract_category_from_query(query)
        if category:
            count = self.product_metadata["categories"][category]["count"]
            return f"There are {count} products in the {category} category."
                
        # Check if asking about specific brand
        brand = self._extract_brand_from_query(query)
        if brand:
            count = len(self.product_metadata["brands"][brand])
            return f"There are {count} products under the {brand.title()} brand."
                
        # Check if asking about categories
        if "categories" in query:
            return f"There are {len(self.product_metadata['categories'])} product categories: {', '.join(self.product_metadata['categories'].keys())}."
            
        # Generic response for unspecified count queries
        return f"We have a total of {self.product_metadata['total_count']} Nestlé products across {len(self.product_metadata['categories'])} categories."
        
    def _handle_list_query(self, query: str) -> str:
        """Handle queries asking for lists of products"""
        # Check if asking about specific category
        category = self._extract_category_from_query(query)
        if category:
            products = self.product_metadata["categories"][category]["products"]
            products_text = ", ".join(products)
            return f"The products in the {category} category are: {products_text}."
                
        # Check if asking about specific brand
        brand = self._extract_brand_from_query(query)
        if brand:
            products = self.product_metadata["brands"][brand]
            products_text = ", ".join(products)
            return f"The {brand.title()} products are: {products_text}."
                
        # If asking for all products
        if re.search(r"all products|all nestl[eé] products", query):
            all_products = []
            for category in self.product_metadata["categories"]:
                all_products.extend(self.product_metadata["categories"][category]["products"])
            products_text = ", ".join(sorted(set(all_products)))
            return f"Here are all the Nestlé products: {products_text}."
            
        # If asking for categories
        if "categories" in query:
            categories = list(self.product_metadata["categories"].keys())
            categories_text = ", ".join(categories)
            return f"The product categories are: {categories_text}."
            
        return None 