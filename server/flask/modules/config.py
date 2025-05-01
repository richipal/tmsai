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
    
    # Try to import VannaDefault class first
    try:
        from vanna import VannaDefault
        VANNA_DEFAULT_AVAILABLE = True
        logger.info("VannaDefault class is available in the vanna package.")
    except (ImportError, AttributeError):
        VANNA_DEFAULT_AVAILABLE = False
        logger.warning("VannaDefault not available directly in vanna package.")
    
    # Try to access Vanna class
    try:
        if hasattr(vanna, 'Vanna'):
            VANNA_CLASS_AVAILABLE = True
            logger.info("Vanna class is available in the vanna package.")
        else:
            VANNA_CLASS_AVAILABLE = False
            logger.warning("Vanna class not found in vanna package.")
    except Exception as e:
        VANNA_CLASS_AVAILABLE = False
        logger.warning(f"Error checking for Vanna class: {str(e)}")
    
    # Try to import vanna.remote
    try:
        import vanna.remote
        VANNA_REMOTE_AVAILABLE = True
        logger.info("vanna.remote module is available.")
    except ImportError:
        VANNA_REMOTE_AVAILABLE = False
        logger.warning("vanna.remote module not available.")
    
    VANNA_AVAILABLE = True
    logger.info(f"Vanna version {vanna.__version__} successfully imported.")
except ImportError as e:
    VANNA_AVAILABLE = False
    VANNA_DEFAULT_AVAILABLE = False
    VANNA_CLASS_AVAILABLE = False
    VANNA_REMOTE_AVAILABLE = False
    logger.warning(f"Vanna module not available: {str(e)}")

try:
    import chromadb
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    logger.warning(
        "ChromaDB module not available, in-memory vector store will not work")

# Get OpenAI API key from environment to use as Vanna API key
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# Use OpenAI API key for Vanna API
API_KEY = OPENAI_API_KEY

# Configure model name to use with Vanna
VANNA_MODEL = 'gpt-4o'

# Flag to indicate we're running in local mode (no API key/cloud dependencies)
LOCAL_MODE = API_KEY is None

logger.info(f"Using Vanna with model: {VANNA_MODEL} and OpenAI API key")

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
