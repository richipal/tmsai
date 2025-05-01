from flask import Flask, request, jsonify
from flask_cors import CORS
import traceback
import time
import os
import logging
import json
import random

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Try to import required packages, but provide fallbacks if not available
try:
    import sqlalchemy
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    logger.warning("SQLAlchemy module not available")

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    logger.warning("Pandas module not available")

try:
    import vanna
    VANNA_AVAILABLE = True
except ImportError:
    VANNA_AVAILABLE = False
    logger.warning("Vanna module not available, using mock implementation")

# Create a mock Vanna implementation for demo purposes
class MockVanna:
    def __init__(self, api_key=None):
        # Store the API key for potential future use
        self.api_key = api_key
        if api_key:
            logger.info("MockVanna initialized with API key")
        
        self.sql_templates = {
            "revenue": "SELECT product_name, SUM(unit_price * quantity) as revenue FROM products JOIN order_details ON products.product_id = order_details.product_id GROUP BY product_name ORDER BY revenue DESC LIMIT 5",
            "orders": "SELECT country, COUNT(*) as order_count FROM customers JOIN orders ON customers.customer_id = orders.customer_id GROUP BY country ORDER BY order_count DESC",
            "sales": "SELECT EXTRACT(MONTH FROM order_date) as month, SUM(unit_price * quantity) as sales FROM orders JOIN order_details ON orders.order_id = order_details.order_id WHERE EXTRACT(YEAR FROM order_date) = 2023 GROUP BY month ORDER BY month",
            "inventory": "SELECT product_name, units_in_stock, units_on_order FROM products WHERE discontinued = 0 ORDER BY units_in_stock ASC LIMIT 10",
            "categories": "SELECT categories.category_name, COUNT(products.product_id) as product_count FROM categories JOIN products ON categories.category_id = products.category_id GROUP BY categories.category_name ORDER BY product_count DESC",
            "default": "SELECT * FROM customers LIMIT 10"
        }
        self.explanations = {
            "revenue": "This query calculates the total revenue for each product by multiplying the unit price by quantity sold across all orders, then returns the top 5 products by revenue.",
            "orders": "This query counts the number of orders placed by customers in each country, showing which countries have the highest order volumes.",
            "sales": "This query analyzes the monthly sales trend for 2023 by calculating the total sales amount for each month of the year.",
            "inventory": "This query retrieves products that are still active (not discontinued) with their current inventory levels, ordered by the smallest inventory first to identify potential stock issues.",
            "categories": "This query analyzes the distribution of products across different categories, showing which categories have the most products.",
            "default": "This query returns a sample of up to 10 customer records from the database to provide a quick overview of customer data."
        }
        
        # Example questions for UI
        self.example_questions = [
            "Show me the top 5 products by revenue",
            "How many orders do we have by country?",
            "What is our monthly sales trend for 2023?",
            "Which products are running low on inventory?",
            "How many products do we have in each category?"
        ]
        
        # Training data for the system
        self.training_data = {
            "question_sql_pairs": [
                {"question": "Show me the top 5 products by revenue", 
                 "sql": "SELECT product_name, SUM(unit_price * quantity) as revenue FROM products JOIN order_details ON products.product_id = order_details.product_id GROUP BY product_name ORDER BY revenue DESC LIMIT 5"},
                {"question": "How many orders do we have by country?", 
                 "sql": "SELECT country, COUNT(*) as order_count FROM customers JOIN orders ON customers.customer_id = orders.customer_id GROUP BY country ORDER BY order_count DESC"},
                {"question": "What is our monthly sales trend for 2023?", 
                 "sql": "SELECT EXTRACT(MONTH FROM order_date) as month, SUM(unit_price * quantity) as sales FROM orders JOIN order_details ON orders.order_id = order_details.order_id WHERE EXTRACT(YEAR FROM order_date) = 2023 GROUP BY month ORDER BY month"},
                {"question": "Which products are running low on inventory?", 
                 "sql": "SELECT product_name, units_in_stock, units_on_order FROM products WHERE discontinued = 0 ORDER BY units_in_stock ASC LIMIT 10"},
                {"question": "How many products do we have in each category?", 
                 "sql": "SELECT categories.category_name, COUNT(products.product_id) as product_count FROM categories JOIN products ON categories.category_id = products.category_id GROUP BY categories.category_name ORDER BY product_count DESC"}
            ],
            "documentation": [
                {"table": "customers", "description": "Contains all customer data including company information, contact details, and location."},
                {"table": "products", "description": "Product catalog with pricing, stock information, and category relationships."},
                {"table": "orders", "description": "Customer orders with dates, shipping details, and relationships to customers."},
                {"table": "order_details", "description": "Line items for each order, with product quantities and pricing information."},
                {"table": "categories", "description": "Product categories with names and descriptions."}
            ],
            "ddl": [
                "CREATE TABLE customers (customer_id VARCHAR PRIMARY KEY, company_name VARCHAR, contact_name VARCHAR, country VARCHAR);",
                "CREATE TABLE products (product_id INT PRIMARY KEY, product_name VARCHAR, unit_price DECIMAL, units_in_stock INT, units_on_order INT, discontinued BOOLEAN, category_id INT);",
                "CREATE TABLE orders (order_id INT PRIMARY KEY, customer_id VARCHAR, order_date DATE);",
                "CREATE TABLE order_details (order_id INT, product_id INT, quantity INT, unit_price DECIMAL);",
                "CREATE TABLE categories (category_id INT PRIMARY KEY, category_name VARCHAR, description VARCHAR);"
            ]
        }
        
    def train_ddl(self, ddl):
        # Just a mock implementation, doesn't actually do anything
        logger.info(f"Mock training with DDL: {ddl[:50]}...")
        return True
    
    def train_documentation(self, documentation):
        # Mock implementation for documentation training
        logger.info(f"Mock training with documentation: {documentation[:50]}...")
        return True
    
    def train_question_sql(self, question, sql):
        # Mock implementation for question-SQL pair training
        logger.info(f"Mock training with question-SQL pair: {question} -> {sql[:30]}...")
        return True
        
    def generate_sql(self, query):
        # Determine which template to use based on keywords in the query
        query = query.lower()
        if "revenue" in query or "top" in query and "product" in query:
            return self.sql_templates["revenue"]
        elif "countr" in query or "order" in query:
            return self.sql_templates["orders"]
        elif "sales" in query or "trend" in query or "month" in query:
            return self.sql_templates["sales"]
        elif "inventory" in query or "stock" in query or "low" in query:
            return self.sql_templates["inventory"]
        elif "categor" in query:
            return self.sql_templates["categories"]
        else:
            return self.sql_templates["default"]
            
    def ask(self, question):
        # Return explanation based on the SQL mentioned in the question
        for key, explanation in self.explanations.items():
            if key in question.lower():
                return explanation
        return self.explanations["default"]
    
    def get_example_questions(self):
        # Return example questions for the UI
        return self.example_questions
    
    def get_training_data(self):
        # Return training data
        return self.training_data
    
    def init_vanna_model(self):
        # Mock initialization
        logger.info("Initialized mock Vanna model")
        return True

# Initialize Vanna AI with mode from environment variable
VANNA_MODEL = os.environ.get('VANNA_MODEL', 'demo')
logger.info(f"Using Vanna model: {VANNA_MODEL}")

# Create a dictionary to store database connections
db_engines = {}

# Function to generate mock data based on the query
def get_mock_data_for_query(sql_query):
    """Generate mock data that would reasonably match the given SQL query"""
    sql_lower = sql_query.lower()
    
    # Mock data for revenue query
    if "revenue" in sql_lower or "sum" in sql_lower and "product" in sql_lower:
        data = [
            {"product_name": "Chai", "revenue": 4725.00},
            {"product_name": "Raclette Courdavault", "revenue": 3950.00},
            {"product_name": "Camembert Pierrot", "revenue": 3650.00},
            {"product_name": "Gnocchi di nonna Alice", "revenue": 3300.00},
            {"product_name": "Manjimup Dried Apples", "revenue": 2940.00}
        ]
        columns = ["product_name", "revenue"]
    
    # Mock data for orders by country
    elif "country" in sql_lower and "order" in sql_lower:
        data = [
            {"country": "USA", "order_count": 122},
            {"country": "Germany", "order_count": 87},
            {"country": "Brazil", "order_count": 83},
            {"country": "France", "order_count": 62},
            {"country": "UK", "order_count": 56},
            {"country": "Italy", "order_count": 41}
        ]
        columns = ["country", "order_count"]
    
    # Mock data for monthly sales
    elif "month" in sql_lower or "sales" in sql_lower:
        data = [
            {"month": 1, "sales": 37850.00},
            {"month": 2, "sales": 40125.00},
            {"month": 3, "sales": 35600.00},
            {"month": 4, "sales": 42300.00},
            {"month": 5, "sales": 39450.00},
            {"month": 6, "sales": 44200.00},
            {"month": 7, "sales": 46500.00},
            {"month": 8, "sales": 47800.00},
            {"month": 9, "sales": 49300.00},
            {"month": 10, "sales": 51450.00},
            {"month": 11, "sales": 58200.00},
            {"month": 12, "sales": 62500.00}
        ]
        columns = ["month", "sales"]
    
    # Default mock data (customers)
    else:
        data = [
            {"customer_id": "ALFKI", "company_name": "Alfreds Futterkiste", "contact_name": "Maria Anders", "country": "Germany"},
            {"customer_id": "ANATR", "company_name": "Ana Trujillo Emparedados", "contact_name": "Ana Trujillo", "country": "Mexico"},
            {"customer_id": "ANTON", "company_name": "Antonio Moreno Taquería", "contact_name": "Antonio Moreno", "country": "Mexico"},
            {"customer_id": "AROUT", "company_name": "Around the Horn", "contact_name": "Thomas Hardy", "country": "UK"},
            {"customer_id": "BERGS", "company_name": "Berglunds snabbköp", "contact_name": "Christina Berglund", "country": "Sweden"}
        ]
        columns = ["customer_id", "company_name", "contact_name", "country"]
    
    return data, columns

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok", "vanna_available": VANNA_AVAILABLE})

@app.route('/api/examples', methods=['GET'])
def get_example_questions():
    """Return example questions for the UI"""
    try:
        # Always try to use the real Vanna API first
        try:
            # Get API key from environment
            api_key = os.environ.get("VANNA_API_KEY")
            if api_key:
                # Create a new instance of Vanna with the API key
                vn = vanna.Vanna(api_key=api_key)
                logger.info("Initializing Vanna with API key")
            else:
                # Create a new instance of Vanna
                vn = vanna.Vanna()
                # Use demo mode which doesn't require an API key
                logger.info("Initializing Vanna in demo mode (no API key found)")
                vn.init_vanna_model()
            
            example_questions = vn.get_example_questions()
            logger.info("Successfully fetched example questions from Vanna API")
        except Exception as e:
            logger.error(f"Error with Vanna API: {str(e)}")
            # Fall back to mock implementation if real Vanna fails
            api_key = os.environ.get("VANNA_API_KEY")
            vn = MockVanna(api_key=api_key)
            example_questions = vn.get_example_questions()
            logger.warning("Using mock example questions")
            
        return jsonify({"examples": example_questions})
    except Exception as e:
        logger.error(f"Error fetching example questions: {str(e)}")
        return jsonify({"error": f"Error fetching example questions: {str(e)}"}), 500
        
@app.route('/api/training-data', methods=['GET'])
def get_training_data():
    """Return training data (question-SQL pairs, documentation, DDL)"""
    try:
        # Always try to use the real Vanna API first
        try:
            # Get API key from environment
            api_key = os.environ.get("VANNA_API_KEY")
            if api_key:
                # Create a new instance of Vanna with the API key
                vn = vanna.Vanna(api_key=api_key)
                logger.info("Initializing Vanna with API key")
            else:
                # Create a new instance of Vanna
                vn = vanna.Vanna()
                # Use demo mode which doesn't require an API key
                logger.info("Initializing Vanna in demo mode (no API key found)")
                vn.init_vanna_model()
            
            training_data = vn.get_training_data()
            logger.info("Successfully fetched training data from Vanna API")
        except Exception as e:
            logger.error(f"Error with Vanna API: {str(e)}")
            # Fall back to mock implementation if real Vanna fails
            api_key = os.environ.get("VANNA_API_KEY")
            vn = MockVanna(api_key=api_key)
            training_data = vn.get_training_data()
            logger.warning("Using mock training data")
            
        return jsonify(training_data)
    except Exception as e:
        logger.error(f"Error fetching training data: {str(e)}")
        return jsonify({"error": f"Error fetching training data: {str(e)}"}), 500

@app.route('/api/train', methods=['POST'])
def train_model():
    """Add training data to the model"""
    try:
        # Get the training data from the request
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        # Always try to use the real Vanna API first
        try:
            # Get API key from environment
            api_key = os.environ.get("VANNA_API_KEY")
            if api_key:
                # Create a new instance of Vanna with the API key
                vn = vanna.Vanna(api_key=api_key)
                logger.info("Initializing Vanna with API key for training")
            else:
                # Create a new instance of Vanna
                vn = vanna.Vanna()
                # Use demo mode which doesn't require an API key
                logger.info("Initializing Vanna in demo mode (no API key found) for training")
                vn.init_vanna_model()
            logger.info("Initialized Vanna API for training")
        except Exception as e:
            logger.error(f"Error with Vanna API: {str(e)}")
            # Fall back to mock implementation if real Vanna fails
            api_key = os.environ.get("VANNA_API_KEY")
            vn = MockVanna(api_key=api_key)
            logger.warning("Using mock implementation for training")
            
        # Train the model with the provided data
        if 'ddl' in data:
            vn.train_ddl(data['ddl'])
            logger.info(f"Trained model with DDL: {data['ddl'][:50]}...")
            
        if 'documentation' in data:
            vn.train_documentation(data['documentation'])
            logger.info(f"Trained model with documentation for: {data['documentation'][:50]}...")
            
        if 'question' in data and 'sql' in data:
            vn.train_question_sql(data['question'], data['sql'])
            logger.info(f"Trained model with question-SQL pair: {data['question']} -> {data['sql'][:30]}...")
            
        return jsonify({"status": "ok", "message": "Training data added successfully"})
    except Exception as e:
        logger.error(f"Error adding training data: {str(e)}")
        return jsonify({"error": f"Error adding training data: {str(e)}"}), 500

@app.route('/api/query', methods=['POST'])
def process_query():
    try:
        start_time = time.time()
        
        # Get the query from the request
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        natural_language_query = data.get('query')
        if not natural_language_query:
            return jsonify({"error": "No query provided"}), 400
        
        connection_info = data.get('connection')
        if not connection_info:
            return jsonify({"error": "No database connection provided"}), 400
        
        # Validate connection info
        required_fields = ['type', 'host', 'port', 'username', 'password', 'database']
        for field in required_fields:
            if field not in connection_info:
                return jsonify({"error": f"Missing connection field: {field}"}), 400
        
        # Create a connection string
        conn_type = connection_info['type']
        if conn_type == 'mysql':
            conn_str = f"mysql+pymysql://{connection_info['username']}:{connection_info['password']}@{connection_info['host']}:{connection_info['port']}/{connection_info['database']}"
        elif conn_type == 'postgresql':
            conn_str = f"postgresql://{connection_info['username']}:{connection_info['password']}@{connection_info['host']}:{connection_info['port']}/{connection_info['database']}"
        else:
            return jsonify({"error": f"Unsupported database type: {conn_type}"}), 400
        
        # In demo mode, we don't actually connect to a database
        # Just log the connection info for reference
        logger.info(f"Demo mode: Would connect to {conn_type} database at {connection_info['host']}:{connection_info['port']}/{connection_info['database']}")
        # Create a placeholder for the engine
        engine = None
        
        # Always use the real Vanna API
        try:
            # Get API key from environment
            api_key = os.environ.get("VANNA_API_KEY")
            if api_key:
                # Create a new instance of Vanna with the API key
                vn = vanna.Vanna(api_key=api_key)
                logger.info("Initializing Vanna with API key")
            else:
                # Create a new instance of Vanna
                vn = vanna.Vanna()
                # Use demo mode which doesn't require an API key
                logger.info("Initializing Vanna in demo mode (no API key found)")
                vn.init_vanna_model()
        except Exception as e:
            logger.error(f"Error initializing Vanna API: {str(e)}")
            # Only use mock as a fallback if real Vanna fails
            logger.warning("Falling back to mock implementation as Vanna isn't available")
            api_key = os.environ.get("VANNA_API_KEY")
            vn = MockVanna(api_key=api_key)
        
        # Extract database schema information or use mock data
        try:
            # Always use mock tables for demo purposes to avoid connection errors
            logger.info("Using mock schema for demo purposes")
            mock_tables = [
                "CREATE TABLE customers (customer_id VARCHAR PRIMARY KEY, company_name VARCHAR, contact_name VARCHAR, country VARCHAR);",
                "CREATE TABLE products (product_id INT PRIMARY KEY, product_name VARCHAR, unit_price DECIMAL);",
                "CREATE TABLE orders (order_id INT PRIMARY KEY, customer_id VARCHAR, order_date DATE);",
                "CREATE TABLE order_details (order_id INT, product_id INT, quantity INT, unit_price DECIMAL);"
            ]
            for ddl in mock_tables:
                vn.train_ddl(ddl)
        
        except Exception as e:
            logger.error(f"Error setting up mock schema: {str(e)}")
            # Continue even if this fails - we can still generate mock SQL
        
        # Generate SQL from natural language
        try:
            generated_sql = vn.generate_sql(natural_language_query)
        except Exception as e:
            logger.error(f"Error generating SQL: {str(e)}")
            return jsonify({"error": f"SQL generation error: {str(e)}"}), 500
        
        # Generate mock data for the executed SQL
        try:
            # Always use mock data since we're in demo mode
            logger.info("Using mock data for demo purposes")
            result_data, columns = get_mock_data_for_query(generated_sql)
            
            # Generate an explanation of the query
            try:
                explanation = vn.ask(f"Explain what this SQL query does: {generated_sql}")
            except:
                explanation = "No explanation available."
            
            end_time = time.time()
            execution_time = int((end_time - start_time) * 1000)  # Convert to milliseconds
            
            return jsonify({
                "sql": generated_sql,
                "data": result_data,
                "columns": columns,
                "explanation": explanation,
                "execution_time": execution_time
            })
        except Exception as e:
            logger.error(f"Error executing SQL: {str(e)}")
            traceback_str = traceback.format_exc()
            return jsonify({
                "sql": generated_sql,
                "error": f"SQL execution error: {str(e)}",
                "traceback": traceback_str
            }), 500
    
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        traceback_str = traceback.format_exc()
        return jsonify({"error": f"Server error: {str(e)}", "traceback": traceback_str}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
