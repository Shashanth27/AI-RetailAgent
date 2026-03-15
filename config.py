"""Configuration settings for the Retail CRM Console Single AI Agent."""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ODOO_API_KEY = os.getenv("ODOO_API_KEY")

# OpenAI Model
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

# Odoo API Settings
ODOO_API_URL = os.getenv("ODOO_URL", "https://odoo.example.com/api")
ODOO_DB = os.getenv("ODOO_DB", "odoo")
ODOO_USERNAME = os.getenv("ODOO_USERNAME", "admin")
ODOO_PASSWORD = os.getenv("ODOO_PASSWORD", "admin")

# API Endpoints
# Odoo JSON-RPC endpoint
JSON_RPC_ENDPOINT = "jsonrpc"
# Legacy endpoints (not used with direct JSON-RPC implementation)
AUTH_ENDPOINT = "jsonrpc"
PRODUCTS_ENDPOINT = "jsonrpc"
CHECKOUT_ENDPOINT = "jsonrpc"
RECOMMENDATIONS_ENDPOINT = "jsonrpc"

# Database Settings
USE_SQLITE = os.getenv("USE_SQLITE", "True").lower() in ("true", "1", "t")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_DB = os.getenv("POSTGRES_DB", "retail_agent")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
SQLITE_DB = os.getenv("SQLITE_DB", "retail_agent.db")

# RAG Settings
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
VECTOR_DIMENSION = 384  # Dimension of the embedding vectors for all-MiniLM-L6-v2

# Logging Settings
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", "retail_agent.log")

# API Request Settings
MAX_RESPONSE_TIME = int(os.getenv("MAX_RESPONSE_TIME", "10"))  # seconds
