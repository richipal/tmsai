"""
Configuration module for the Flask application
"""
import os
import logging

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Package availability flags
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    logger.warning("Requests module not available, HTTP client will not work")

try:
    import vanna
    import vanna.remote
    VANNA_AVAILABLE = True
    VANNA_REMOTE_AVAILABLE = True
except ImportError:
    VANNA_AVAILABLE = False
    VANNA_REMOTE_AVAILABLE = False
    logger.warning("Vanna module not available, using custom implementation")

try:
    import chromadb
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    logger.warning("ChromaDB module not available, in-memory vector store will not work")

# Get API key from environment
API_KEY = os.environ.get("VANNA_API_KEY", "demo")
# Initialize Vanna AI with mode from environment variable
VANNA_MODEL = os.environ.get('VANNA_MODEL', 'demo')
logger.info(f"Using Vanna model: {VANNA_MODEL}")

# Default examples for the UI
DEFAULT_EXAMPLES = [
    "Show me the top 5 products by revenue",
    "How many orders do we have by country?",
    "What is our monthly sales trend for 2023?",
    "Which products are running low on inventory?",
    "How many products do we have in each category?"
]

# Sample schema for the Northwind database
MOCK_TABLES = [
    "CREATE TABLE customers (customer_id VARCHAR PRIMARY KEY, company_name VARCHAR, contact_name VARCHAR, country VARCHAR);",
    "CREATE TABLE products (product_id INT PRIMARY KEY, product_name VARCHAR, unit_price DECIMAL, units_in_stock INT, units_on_order INT, discontinued BOOLEAN, category_id INT);",
    "CREATE TABLE orders (order_id INT PRIMARY KEY, customer_id VARCHAR, order_date DATE);",
    "CREATE TABLE order_details (order_id INT, product_id INT, quantity INT, unit_price DECIMAL);",
    "CREATE TABLE categories (category_id INT PRIMARY KEY, category_name VARCHAR, description VARCHAR);"
]