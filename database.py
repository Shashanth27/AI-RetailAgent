"""Database operations for the Retail CRM Console Single AI Agent."""

import logging
import json
import sqlite3
import psycopg2
from typing import Dict, List, Tuple, Optional, Any, Union

import numpy as np

import config


class Database:
    """Database operations for the Retail CRM Console Single AI Agent."""
    
    def __init__(self):
        """Initialize the database connection."""
        self.conn = None
        self.cursor = None
        self.logger = logging.getLogger(__name__)
    
    def connect(self) -> None:
        """Connect to the database."""
        try:
            if config.USE_SQLITE:
                self.logger.info(f"Connecting to SQLite database: {config.SQLITE_DB}")
                self.conn = sqlite3.connect(config.SQLITE_DB)
                # Enable foreign keys
                self.conn.execute("PRAGMA foreign_keys = ON")
                # Convert rows to dictionaries
                self.conn.row_factory = sqlite3.Row
            else:
                self.logger.info(f"Connecting to PostgreSQL database: {config.POSTGRES_DB}")
                self.conn = psycopg2.connect(
                    host=config.POSTGRES_HOST,
                    port=config.POSTGRES_PORT,
                    database=config.POSTGRES_DB,
                    user=config.POSTGRES_USER,
                    password=config.POSTGRES_PASSWORD
                )
            
            self.cursor = self.conn.cursor()
            self.logger.info("Database connection established")
        except Exception as e:
            self.logger.error(f"Error connecting to database: {e}")
            raise
    
    def disconnect(self) -> None:
        """Disconnect from the database."""
        try:
            if self.conn:
                self.conn.close()
                self.conn = None
                self.cursor = None
                self.logger.info("Database connection closed")
        except Exception as e:
            self.logger.error(f"Error disconnecting from database: {e}")
    
    def create_tables(self) -> None:
        """Create database tables if they don't exist."""
        try:
            if config.USE_SQLITE:
                # SQLite tables
                self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    price REAL NOT NULL,
                    available BOOLEAN NOT NULL DEFAULT 1,
                    tags TEXT
                )
                ''')
                
                self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS embeddings (
                    product_id INTEGER PRIMARY KEY,
                    embedding BLOB NOT NULL,
                    FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE
                )
                ''')
                
                self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_preferences (
                    user_id INTEGER NOT NULL,
                    product_id INTEGER NOT NULL,
                    score REAL NOT NULL,
                    PRIMARY KEY (user_id, product_id),
                    FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE
                )
                ''')
            else:
                # PostgreSQL tables
                self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS products (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    price REAL NOT NULL,
                    available BOOLEAN NOT NULL DEFAULT TRUE,
                    tags TEXT
                )
                ''')
                
                self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS embeddings (
                    product_id INTEGER PRIMARY KEY REFERENCES products (id) ON DELETE CASCADE,
                    embedding BYTEA NOT NULL
                )
                ''')
                
                self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_preferences (
                    user_id INTEGER NOT NULL,
                    product_id INTEGER NOT NULL REFERENCES products (id) ON DELETE CASCADE,
                    score REAL NOT NULL,
                    PRIMARY KEY (user_id, product_id)
                )
                ''')
            
            self.conn.commit()
            self.logger.info("Database tables created")
        except Exception as e:
            self.logger.error(f"Error creating database tables: {e}")
            raise
    
    def store_product(self, product: Dict[str, Any]) -> bool:
        """Store a product in the database.
        
        Args:
            product: Product data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Convert tags list to JSON string
            tags_json = json.dumps(product.get('tags', []))
            
            if config.USE_SQLITE:
                self.cursor.execute('''
                INSERT OR REPLACE INTO products (id, name, description, price, available, tags)
                VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    product['id'],
                    product['name'],
                    product['description'],
                    product['price'],
                    product['available'],
                    tags_json
                ))
            else:
                self.cursor.execute('''
                INSERT INTO products (id, name, description, price, available, tags)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE
                SET name = EXCLUDED.name,
                    description = EXCLUDED.description,
                    price = EXCLUDED.price,
                    available = EXCLUDED.available,
                    tags = EXCLUDED.tags
                ''', (
                    product['id'],
                    product['name'],
                    product['description'],
                    product['price'],
                    product['available'],
                    tags_json
                ))
            
            self.conn.commit()
            self.logger.info(f"Product {product['id']} stored in database")
            return True
        except Exception as e:
            self.logger.error(f"Error storing product: {e}")
            self.conn.rollback()
            return False
    
    def get_product(self, product_id: int) -> Optional[Dict[str, Any]]:
        """Get a product from the database.
        
        Args:
            product_id: ID of the product
            
        Returns:
            Product data or None if not found
        """
        try:
            if config.USE_SQLITE:
                self.cursor.execute('''
                SELECT * FROM products WHERE id = ?
                ''', (product_id,))
                row = self.cursor.fetchone()
            else:
                self.cursor.execute('''
                SELECT * FROM products WHERE id = %s
                ''', (product_id,))
                row = self.cursor.fetchone()
            
            if not row:
                return None
            
            # Convert row to dictionary
            if config.USE_SQLITE:
                product = dict(row)
            else:
                columns = [desc[0] for desc in self.cursor.description]
                product = dict(zip(columns, row))
            
            # Parse tags JSON
            if product['tags']:
                product['tags'] = json.loads(product['tags'])
            else:
                product['tags'] = []
            
            return product
        except Exception as e:
            self.logger.error(f"Error getting product: {e}")
            return None
    
    def get_products(self, available_only: bool = False) -> List[Dict[str, Any]]:
        """Get all products from the database.
        
        Args:
            available_only: If True, only return available products
            
        Returns:
            List of products
        """
        try:
            if available_only:
                if config.USE_SQLITE:
                    self.cursor.execute('''
                    SELECT * FROM products WHERE available = 1
                    ''')
                else:
                    self.cursor.execute('''
                    SELECT * FROM products WHERE available = TRUE
                    ''')
            else:
                self.cursor.execute('''
                SELECT * FROM products
                ''')
            
            rows = self.cursor.fetchall()
            products = []
            
            for row in rows:
                if config.USE_SQLITE:
                    product = dict(row)
                else:
                    columns = [desc[0] for desc in self.cursor.description]
                    product = dict(zip(columns, row))
                
                # Parse tags JSON
                if product['tags']:
                    product['tags'] = json.loads(product['tags'])
                else:
                    product['tags'] = []
                
                products.append(product)
            
            return products
        except Exception as e:
            self.logger.error(f"Error getting products: {e}")
            return []
    
    def search_products(self, query: str, available_only: bool = False) -> List[Dict[str, Any]]:
        """Search for products in the database.
        
        Args:
            query: Search query
            available_only: If True, only return available products
            
        Returns:
            List of matching products
        """
        try:
            search_term = f"%{query}%"
            
            if available_only:
                if config.USE_SQLITE:
                    self.cursor.execute('''
                    SELECT * FROM products 
                    WHERE (name LIKE ? OR description LIKE ? OR tags LIKE ?) AND available = 1
                    ''', (search_term, search_term, search_term))
                else:
                    self.cursor.execute('''
                    SELECT * FROM products 
                    WHERE (name ILIKE %s OR description ILIKE %s OR tags ILIKE %s) AND available = TRUE
                    ''', (search_term, search_term, search_term))
            else:
                if config.USE_SQLITE:
                    self.cursor.execute('''
                    SELECT * FROM products 
                    WHERE name LIKE ? OR description LIKE ? OR tags LIKE ?
                    ''', (search_term, search_term, search_term))
                else:
                    self.cursor.execute('''
                    SELECT * FROM products 
                    WHERE name ILIKE %s OR description ILIKE %s OR tags ILIKE %s
                    ''', (search_term, search_term, search_term))
            
            rows = self.cursor.fetchall()
            products = []
            
            for row in rows:
                if config.USE_SQLITE:
                    product = dict(row)
                else:
                    columns = [desc[0] for desc in self.cursor.description]
                    product = dict(zip(columns, row))
                
                # Parse tags JSON
                if product['tags']:
                    product['tags'] = json.loads(product['tags'])
                else:
                    product['tags'] = []
                
                products.append(product)
            
            return products
        except Exception as e:
            self.logger.error(f"Error searching products: {e}")
            return []
    
    def store_embedding(self, product_id: int, embedding: List[float]) -> bool:
        """Store a product embedding in the database.
        
        Args:
            product_id: ID of the product
            embedding: Embedding vector
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Convert embedding to bytes
            embedding_bytes = np.array(embedding, dtype=np.float32).tobytes()
            
            if config.USE_SQLITE:
                self.cursor.execute('''
                INSERT OR REPLACE INTO embeddings (product_id, embedding)
                VALUES (?, ?)
                ''', (product_id, embedding_bytes))
            else:
                self.cursor.execute('''
                INSERT INTO embeddings (product_id, embedding)
                VALUES (%s, %s)
                ON CONFLICT (product_id) DO UPDATE
                SET embedding = EXCLUDED.embedding
                ''', (product_id, psycopg2.Binary(embedding_bytes)))
            
            self.conn.commit()
            self.logger.info(f"Embedding for product {product_id} stored in database")
            return True
        except Exception as e:
            self.logger.error(f"Error storing embedding: {e}")
            self.conn.rollback()
            return False
    
    def get_embeddings(self) -> List[Tuple[int, np.ndarray]]:
        """Get all product embeddings from the database.
        
        Returns:
            List of tuples (product_id, embedding)
        """
        try:
            self.cursor.execute('''
            SELECT product_id, embedding FROM embeddings
            ''')
            
            rows = self.cursor.fetchall()
            embeddings = []
            
            for row in rows:
                if config.USE_SQLITE:
                    product_id = row[0]
                    embedding_bytes = row[1]
                else:
                    product_id = row[0]
                    embedding_bytes = bytes(row[1])
                
                # Convert bytes to numpy array
                embedding = np.frombuffer(embedding_bytes, dtype=np.float32)
                
                embeddings.append((product_id, embedding))
            
            return embeddings
        except Exception as e:
            self.logger.error(f"Error getting embeddings: {e}")
            return []
    
    def store_user_preference(self, user_id: int, product_id: int, score: float) -> bool:
        """Store a user preference in the database.
        
        Args:
            user_id: ID of the user
            product_id: ID of the product
            score: Preference score
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if config.USE_SQLITE:
                self.cursor.execute('''
                INSERT OR REPLACE INTO user_preferences (user_id, product_id, score)
                VALUES (?, ?, ?)
                ''', (user_id, product_id, score))
            else:
                self.cursor.execute('''
                INSERT INTO user_preferences (user_id, product_id, score)
                VALUES (%s, %s, %s)
                ON CONFLICT (user_id, product_id) DO UPDATE
                SET score = EXCLUDED.score
                ''', (user_id, product_id, score))
            
            self.conn.commit()
            self.logger.info(f"Preference for user {user_id}, product {product_id} stored in database")
            return True
        except Exception as e:
            self.logger.error(f"Error storing user preference: {e}")
            self.conn.rollback()
            return False
    
    def get_user_preferences(self, user_id: int) -> Dict[int, float]:
        """Get user preferences from the database.
        
        Args:
            user_id: ID of the user
            
        Returns:
            Dictionary mapping product_id to score
        """
        try:
            if config.USE_SQLITE:
                self.cursor.execute('''
                SELECT product_id, score FROM user_preferences WHERE user_id = ?
                ''', (user_id,))
            else:
                self.cursor.execute('''
                SELECT product_id, score FROM user_preferences WHERE user_id = %s
                ''', (user_id,))
            
            rows = self.cursor.fetchall()
            preferences = {}
            
            for row in rows:
                product_id = row[0]
                score = row[1]
                preferences[product_id] = score
            
            return preferences
        except Exception as e:
            self.logger.error(f"Error getting user preferences: {e}")
            return {}
    
    def create_user_preferences_table(self) -> None:
        """Create the user_preferences_json table if it doesn't exist."""
        try:
            if config.USE_SQLITE:
                self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_preferences_json (
                    user_id INTEGER PRIMARY KEY,
                    preferences_json TEXT NOT NULL
                )
                ''')
            else:
                self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_preferences_json (
                    user_id INTEGER PRIMARY KEY,
                    preferences_json TEXT NOT NULL
                )
                ''')
            
            self.conn.commit()
            self.logger.info("User preferences JSON table created")
        except Exception as e:
            self.logger.error(f"Error creating user preferences JSON table: {e}")
            self.conn.rollback()
    
    def update_user_preferences(self, user_id: int, preferences_json: str) -> bool:
        """Update user preferences JSON in the database.
        
        Args:
            user_id: ID of the user
            preferences_json: JSON string of user preferences
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure the table exists
            self.create_user_preferences_table()
            
            if config.USE_SQLITE:
                self.cursor.execute('''
                INSERT OR REPLACE INTO user_preferences_json (user_id, preferences_json)
                VALUES (?, ?)
                ''', (user_id, preferences_json))
            else:
                self.cursor.execute('''
                INSERT INTO user_preferences_json (user_id, preferences_json)
                VALUES (%s, %s)
                ON CONFLICT (user_id) DO UPDATE
                SET preferences_json = EXCLUDED.preferences_json
                ''', (user_id, preferences_json))
            
            self.conn.commit()
            self.logger.info(f"Preferences JSON for user {user_id} stored in database")
            return True
        except Exception as e:
            self.logger.error(f"Error storing user preferences JSON: {e}")
            self.conn.rollback()
            return False
    
    def get_user_preferences_json(self, user_id: int) -> Optional[str]:
        """Get user preferences JSON from the database.
        
        Args:
            user_id: ID of the user
            
        Returns:
            JSON string of user preferences or None if not found
        """
        try:
            # Ensure the table exists
            self.create_user_preferences_table()
            
            if config.USE_SQLITE:
                self.cursor.execute('''
                SELECT preferences_json FROM user_preferences_json WHERE user_id = ?
                ''', (user_id,))
            else:
                self.cursor.execute('''
                SELECT preferences_json FROM user_preferences_json WHERE user_id = %s
                ''', (user_id,))
            
            row = self.cursor.fetchone()
            
            if row:
                return row[0]
            else:
                return None
        except Exception as e:
            self.logger.error(f"Error getting user preferences JSON: {e}")
            return None
    
    def close(self) -> None:
        """Close the database connection."""
        self.disconnect()
