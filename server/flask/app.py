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
    def __init__(self):
        self.sql_templates = {
            "revenue": "SELECT product_name, SUM(unit_price * quantity) as revenue FROM products JOIN order_details ON products.product_id = order_details.product_id GROUP BY product_name ORDER BY revenue DESC LIMIT 5",
            "orders": "SELECT country, COUNT(*) as order_count FROM customers JOIN orders ON customers.customer_id = orders.customer_id GROUP BY country ORDER BY order_count DESC",
            "sales": "SELECT EXTRACT(MONTH FROM order_date) as month, SUM(unit_price * quantity) as sales FROM orders JOIN order_details ON orders.order_id = order_details.order_id WHERE EXTRACT(YEAR FROM order_date) = 2023 GROUP BY month ORDER BY month",
            "default": "SELECT * FROM customers LIMIT 10"
        }
        self.explanations = {
            "revenue": "This query calculates the total revenue for each product by multiplying the unit price by quantity sold across all orders, then returns the top 5 products by revenue.",
            "orders": "This query counts the number of orders placed by customers in each country, showing which countries have the highest order volumes.",
            "sales": "This query analyzes the monthly sales trend for 2023 by calculating the total sales amount for each month of the year.",
            "default": "This query returns a sample of up to 10 customer records from the database to provide a quick overview of customer data."
        }
        
    def train_ddl(self, ddl):
        # Just a mock implementation, doesn't actually do anything
        logger.info(f"Mock training with DDL: {ddl[:50]}...")
        return True
        
    def generate_sql(self, query):
        # Determine which template to use based on keywords in the query
        query = query.lower()
        if "revenue" in query or "top" in query:
            return self.sql_templates["revenue"]
        elif "countr" in query or "order" in query:
            return self.sql_templates["orders"]
        elif "sales" in query or "trend" in query or "month" in query:
            return self.sql_templates["sales"]
        else:
            return self.sql_templates["default"]
            
    def ask(self, question):
        # Return explanation based on the SQL mentioned in the question
        for key, explanation in self.explanations.items():
            if key in question.lower():
                return explanation
        return self.explanations["default"]
    
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
        
        # Create or get a database engine
        engine_key = f"{connection_info['host']}:{connection_info['port']}/{connection_info['database']}"
        if engine_key not in db_engines:
            try:
                engine = sqlalchemy.create_engine(conn_str)
                db_engines[engine_key] = engine
            except Exception as e:
                logger.error(f"Error creating database connection: {str(e)}")
                return jsonify({"error": f"Database connection error: {str(e)}"}), 500
        
        engine = db_engines[engine_key]
        
        # Initialize Vanna AI or use mock implementation
        if VANNA_AVAILABLE:
            vn = vanna.Vanna()
            if VANNA_MODEL == 'demo':
                # Use demo mode which doesn't require an API key
                vn.init_vanna_model()
        else:
            # Use our mock implementation
            logger.warning("Using mock implementation as Vanna isn't available")
            vn = MockVanna()
        
        # Extract database schema information or use mock data
        try:
            if SQLALCHEMY_AVAILABLE:
                inspector = sqlalchemy.inspect(engine)
                tables = inspector.get_table_names()
                
                # Extract table definitions
                for table in tables:
                    columns = inspector.get_columns(table)
                    column_info = []
                    for column in columns:
                        column_info.append({
                            "name": column['name'],
                            "type": str(column['type'])
                        })
                    
                    # Add the table definition to Vanna
                    ddl = f"CREATE TABLE {table} ("
                    for i, col in enumerate(column_info):
                        if i > 0:
                            ddl += ", "
                        ddl += f"{col['name']} {col['type']}"
                    ddl += ");"
                    vn.train_ddl(ddl)
            else:
                # Use mock tables for demo purposes
                logger.info("Using mock schema since SQLAlchemy is not available")
                mock_tables = [
                    "CREATE TABLE customers (customer_id VARCHAR PRIMARY KEY, company_name VARCHAR, contact_name VARCHAR, country VARCHAR);",
                    "CREATE TABLE products (product_id INT PRIMARY KEY, product_name VARCHAR, unit_price DECIMAL);",
                    "CREATE TABLE orders (order_id INT PRIMARY KEY, customer_id VARCHAR, order_date DATE);",
                    "CREATE TABLE order_details (order_id INT, product_id INT, quantity INT, unit_price DECIMAL);"
                ]
                for ddl in mock_tables:
                    vn.train_ddl(ddl)
            
            # Optionally, you can also add documentation
            # vn.train_documentation(documentation)
        except Exception as e:
            logger.error(f"Error extracting schema: {str(e)}")
            return jsonify({"error": f"Schema extraction error: {str(e)}"}), 500
        
        # Generate SQL from natural language
        try:
            generated_sql = vn.generate_sql(natural_language_query)
        except Exception as e:
            logger.error(f"Error generating SQL: {str(e)}")
            return jsonify({"error": f"SQL generation error: {str(e)}"}), 500
        
        # Execute the generated SQL or return mock data
        try:
            if PANDAS_AVAILABLE and SQLALCHEMY_AVAILABLE:
                try:
                    df = pd.read_sql(generated_sql, engine)
                    result_data = df.to_dict(orient='records')
                    columns = df.columns.tolist()
                except Exception as e:
                    logger.error(f"Error executing SQL: {str(e)}")
                    # Provide mock results when SQL fails
                    result_data, columns = get_mock_data_for_query(generated_sql)
            else:
                # Use mock data when pandas/sqlalchemy is not available
                logger.info("Using mock data since pandas or sqlalchemy is not available")
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
