"""Retrieval-Augmented Generation (RAG) implementation for the Retail CRM Console Single AI Agent."""

import logging
import random
from typing import Dict, List, Tuple, Optional

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer

import config
from database import Database
from models import Product


class RAG:
    """Retrieval-Augmented Generation (RAG) for product recommendations."""
    
    def __init__(self, db: Database):
        """Initialize the RAG system.
        
        Args:
            db: Database instance
        """
        self.db = db
        self.model = SentenceTransformer(config.EMBEDDING_MODEL)
        self.embeddings = None
        self.product_ids = []
        self.logger = logging.getLogger(__name__)
        
        # Initialize the embeddings index
        self.initialize_index()
    
    def initialize_index(self) -> None:
        """Initialize the embeddings index with product embeddings from the database."""
        try:
            # Get product embeddings from database
            product_embeddings = self.db.get_embeddings()
            
            if not product_embeddings:
                self.logger.warning("No product embeddings found in database")
                # Create empty arrays
                self.product_ids = []
                self.embeddings = np.empty((0, config.VECTOR_DIMENSION), dtype=np.float32)
                return
            
            # Extract product IDs and embeddings
            self.product_ids = [pe[0] for pe in product_embeddings]
            self.embeddings = [pe[1] for pe in product_embeddings]
            
            self.logger.info(f"Initialized embeddings index with {len(self.product_ids)} products")
        except Exception as e:
            self.logger.error(f"Error initializing embeddings index: {e}")
            # Create empty arrays
            self.product_ids = []
            self.embeddings = []
    
    def update_index(self) -> None:
        """Update the embeddings index with the latest product embeddings."""
        self.initialize_index()
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate an embedding for the given text.
        
        Args:
            text: Text to generate embedding for
            
        Returns:
            Embedding vector
        """
        try:
            return self.model.encode(text, convert_to_numpy=True)
        except Exception as e:
            self.logger.error(f"Error generating embedding: {e}")
            return [0.0] * config.VECTOR_DIMENSION
    
    def generate_product_embedding(self, product: Product) -> List[float]:
        """Generate an embedding for a product.
        
        Args:
            product: Product to generate embedding for
            
        Returns:
            Embedding vector
        """
        # Combine product name, description, and tags for better embedding
        text = f"{product.name} {product.description} {' '.join(product.tags)}"
        return self.generate_embedding(text)
    
    def store_product_embedding(self, product: Product) -> bool:
        """Generate and store an embedding for a product.
        
        Args:
            product: Product to generate and store embedding for
            
        Returns:
            True if successful, False otherwise
        """
        try:
            embedding = self.generate_product_embedding(product)
            success = self.db.store_embedding(product.id, embedding)
            
            if success:
                self.update_index()
            
            return success
        except Exception as e:
            self.logger.error(f"Error storing product embedding: {e}")
            return False
    
    def search_similar_products(
        self, 
        query: str, 
        k: int = 5,
        exclude_ids: Optional[List[int]] = None
    ) -> List[int]:
        """Search for products similar to the query.
        
        Args:
            query: Search query
            k: Number of results to return
            exclude_ids: Product IDs to exclude from results
            
        Returns:
            List of product IDs
        """
        if self.embeddings is None or len(self.embeddings) == 0:
            self.logger.warning("Embeddings index is empty, returning empty results")
            return []
        
        try:
            # Generate embedding for query
            query_embedding = self.generate_embedding(query)
            
            # Use cosine similarity to find similar products
            similarities = [0.0] * len(self.product_ids)
            for i, embedding in enumerate(self.embeddings):
                similarities[i] = cosine_similarity([query_embedding], [embedding])[0][0]
            
            # Sort by similarity (highest first)
            sorted_indices = sorted(range(len(similarities)), key=lambda i: similarities[i], reverse=True)
            
            # Extract product IDs
            product_ids = []
            for idx in sorted_indices:
                if idx < len(self.product_ids):
                    product_id = self.product_ids[idx]
                    if not exclude_ids or product_id not in exclude_ids:
                        product_ids.append(product_id)
                        if len(product_ids) >= k:
                            break
            
            return product_ids
        except Exception as e:
            self.logger.error(f"Error searching similar products: {e}")
            return []
    
    def get_personalized_recommendations(
        self, 
        user_id: int, 
        k: int = 5,
        exclude_ids: Optional[List[int]] = None
    ) -> List[int]:
        """Get personalized product recommendations for a user.
        
        Args:
            user_id: User ID
            k: Number of recommendations to return
            exclude_ids: Product IDs to exclude from recommendations
            
        Returns:
            List of recommended product IDs
        """
        try:
            # Get user preferences
            user_preferences = self.db.get_user_preferences(user_id)
            
            if not user_preferences:
                self.logger.info(f"No preferences found for user {user_id}, returning generic recommendations")
                # Return generic recommendations
                return self.get_generic_recommendations(k, exclude_ids)
            
            # Get products for user's preferred products
            preferred_products = []
            for product_id, score in user_preferences.items():
                product = self.db.get_product(product_id)
                if product and product['available']:
                    preferred_products.append((product, score))
            
            if not preferred_products:
                self.logger.info(f"No available preferred products for user {user_id}, returning generic recommendations")
                # Return generic recommendations
                return self.get_generic_recommendations(k, exclude_ids)
            
            # Sort by preference score (highest first)
            preferred_products.sort(key=lambda x: x[1], reverse=True)
            
            # Use top preferred products to find similar products
            recommendations = set()
            for product, _ in preferred_products[:3]:  # Use top 3 preferred products
                # Create query from product
                query = f"{product['name']} {product['description']} {' '.join(product['tags'])}"
                
                # Search for similar products
                similar_products = self.search_similar_products(
                    query=query,
                    k=k,
                    exclude_ids=exclude_ids
                )
                
                # Add to recommendations
                recommendations.update(similar_products)
                
                # Exit if we have enough recommendations
                if len(recommendations) >= k:
                    break
            
            # If we don't have enough recommendations, add some generic ones
            if len(recommendations) < k:
                generic_recommendations = self.get_generic_recommendations(
                    k=k - len(recommendations),
                    exclude_ids=list(recommendations) + (exclude_ids or [])
                )
                recommendations.update(generic_recommendations)
            
            # Return top-k recommendations
            return list(recommendations)[:k]
        except Exception as e:
            self.logger.error(f"Error getting personalized recommendations: {e}")
            return self.get_generic_recommendations(k, exclude_ids)
    
    def get_generic_recommendations(
        self, 
        k: int = 5,
        exclude_ids: Optional[List[int]] = None
    ) -> List[int]:
        """Get generic product recommendations.
        
        Args:
            k: Number of recommendations to return
            exclude_ids: Product IDs to exclude from recommendations
            
        Returns:
            List of recommended product IDs
        """
        try:
            # Get all available products
            products = self.db.get_products(available_only=True)
            
            if not products:
                self.logger.warning("No available products for recommendations")
                return []
            
            # Filter out excluded product IDs
            if exclude_ids:
                products = [p for p in products if p['id'] not in exclude_ids]
            
            # If we have fewer products than requested, return all of them
            if len(products) <= k:
                return [p['id'] for p in products]
            
            # Otherwise return a random sample
            random.shuffle(products)
            return [p['id'] for p in products[:k]]
        except Exception as e:
            self.logger.error(f"Error getting generic recommendations: {e}")
            return []
