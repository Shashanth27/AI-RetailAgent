"""Data models for the Retail CRM Console Single AI Agent."""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class Product(BaseModel):
    """Product model."""
    
    id: int
    name: str
    description: str
    price: float
    available: bool = True
    default_code: str = ""
    tags: List[str] = Field(default_factory=list)


class CartItem(BaseModel):
    """Cart item model."""
    
    product: Product
    quantity: int = 1
    
    @property
    def subtotal(self) -> float:
        """Calculate subtotal for this item."""
        return self.product.price * self.quantity


class Cart(BaseModel):
    """Shopping cart model."""
    
    user_id: Optional[int] = None
    items: List[CartItem] = Field(default_factory=list)
    
    @property
    def total(self) -> float:
        """Calculate total for all items in the cart."""
        return sum(item.subtotal for item in self.items)
    
    @property
    def item_count(self) -> int:
        """Calculate total number of items in the cart."""
        return sum(item.quantity for item in self.items)
    
    def add_item(self, product: Product, quantity: int = 1) -> None:
        """Add a product to the cart.
        
        Args:
            product: Product to add
            quantity: Quantity to add
        """
        # Check if product is already in cart
        for item in self.items:
            if item.product.id == product.id:
                item.quantity += quantity
                return
        
        # Add new item
        self.items.append(CartItem(product=product, quantity=quantity))
    
    def update_item(self, product_id: int, quantity: int) -> None:
        """Update quantity of a product in the cart.
        
        Args:
            product_id: ID of the product to update
            quantity: New quantity
        """
        for item in self.items:
            if item.product.id == product_id:
                item.quantity = quantity
                return
    
    def remove_item(self, product_id: int) -> None:
        """Remove a product from the cart.
        
        Args:
            product_id: ID of the product to remove
        """
        self.items = [item for item in self.items if item.product.id != product_id]
    
    def clear(self) -> None:
        """Clear the cart."""
        self.items = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert cart to dictionary for API requests."""
        return {
            "user_id": self.user_id,
            "items": [
                {
                    "product_id": item.product.id,
                    "quantity": item.quantity,
                    "price": item.product.price
                }
                for item in self.items
            ],
            "total": self.total
        }


class User(BaseModel):
    """User model."""
    
    id: int
    name: str
    email: str


# API Response Models
class ApiResponse(BaseModel):
    """Base API response model."""
    
    success: bool
    error: Optional[str] = None


class AuthResponse(ApiResponse):
    """Authentication response model."""
    
    token: Optional[str] = None
    user: Optional[User] = None
    message: Optional[str] = None
    uid: Optional[int] = None


class ProductsResponse(ApiResponse):
    """Products response model."""
    
    products: List[Product] = Field(default_factory=list)


class RecommendationsResponse(ApiResponse):
    """Recommendations response model."""
    
    recommendations: List[Product] = Field(default_factory=list)


class CheckoutResponse(ApiResponse):
    """Checkout response model."""
    
    order_id: Optional[int] = None
    order_total: Optional[float] = None
