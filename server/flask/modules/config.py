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

# Northwind-specific examples for the UI based on actual schema
DEFAULT_EXAMPLES = [
    "List the top 5 products by revenue",
    "How many orders do we have by customer country?",
    "Show the monthly sales trend for 2018",
    "Which products are running low on inventory?",
    "What is the average order value by country?",
    "Which products have the highest profit margin?",
    "Show me sales by category for the last quarter",
    "Who are our top 10 customers by order volume?"
]

# Comprehensive schema for the Northwind database
NORTHWIND_SCHEMA = [
    """CREATE TABLE categories (
        category_id INT PRIMARY KEY,
        category_name VARCHAR(15) NOT NULL,
        description TEXT,
        picture BLOB
    );""",
    
    """CREATE TABLE customers (
        customer_id VARCHAR(5) PRIMARY KEY,
        company_name VARCHAR(40) NOT NULL,
        contact_name VARCHAR(30),
        contact_title VARCHAR(30),
        address VARCHAR(60),
        city VARCHAR(15),
        region VARCHAR(15),
        postal_code VARCHAR(10),
        country VARCHAR(15),
        phone VARCHAR(24),
        fax VARCHAR(24)
    );""",
    
    """CREATE TABLE employees (
        employee_id INT PRIMARY KEY,
        last_name VARCHAR(20) NOT NULL,
        first_name VARCHAR(10) NOT NULL,
        title VARCHAR(30),
        title_of_courtesy VARCHAR(25),
        birth_date DATE,
        hire_date DATE,
        address VARCHAR(60),
        city VARCHAR(15),
        region VARCHAR(15),
        postal_code VARCHAR(10),
        country VARCHAR(15),
        home_phone VARCHAR(24),
        extension VARCHAR(4),
        photo BLOB,
        notes TEXT,
        reports_to INT,
        photo_path VARCHAR(255),
        FOREIGN KEY (reports_to) REFERENCES employees (employee_id)
    );""",
    
    """CREATE TABLE suppliers (
        supplier_id INT PRIMARY KEY,
        company_name VARCHAR(40) NOT NULL,
        contact_name VARCHAR(30),
        contact_title VARCHAR(30),
        address VARCHAR(60),
        city VARCHAR(15),
        region VARCHAR(15),
        postal_code VARCHAR(10),
        country VARCHAR(15),
        phone VARCHAR(24),
        fax VARCHAR(24),
        homepage TEXT
    );""",
    
    """CREATE TABLE products (
        product_id INT PRIMARY KEY,
        product_name VARCHAR(40) NOT NULL,
        supplier_id INT,
        category_id INT,
        quantity_per_unit VARCHAR(20),
        unit_price DECIMAL(10,2),
        units_in_stock INT,
        units_on_order INT,
        reorder_level INT,
        discontinued BOOLEAN NOT NULL,
        FOREIGN KEY (category_id) REFERENCES categories (category_id),
        FOREIGN KEY (supplier_id) REFERENCES suppliers (supplier_id)
    );""",
    
    """CREATE TABLE shippers (
        shipper_id INT PRIMARY KEY,
        company_name VARCHAR(40) NOT NULL,
        phone VARCHAR(24)
    );""",
    
    """CREATE TABLE orders (
        order_id INT PRIMARY KEY,
        customer_id VARCHAR(5),
        employee_id INT,
        order_date DATE,
        required_date DATE,
        shipped_date DATE,
        ship_via INT,
        freight DECIMAL(10,2),
        ship_name VARCHAR(40),
        ship_address VARCHAR(60),
        ship_city VARCHAR(15),
        ship_region VARCHAR(15),
        ship_postal_code VARCHAR(10),
        ship_country VARCHAR(15),
        FOREIGN KEY (customer_id) REFERENCES customers (customer_id),
        FOREIGN KEY (employee_id) REFERENCES employees (employee_id),
        FOREIGN KEY (ship_via) REFERENCES shippers (shipper_id)
    );""",
    
    """CREATE TABLE order_details (
        order_id INT,
        product_id INT,
        unit_price DECIMAL(10,2) NOT NULL,
        quantity INT NOT NULL,
        discount FLOAT NOT NULL,
        PRIMARY KEY (order_id, product_id),
        FOREIGN KEY (order_id) REFERENCES orders (order_id),
        FOREIGN KEY (product_id) REFERENCES products (product_id)
    );"""
]

# Use NORTHWIND_SCHEMA as the active schema
MOCK_TABLES = NORTHWIND_SCHEMA
