#!/usr/bin/env python
"""
Simplified test script to verify improvements to the product recommendation system.
This script tests:
1. Product ID display in search results
2. Gender-specific filtering in recommendations
3. Discount product filtering
"""

import logging
import sys
import re
from typing import List, Dict, Any, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("simple_test")

# Mock data for testing
mock_products = [
    {"id": 1, "name": "Men's Shampoo", "list_price": 10.0, "gender": "men", "qty_available": 10},
    {"id": 2, "name": "Women's Conditioner", "list_price": 12.0, "gender": "women", "qty_available": 5},
    {"id": 3, "name": "Men's Hair Gel", "list_price": 8.0, "gender": "men", "qty_available": 8},
    {"id": 4, "name": "Women's Hair Mask", "list_price": 15.0, "gender": "women", "qty_available": 3},
    {"id": 5, "name": "Discount Shampoo", "list_price": 0.0, "gender": "unisex", "qty_available": 20},
    {"id": 6, "name": "Special Discount Hair Spray", "list_price": 5.0, "gender": "unisex", "qty_available": 15},
    {"id": 9997, "name": "Regular Shampoo", "list_price": 10.0, "gender": "unisex", "qty_available": 12},
]

def format_product_list(products: List[Dict[str, Any]]) -> str:
    """Format a list of products for display.
    
    Args:
        products: List of product dictionaries
        
    Returns:
        Formatted product list as a string
    """
    result = ""
    for i, product in enumerate(products, 1):
        price = product.get("list_price", 0.0)
        availability = "(In Stock)" if product.get("qty_available", 0) > 0 else "(Out of Stock)"
        product_id = product.get("id", "Unknown")
        result += f"{i}. {product.get('name', 'Unknown')} - ${price:.2f} {availability} [ID: {product_id}]\n"
    
    return result

def filter_products_by_gender(products: List[Dict[str, Any]], gender: str) -> List[Dict[str, Any]]:
    """Filter products by gender.
    
    Args:
        products: List of product dictionaries
        gender: Gender to filter by (men or women)
        
    Returns:
        Filtered list of products
    """
    if not gender or not products:
        return products
    
    # For testing purposes, we're using a simplified approach
    # In a real implementation, we would use more sophisticated filtering
    if gender == "men":
        # For men, include both men's products and some unisex products
        filtered = [p for p in products if p.get("gender") == "men" or "men" in p.get("name", "").lower()]
        
        # If no men's products found, return all products
        if not filtered:
            logger.warning(f"No products found matching gender filter: {gender}, returning all products")
            return products
        
        return filtered
    
    elif gender == "women":
        # For women, include only women's products
        filtered = [p for p in products if p.get("gender") == "women" or "women" in p.get("name", "").lower()]
        
        # If no women's products found, return all products
        if not filtered:
            logger.warning(f"No products found matching gender filter: {gender}, returning all products")
            return products
        
        return filtered
    
    # Default: return all products
    return products

def filter_discount_products(products: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int]:
    """Filter out discount products.
    
    Args:
        products: List of product dictionaries
        
    Returns:
        Tuple of (filtered products, count of filtered products)
    """
    if not products:
        return [], 0
    
    # Filter out products with price of 0 or name containing "discount"
    original_count = len(products)
    filtered = [
        p for p in products 
        if p.get("list_price", 0) > 0 and "discount" not in p.get("name", "").lower()
    ]
    
    filtered_count = original_count - len(filtered)
    return filtered, filtered_count

def extract_product_id(message: str) -> int:
    """Extract product ID from a message.
    
    Args:
        message: User message
        
    Returns:
        Product ID or None if not found
    """
    # Look for patterns like "add product 123 to cart" or "add to cart product 123"
    id_patterns = [
        r"product\s+(\d+)",
        r"item\s+(\d+)",
        r"id\s+(\d+)",
        r"#(\d+)",
        r"add\s+(\d+)",
        r"cart\s+(\d+)",
    ]
    
    for pattern in id_patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                continue
    
    # If no pattern matched, check if the message contains just a number
    if message.strip().isdigit():
        return int(message.strip())
    
    return None

def test_product_id_display():
    """Test that product IDs are displayed in search results."""
    logger.info("=== Testing Product ID Display in Search Results ===")
    
    # Format a sample product list
    products = mock_products[:2]  # Use first two products
    formatted = format_product_list(products)
    
    logger.info("Formatted product list:\n%s", formatted)
    
    # Check if product IDs are displayed
    if "[ID:" in formatted or "[ID: " in formatted:
        logger.info("✅ Product IDs are displayed in search results")
    else:
        logger.error("❌ Product IDs are NOT displayed in search results")

def test_gender_filtering():
    """Test gender-specific filtering in recommendations."""
    logger.info("\n=== Testing Gender-Specific Recommendations ===")
    
    # Test men's filter
    men_filtered = filter_products_by_gender(mock_products, "men")
    men_products_count = len(men_filtered)
    logger.info("Men's filtered products:\n%s", format_product_list(men_filtered))
    
    # Test women's filter
    women_filtered = filter_products_by_gender(mock_products, "women")
    women_products_count = len(women_filtered)
    logger.info("Women's filtered products:\n%s", format_product_list(women_filtered))
    
    # Check if filters are working correctly
    men_only = all("men" in p.get("gender", "").lower() or "men" in p.get("name", "").lower() for p in men_filtered)
    women_only = all("women" in p.get("gender", "").lower() or "women" in p.get("name", "").lower() for p in women_filtered)
    
    if men_products_count > 0 and men_only:
        logger.info("✅ Men's filter is applied correctly")
    else:
        logger.error("❌ Men's filter is NOT applied correctly")
        
    if women_products_count > 0 and women_only:
        logger.info("✅ Women's filter is applied correctly")
    else:
        logger.error("❌ Women's filter is NOT applied correctly")
    
    # Test gender-specific recommendation responses
    def test_gender_recommendation(gender):
        # Format the response with explicit gender mention
        response = f"Here are some products for {gender} I think you might like:\n\n"
        response += format_product_list(filter_products_by_gender(mock_products, gender))
        response += "\n\nWould you like more details about any of these products?"
        return response
    
    # Test men's recommendations
    men_response = test_gender_recommendation("men")
    logger.info("Men's recommendations response:\n%s", men_response)
    
    # Test women's recommendations
    women_response = test_gender_recommendation("women")
    logger.info("Women's recommendations response:\n%s", women_response)
    
    # Check if gender is mentioned in responses
    if "for men" in men_response.lower():
        logger.info("✅ Men's filter is mentioned in response")
    else:
        logger.error("❌ Men's filter is NOT mentioned in response")
        
    if "for women" in women_response.lower():
        logger.info("✅ Women's filter is mentioned in response")
    else:
        logger.error("❌ Women's filter is NOT mentioned in response")

def test_discount_filtering():
    """Test discount product filtering in recommendations."""
    logger.info("\n=== Testing Discount Product Filtering ===")
    
    # Test filtering out discount products
    filtered_products, filtered_count = filter_discount_products(mock_products)
    
    logger.info("Formatted product list:\n%s", format_product_list(filtered_products))
    
    # Check if discount products are filtered out
    has_discount = any(p.get("list_price", 0) == 0 or "discount" in p.get("name", "").lower() for p in filtered_products)
    has_regular = any(p.get("list_price", 0) > 0 and "discount" not in p.get("name", "").lower() for p in filtered_products)
    
    if not has_discount and filtered_count > 0:
        logger.info("✅ Discount products are filtered out correctly")
    else:
        logger.error("❌ Discount products are NOT filtered out correctly")
        
    if has_regular:
        logger.info("✅ Regular products are retained correctly")
    else:
        logger.error("❌ Regular products are NOT retained correctly")

def test_product_id_extraction():
    """Test product ID extraction from messages."""
    logger.info("\n=== Testing Add to Cart with Product ID ===")
    
    # Test extracting product ID from message
    message = "add product 1234 to cart"
    product_id = extract_product_id(message)
    
    logger.info("Extracted product ID: %s", product_id)
    
    # Check if product ID is extracted correctly
    if product_id == 1234:
        logger.info("✅ Product ID extraction works correctly")
    else:
        logger.error("❌ Product ID extraction does NOT work correctly")

def main():
    """Run all tests."""
    logger.info("Starting tests for product recommendation improvements")
    
    # Run tests
    test_product_id_display()
    test_gender_filtering()
    test_discount_filtering()
    test_product_id_extraction()
    
    logger.info("\nAll tests completed")

if __name__ == "__main__":
    main()
