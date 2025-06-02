import unittest
from services.structured_query_service import StructuredQueryService

class TestStructuredQueryService(unittest.TestCase):
    """Test cases for the StructuredQueryService"""
    
    def setUp(self):
        """Set up the test environment"""
        self.service = StructuredQueryService()
        
    def test_count_queries(self):
        """Test queries asking for counts of products"""
        # Test total product count queries
        self.assertIsNotNone(self.service.handle_query("How many Nestlé products are listed on the site?"))
        self.assertIsNotNone(self.service.handle_query("What is the total number of products?"))
        self.assertIsNotNone(self.service.handle_query("How many products does Nestlé offer?"))
        
        # Test category count queries
        self.assertIsNotNone(self.service.handle_query("How many coffee products are there?"))
        self.assertIsNotNone(self.service.handle_query("How many products are in the chocolate category?"))
        self.assertIsNotNone(self.service.handle_query("Number of water products?"))
        
        # Test brand count queries
        self.assertIsNotNone(self.service.handle_query("How many Nespresso products are there?"))
        
        # Test category count with variations
        self.assertIsNotNone(self.service.handle_query("How many coffees are available?"))
        self.assertIsNotNone(self.service.handle_query("How many ice cream products do you have?"))
        
    def test_list_queries(self):
        """Test queries asking for lists of products"""
        # Test category list queries
        self.assertIsNotNone(self.service.handle_query("What are the coffee products?"))
        self.assertIsNotNone(self.service.handle_query("List all chocolate products"))
        self.assertIsNotNone(self.service.handle_query("Show me the water products"))
        
        # Test brand list queries
        self.assertIsNotNone(self.service.handle_query("What are the Nestlé products?"))
        self.assertIsNotNone(self.service.handle_query("List all Nespresso products"))
        
        # Test all products query
        self.assertIsNotNone(self.service.handle_query("What are all the products?"))
        self.assertIsNotNone(self.service.handle_query("List all Nestlé products"))
        
        # Test categories query
        self.assertIsNotNone(self.service.handle_query("What are the product categories?"))
        
    def test_normalized_queries(self):
        """Test queries with normalized terms"""
        # Test with normalized category names
        self.assertIsNotNone(self.service.handle_query("How many icecream products do you have?"))
        self.assertIsNotNone(self.service.handle_query("List all icecream products"))
        
        # Test with normalized brand names
        self.assertIsNotNone(self.service.handle_query("How many HaagenDazs products are there?"))
        self.assertIsNotNone(self.service.handle_query("List all SanPellegrino products"))
        
    def test_non_structured_queries(self):
        """Test queries that are not structured queries"""
        self.assertIsNone(self.service.handle_query("Tell me about KitKat"))
        self.assertIsNone(self.service.handle_query("Where can I buy Nescafé?"))
        self.assertIsNone(self.service.handle_query("What is the price of Smarties?"))
        
    def test_response_content(self):
        """Test the content of responses"""
        # Test total product count response
        response = self.service.handle_query("How many Nestlé products are listed on the site?")
        self.assertIn("18", response)
        
        # Test category count response
        response = self.service.handle_query("How many coffee products are there?")
        self.assertIn("5", response)
        
        # Test category list response
        response = self.service.handle_query("What are the coffee products?")
        for product in ["Nescafé", "Nespresso"]:
            self.assertIn(product, response)
            
        # Test all products response
        response = self.service.handle_query("List all Nestlé products")
        for product in ["KitKat", "Nescafé", "Perrier"]:
            self.assertIn(product, response)
            
        # Test categories response
        response = self.service.handle_query("What are the product categories?")
        for category in ["coffee", "chocolate", "water"]:
            self.assertIn(category, response)

if __name__ == "__main__":
    unittest.main() 