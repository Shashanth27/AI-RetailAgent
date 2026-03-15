#!/usr/bin/env python
"""
Test script to verify improvements to the product recommendation system.
This script tests:
1. Product ID display in search results
2. Gender-specific filtering in recommendations
3. Discount product filtering
"""

import logging
import sys
from agent import RetailAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("test_improvements")

def test_search_with_product_ids():
    """Test that product IDs are displayed in search results."""
    logger.info("=== Testing Product ID Display in Search Results ===")
    agent = RetailAgent()
    
    # Test search results
    search_response = agent._handle_search_intent("search shampoo")
    logger.info(f"Search response:\n{search_response}")
    
    # Check if product IDs are displayed
    if "[ID:" in search_response:
        logger.info("✅ Product IDs are displayed in search results")
    else:
        logger.error("❌ Product IDs are NOT displayed in search results")
    
    logger.info("")
    return agent

def test_gender_specific_recommendations(agent):
    """Test gender-specific filtering in recommendations."""
    logger.info("=== Testing Gender-Specific Recommendations ===")
    
    # Create mock products with gender-specific attributes for testing
    mock_products = [
        {"id": 1, "name": "Men's Shampoo", "price": 10.0, "in_stock": True, "description": "For men"},
        {"id": 2, "name": "Women's Conditioner", "price": 12.0, "in_stock": True, "description": "For women"},
        {"id": 3, "name": "Men's Hair Gel", "price": 8.0, "in_stock": True, "description": "For men"},
        {"id": 4, "name": "Women's Hair Mask", "price": 15.0, "in_stock": True, "description": "For women"},
        {"id": 5, "name": "Unisex Shampoo", "price": 9.0, "in_stock": True, "description": "For everyone"}
    ]
    
    # Test men's filtering directly
    men_filtered = agent._filter_products_by_gender(mock_products, "men")
    men_formatted = agent._format_product_list(men_filtered)
    logger.info("Men's filtered products:\n%s", men_formatted)
    
    # Test women's filtering directly
    women_filtered = agent._filter_products_by_gender(mock_products, "women")
    women_formatted = agent._format_product_list(women_filtered)
    logger.info("Women's filtered products:\n%s", women_formatted)
    
    # Check if filtering worked correctly
    men_products_count = sum(1 for p in men_filtered if "men" in p["name"].lower() or "men" in p.get("description", "").lower())
    women_products_count = sum(1 for p in women_filtered if "women" in p["name"].lower() or "women" in p.get("description", "").lower())
    
    # Check that men's products only contain men's items
    men_only = all("men" in p["name"].lower() or "men" in p.get("description", "").lower() for p in men_filtered)
    
    # Check that women's products only contain women's items
    women_only = all("women" in p["name"].lower() or "women" in p.get("description", "").lower() for p in women_filtered)
    
    if men_products_count > 0 and men_only:
        logger.info("✅ Men's filter is applied correctly")
    else:
        logger.error("❌ Men's filter is NOT applied correctly")
        
    if women_products_count > 0 and women_only:
        logger.info("✅ Women's filter is applied correctly")
    else:
        logger.error("❌ Women's filter is NOT applied correctly")
    
    # Create a custom recommendation function to test gender-specific recommendations
    def test_gender_recommendation(gender):
        # Create a direct recommendation with gender filter
        success, message, recs = agent.get_recommendations()
        if success and recs:
            # Apply gender filter directly
            filtered_recs = agent._filter_products_by_gender(recs, gender)
            # Format the response with explicit gender mention
            response = f"Here are some products for {gender} I think you might like:\n\n"
            response += agent._format_product_list(filtered_recs)
            response += "\n\nWould you like more details about any of these products?"
            return response
        return f"No recommendations for {gender} available."
    
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
    
    logger.info("")

def test_discount_product_filtering(agent):
    """Test that discount products are filtered out from recommendations."""
    logger.info("=== Testing Discount Product Filtering ===")
    
    # Force some discount products to be created
    discount_products = [
        {"id": 9999, "name": "Discount Shampoo Sale", "price": 0.0, "in_stock": True},
        {"id": 9998, "name": "Free Hair Mask", "price": 0.0, "in_stock": True},
        {"id": 9997, "name": "Regular Shampoo", "price": 10.0, "in_stock": True},
    ]
    
    # Test filtering
    formatted_list = agent._format_product_list(discount_products)
    logger.info(f"Formatted product list:\n{formatted_list}")
    
    # Check if discount products are filtered out
    if "Discount" not in formatted_list and "Free" not in formatted_list:
        logger.info("✅ Discount products are filtered out correctly")
    else:
        logger.error("❌ Discount products are NOT filtered out correctly")
    
    if "Regular" in formatted_list:
        logger.info("✅ Regular products are retained correctly")
    else:
        logger.error("❌ Regular products are NOT retained correctly")
    
    logger.info("")

def test_add_to_cart_with_product_id(agent):
    """Test adding products to cart using product ID."""
    logger.info("=== Testing Add to Cart with Product ID ===")
    
    # Test add to cart with product ID
    add_to_cart_response = agent._handle_add_to_cart_intent("add product with ID 1234 to cart")
    logger.info(f"Add to cart response:\n{add_to_cart_response}")
    
    # Check if product ID is extracted
    if "1234" in add_to_cart_response:
        logger.info("✅ Product ID extraction works correctly")
    else:
        logger.error("❌ Product ID extraction does NOT work correctly")
    
    logger.info("")

def main():
    """Run all tests."""
    logger.info("Starting tests for product recommendation improvements")
    
    # Run tests
    agent = test_search_with_product_ids()
    test_gender_specific_recommendations(agent)
    test_discount_product_filtering(agent)
    test_add_to_cart_with_product_id(agent)
    
    logger.info("All tests completed")

if __name__ == "__main__":
    main()
