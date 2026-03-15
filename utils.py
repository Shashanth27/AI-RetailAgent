"""Utility functions for the Retail CRM Console Single AI Agent."""

import logging
import os
import sys
from typing import Dict, Any, Optional

from colorama import Fore, Style


def setup_logging(level: int = logging.INFO, log_file: Optional[str] = None) -> None:
    """Set up logging configuration.
    
    Args:
        level: Logging level
        log_file: Path to log file
    """
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(level)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Create file handler if log file is specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)


def print_colored(text: str, color: str = Fore.WHITE, bold: bool = False, center: bool = False) -> None:
    """Print colored text.
    
    Args:
        text: Text to print
        color: Color to use
        bold: Whether to print in bold
        center: Whether to center the text
    """
    if center:
        terminal_width = os.get_terminal_size().columns
        text = text.center(terminal_width)
    
    if bold:
        print(f"{color}{Style.BRIGHT}{text}{Style.RESET_ALL}")
    else:
        print(f"{color}{text}{Style.RESET_ALL}")


def print_product(product: Dict[str, Any]) -> None:
    """Print product information.
    
    Args:
        product: Product data
    """
    print("\n" + "-" * 50)
    print_colored(f"ID: {product.get('id', 'N/A')}", Fore.CYAN)
    print_colored(f"Name: {product.get('name', 'N/A')}", Fore.GREEN, bold=True)
    
    # Handle different price keys
    if 'price' in product:
        price = product['price']
    elif 'list_price' in product:
        price = product['list_price']
    else:
        price = 0.0
    print_colored(f"Price: ₴{price:.2f}", Fore.YELLOW)
    
    # Handle different availability keys
    if 'available' in product:
        available = product['available']
    elif 'qty_available' in product:
        available = product['qty_available'] > 0
    else:
        available = False
    print_colored(f"Available: {'Yes' if available else 'No'}", 
                 Fore.GREEN if available else Fore.RED)
    
    # Handle description
    if 'description' in product:
        description = product['description']
    elif 'description_sale' in product:
        description = product['description_sale']
    else:
        description = 'No description available'
    print_colored(f"Description: {description}")
    
    # Handle tags
    if 'tags' in product and product['tags']:
        tags_str = ", ".join(product['tags'])
        print_colored(f"Tags: {tags_str}", Fore.BLUE)
    
    # Add product code if available
    if 'default_code' in product and product['default_code']:
        print_colored(f"Product Code: {product['default_code']}", Fore.MAGENTA)
    
    print("-" * 50)


def print_cart(cart: Dict[str, Any]) -> None:
    """Print cart information.
    
    Args:
        cart: Cart data
    """
    print("\n" + "=" * 50)
    print_colored("Shopping Cart", Fore.CYAN, bold=True, center=True)
    print("=" * 50)
    
    if not cart.get('items'):
        print_colored("Your cart is empty", Fore.YELLOW)
        print("=" * 50)
        return
    
    print_colored(f"{'ID':<5} {'Name':<30} {'Price':<10} {'Qty':<5} {'Subtotal':<10}", Fore.WHITE, bold=True)
    print("-" * 50)
    
    for item in cart.get('items', []):
        product = item['product']
        quantity = item['quantity']
        subtotal = product['price'] * quantity
        
        print_colored(
            f"{product['id']:<5} {product['name'][:30]:<30} ₴{product['price']:<9.2f} {quantity:<5} ₴{subtotal:<9.2f}",
            Fore.WHITE
        )
    
    print("-" * 50)
    print_colored(f"Total Items: {cart.get('item_count', 0)}", Fore.YELLOW)
    print_colored(f"Total: ₴{cart.get('total', 0):.2f}", Fore.GREEN, bold=True)
    print("=" * 50)
