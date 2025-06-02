#!/usr/bin/env python3
"""
Script to update product metadata from existing product data sources.
This script reads product data from mock_amazon_links.json and mock_stores.json,
and generates structured metadata for use in the StructuredQueryService.
"""

import json
import os
import sys
from collections import defaultdict
from typing import Dict, List, Any

# Add the parent directory to the path so we can import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def load_json_file(file_path: str) -> Dict[str, Any]:
    """Load a JSON file and return its contents"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return {}

def categorize_products(products: List[str]) -> Dict[str, List[str]]:
    """
    Categorize products based on predefined categories
    
    Args:
        products: List of product names
        
    Returns:
        Dictionary mapping categories to lists of products
    """
    categories = {
        "coffee": ["Nescafé", "Nescafé Gold", "Nescafé Dolce Gusto", "Starbucks by Nescafé", "Nespresso"],
        "chocolate": ["KitKat", "Aero", "Smarties", "After Eight", "Crunch", "Coffee Crisp", "Turtles"],
        "water": ["Nestlé Pure Life", "Perrier", "San Pellegrino"],
        "dairy": ["Carnation", "Coffee-mate"],
        "ice cream": ["Häagen-Dazs"]
    }
    
    # Create a mapping from product to category
    product_to_category = {}
    for category, product_list in categories.items():
        for product in product_list:
            product_to_category[product] = category
    
    # Categorize the input products
    categorized = defaultdict(list)
    for product in products:
        category = product_to_category.get(product, "other")
        categorized[category].append(product)
    
    return dict(categorized)

def identify_brands(products: List[str]) -> Dict[str, List[str]]:
    """
    Identify brands from product names
    
    Args:
        products: List of product names
        
    Returns:
        Dictionary mapping brands to lists of products
    """
    brands = {
        "nestle": ["Nescafé", "Nestlé Pure Life", "KitKat", "Aero", "Smarties", "Coffee Crisp", "Crunch", "After Eight"],
        "nespresso": ["Nespresso"],
        "perrier": ["Perrier"],
        "san pellegrino": ["San Pellegrino"],
        "haagen-dazs": ["Häagen-Dazs"]
    }
    
    # Validate and filter brands
    validated_brands = {}
    for brand, brand_products in brands.items():
        # Only include brands where at least one product exists in our product list
        filtered_products = [p for p in brand_products if p in products]
        if filtered_products:
            validated_brands[brand] = filtered_products
    
    return validated_brands

def generate_metadata(amazon_links_path: str, stores_path: str) -> Dict[str, Any]:
    """
    Generate product metadata from Amazon links and store data
    
    Args:
        amazon_links_path: Path to the mock_amazon_links.json file
        stores_path: Path to the mock_stores.json file
        
    Returns:
        Dictionary containing product metadata
    """
    # Load data from files
    amazon_links = load_json_file(amazon_links_path)
    stores = load_json_file(stores_path)
    
    # Extract unique product names
    amazon_products = [item["name"] for item in amazon_links]
    store_products = []
    for store in stores:
        store_products.extend([product["name"] for product in store.get("products", [])])
    
    # Combine and deduplicate product names
    all_products = list(set(amazon_products + store_products))
    
    # Categorize products
    categories = categorize_products(all_products)
    
    # Identify brands
    brands = identify_brands(all_products)
    
    # Generate metadata
    metadata = {
        "total_count": len(all_products),
        "categories": {},
        "brands": brands
    }
    
    # Add category data with counts
    for category, products in categories.items():
        metadata["categories"][category] = {
            "count": len(products),
            "products": products
        }
    
    return metadata

def save_metadata(metadata: Dict[str, Any], output_path: str) -> None:
    """
    Save metadata to a Python file
    
    Args:
        metadata: The metadata dictionary
        output_path: Path to save the Python file
    """
    with open(output_path, 'w', encoding='utf-8') as file:
        file.write("# This file is auto-generated. Do not edit directly.\n\n")
        file.write("def get_product_metadata():\n")
        file.write("    \"\"\"Return the product metadata\"\"\"\n")
        file.write("    return ")
        file.write(json.dumps(metadata, indent=4).replace("null", "None"))
        file.write("\n")

def main():
    """Main function"""
    # Define file paths
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    amazon_links_path = os.path.join(base_dir, "data", "mock_amazon_links.json")
    stores_path = os.path.join(base_dir, "data", "mock_stores.json")
    output_path = os.path.join(base_dir, "services", "product_metadata.py")
    
    # Generate metadata
    metadata = generate_metadata(amazon_links_path, stores_path)
    
    # Save metadata
    save_metadata(metadata, output_path)
    
    print(f"Generated product metadata with {metadata['total_count']} products")
    print(f"Metadata saved to {output_path}")

if __name__ == "__main__":
    main() 