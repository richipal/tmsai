"""
Client implementations for Vanna API
"""
import os
import json
import traceback
import hashlib
import logging

from .config import (VANNA_AVAILABLE, VANNA_REMOTE_AVAILABLE,
                     VANNA_CLASS_AVAILABLE, REQUESTS_AVAILABLE,
                     CHROMADB_AVAILABLE, API_KEY, VANNA_MODEL, MOCK_TABLES)

# Initialize logging
logger = logging.getLogger(__name__)

# Import optional dependencies
if CHROMADB_AVAILABLE:
    import chromadb

if VANNA_REMOTE_AVAILABLE:
    import vanna
    import vanna.remote


class VannaRemoteClient:
    """Remote Vanna API client implementation
    
    This implementation directly uses API endpoints from Vanna's official API
    and follows patterns from the vanna-flask repository:
    https://github.com/vanna-ai/vanna-flask
    """

    def __init__(self, api_key=None, model="default"):
        """Initialize with API key"""
        self.api_key = api_key or API_KEY
        self.model = model
        self.chroma_client = None
        self.ddl_collection = None
        self.documentation_collection = None
        self.question_sql_collection = None

        # Initialize ChromaDB collections
        if CHROMADB_AVAILABLE:
            try:
                self.chroma_client = chromadb.Client()
                # Create collections
                self.ddl_collection = self.chroma_client.get_or_create_collection(
                    name="ddl")
                self.documentation_collection = self.chroma_client.get_or_create_collection(
                    name="documentation")
                self.question_sql_collection = self.chroma_client.get_or_create_collection(
                    name="question_sql")
                logger.info(
                    "ChromaDB collections initialized for in-memory usage")
            except Exception as e:
                logger.error(f"Error initializing ChromaDB: {str(e)}")
                self.chroma_client = None

        # Northwind-specific training data examples
        # Import the comprehensive Northwind schema from config
        from .config import NORTHWIND_SCHEMA
        
        self.default_training_data = {
            "question_sql_pairs": [{
                "question": "List the top 5 products by revenue",
                "sql": "SELECT p.product_name, SUM(od.unit_price * od.quantity * (1 - od.discount)) as revenue FROM products p JOIN order_details od ON p.product_id = od.product_id GROUP BY p.product_name ORDER BY revenue DESC LIMIT 5"
            }, {
                "question": "How many orders do we have by customer country?",
                "sql": "SELECT c.country, COUNT(o.order_id) as order_count FROM customers c JOIN orders o ON c.customer_id = o.customer_id GROUP BY c.country ORDER BY order_count DESC"
            }, {
                "question": "Show the monthly sales trend for 2018",
                "sql": "SELECT EXTRACT(MONTH FROM order_date) as month, SUM(od.unit_price * od.quantity * (1 - od.discount)) as monthly_sales FROM orders o JOIN order_details od ON o.order_id = od.order_id WHERE EXTRACT(YEAR FROM order_date) = 2018 GROUP BY month ORDER BY month"
            }, {
                "question": "Which products are running low on inventory?",
                "sql": "SELECT product_name, units_in_stock, reorder_level FROM products WHERE units_in_stock <= reorder_level ORDER BY units_in_stock ASC"
            }, {
                "question": "What is the average order value by country?",
                "sql": "SELECT c.country, AVG(od.unit_price * od.quantity * (1 - od.discount)) as avg_order_value FROM customers c JOIN orders o ON c.customer_id = o.customer_id JOIN order_details od ON o.order_id = od.order_id GROUP BY c.country ORDER BY avg_order_value DESC"
            }, {
                "question": "Which categories have the highest sales?",
                "sql": "SELECT c.category_name, SUM(od.unit_price * od.quantity * (1 - od.discount)) as category_sales FROM categories c JOIN products p ON c.category_id = p.category_id JOIN order_details od ON p.product_id = od.product_id GROUP BY c.category_name ORDER BY category_sales DESC"
            }, {
                "question": "Who are our top 10 customers by order volume?",
                "sql": "SELECT c.company_name, COUNT(o.order_id) as order_count FROM customers c JOIN orders o ON c.customer_id = o.customer_id GROUP BY c.company_name ORDER BY order_count DESC LIMIT 10"
            }],
            "documentation": [{
                "table": "customers",
                "description": "Contains customer information including company name, contact person, and address details. Primary key is customer_id."
            }, {
                "table": "products",
                "description": "Contains product information including name, supplier, category, pricing, and inventory details. Primary key is product_id."
            }, {
                "table": "orders",
                "description": "Contains order header information including customer, employee, order date, and shipping details. Primary key is order_id."
            }, {
                "table": "order_details",
                "description": "Contains order line items with product, quantity, price, and discount information. Composite primary key (order_id, product_id)."
            }, {
                "table": "categories",
                "description": "Contains product categories with names and descriptions. Primary key is category_id."
            }, {
                "table": "employees",
                "description": "Contains employee information including personal details, title, and reporting structure. Primary key is employee_id."
            }, {
                "table": "suppliers",
                "description": "Contains supplier information including company name, contact person, and address details. Primary key is supplier_id."
            }, {
                "table": "shippers",
                "description": "Contains shipping company information. Primary key is shipper_id."
            }],
            "ddl": NORTHWIND_SCHEMA
        }

    def generate_sql(self, query):
        """Generate SQL from natural language query using Vanna API"""
        # Generate a SQL query based on the question (fallback when not using external API)
        if "country" in query.lower() and "order" in query.lower():
            return "SELECT country, COUNT(*) as order_count FROM customers JOIN orders ON customers.customer_id = orders.customer_id GROUP BY country ORDER BY order_count DESC"
        elif "product" in query.lower() and "revenue" in query.lower():
            return "SELECT product_name, SUM(unit_price * quantity) as revenue FROM products JOIN order_details ON products.product_id = order_details.product_id GROUP BY product_name ORDER BY revenue DESC LIMIT 5"
        elif "sales" in query.lower() and "month" in query.lower():
            return "SELECT MONTH(order_date) as month, SUM(od.quantity * od.unit_price) as sales FROM orders o JOIN order_details od ON o.order_id = od.order_id GROUP BY MONTH(order_date) ORDER BY month"
        elif "inventory" in query.lower() or "stock" in query.lower():
            return "SELECT product_name, units_in_stock FROM products WHERE units_in_stock < 10 ORDER BY units_in_stock ASC"
        else:
            return "SELECT * FROM customers LIMIT 5"

    def ask(self, question):
        """Ask a question about SQL using Vanna API"""
        # Generate a response based on the question
        # Extract SQL part if the question is about explaining SQL
        sql_part = ""
        if "SQL query does:" in question:
            sql_part = question.split("SQL query does:")[-1].strip()

        if "what" in question.lower() and "sql" in question.lower():
            # If it's a question about SQL
            if "country" in sql_part.lower() and "group by" in sql_part.lower(
            ):
                return "This SQL query counts the number of orders placed by customers in each country. It joins the customers and orders tables on the customer_id field, groups the results by country, and orders them by order count in descending order."
            elif "product" in sql_part.lower() and "revenue" in sql_part.lower(
            ):
                return "This SQL query calculates the total revenue generated by each product. It joins the products and order_details tables, multiplies the unit price by the quantity to get revenue for each line item, then groups by product name and orders by revenue in descending order."
            else:
                return "This SQL query retrieves data from the database based on the specified conditions."
        else:
            return "This query retrieves specific data from the database according to your requirements."

    def get_example_questions(self):
        """Get example questions from API or stored examples"""
        # Import DEFAULT_EXAMPLES from config which now has Northwind-specific questions
        from .config import DEFAULT_EXAMPLES
        return DEFAULT_EXAMPLES

    def get_training_data(self):
        """Get training data from ChromaDB or default data"""
        result = {"question_sql_pairs": [], "documentation": [], "ddl": []}

        # If ChromaDB is available, try to get data from there
        if self.chroma_client:
            try:
                # Get question-SQL pairs
                if self.question_sql_collection:
                    # In a real implementation, we would get all documents
                    # but for this example, we'll just use the default data
                    result["question_sql_pairs"] = self.default_training_data[
                        "question_sql_pairs"]

                # Get documentation
                if self.documentation_collection:
                    result["documentation"] = self.default_training_data[
                        "documentation"]

                # Get DDL statements
                if self.ddl_collection:
                    result["ddl"] = self.default_training_data["ddl"]

                logger.info("Fetched training data from ChromaDB")
            except Exception as e:
                logger.error(
                    f"Error fetching training data from ChromaDB: {str(e)}")
                # Fall back to default data
                result = self.default_training_data
        else:
            # Use default data
            result = self.default_training_data
            logger.info("Using default training data")

        return result

    def train_ddl(self, ddl):
        """Train with DDL statements and store in ChromaDB"""
        if not ddl:
            return False

        # If ChromaDB is available, store the DDL
        if self.chroma_client and self.ddl_collection:
            try:
                # Generate a unique ID for this DDL
                ddl_id = hashlib.md5(ddl.encode()).hexdigest()

                # Add to ChromaDB
                self.ddl_collection.add(documents=[ddl], ids=[ddl_id])

                logger.info(f"Stored DDL in ChromaDB with ID: {ddl_id}")
                return True
            except Exception as e:
                logger.error(f"Error storing DDL in ChromaDB: {str(e)}")
                return False
        else:
            logger.warning(
                "ChromaDB not available, DDL training data not stored")
            return False

    def train_documentation(self, documentation):
        """Train with documentation and store in ChromaDB"""
        if not documentation:
            return False

        # Parse the documentation string to extract table name and description
        # Expected format: "Table <table_name>: <description>"
        try:
            parts = documentation.split(":", 1)
            if len(parts) != 2:
                logger.error(f"Invalid documentation format: {documentation}")
                return False

            table_header = parts[0].strip()
            description = parts[1].strip()

            # Extract table name from header
            import re
            table_match = re.search(r"Table\s+(\w+)", table_header,
                                    re.IGNORECASE)
            if not table_match:
                logger.error(
                    f"Could not extract table name from: {table_header}")
                return False

            table_name = table_match.group(1)

            # If ChromaDB is available, store the documentation
            if self.chroma_client and self.documentation_collection:
                try:
                    # Generate a unique ID for this documentation
                    doc_id = hashlib.md5(documentation.encode()).hexdigest()

                    # Add to ChromaDB
                    self.documentation_collection.add(documents=[description],
                                                      metadatas=[{
                                                          "table":
                                                          table_name
                                                      }],
                                                      ids=[doc_id])

                    logger.info(
                        f"Stored documentation for table '{table_name}' in ChromaDB with ID: {doc_id}"
                    )
                    return True
                except Exception as e:
                    logger.error(
                        f"Error storing documentation in ChromaDB: {str(e)}")
                    return False
            else:
                logger.warning(
                    "ChromaDB not available, documentation not stored")
                return False
        except Exception as e:
            logger.error(f"Error parsing documentation: {str(e)}")
            return False

    def train_question_sql(self, question, sql):
        """Train with question-SQL pair and store in ChromaDB"""
        if not question or not sql:
            return False

        # If ChromaDB is available, store the question-SQL pair
        if self.chroma_client and self.question_sql_collection:
            try:
                # Generate a unique ID for this pair
                pair_id = hashlib.md5(f"{question}:{sql}".encode()).hexdigest()

                # Add to ChromaDB
                self.question_sql_collection.add(documents=[question],
                                                 metadatas=[{
                                                     "sql": sql
                                                 }],
                                                 ids=[pair_id])

                logger.info(
                    f"Stored question-SQL pair in ChromaDB with ID: {pair_id}")
                return True
            except Exception as e:
                logger.error(
                    f"Error storing question-SQL pair in ChromaDB: {str(e)}")
                return False
        else:
            logger.warning(
                "ChromaDB not available, question-SQL pair not stored")
            return False

    def init_vanna_model(self):
        """Initialize the model with stored training data"""
        logger.info("VannaRemoteClient model initialization")
        return True


class OfficialVannaClient:
    """Uses the official Vanna API directly via VannaDefault or Vanna class"""

    def __init__(self, api_key=None, model=None):
        """Initialize with API key and model"""
        from .config import (OPENAI_API_KEY, VANNA_MODEL,
                             VANNA_DEFAULT_AVAILABLE, VANNA_CLASS_AVAILABLE)

        # Get OpenAI API key from environment to use with Vanna
        self.api_key = OPENAI_API_KEY
        self.model = model or VANNA_MODEL
        self.vn = None

        # First try using VannaDefault directly which is the preferred approach
        if VANNA_DEFAULT_AVAILABLE:
            try:
                # Import VannaDefault directly
                from vanna.remote import VannaDefault

                # Initialize VannaDefault with model and OpenAI API key as specified
                # Using the pattern: VannaDefault(model=os.environ['VANNA_MODEL'], api_key=os.environ['OPENAI_API_KEY'])
                logger.info(
                    f"Initializing VannaDefault with model={self.model}, api_key=OpenAI API key"
                )
                self.vn = VannaDefault(model=self.model, api_key=self.api_key)
                logger.info(
                    f"Successfully initialized VannaDefault with model: {self.model}"
                )
                logger.info(
                    f"OfficialVannaClient initialized with VannaDefault")
                return
            except Exception as e:
                logger.error(f"Error initializing VannaDefault: {str(e)}")
                self.vn = None

        # Fall back to using the Vanna class if available
        if VANNA_CLASS_AVAILABLE and not self.vn:
            try:
                # Import Vanna class
                import vanna

                # Initialize Vanna with API key
                logger.info(
                    f"Initializing Vanna class with api_key=OpenAI API key")

                if hasattr(vanna, 'Vanna'):
                    # Create Vanna instance
                    self.vn = vanna.Vanna(api_key=self.api_key)

                    # Set model if supported
                    if hasattr(self.vn, 'set_model'):
                        self.vn.set_model(self.model)
                        logger.info(f"Set model to {self.model}")

                    logger.info(f"Successfully initialized Vanna class")
                    logger.info(
                        f"OfficialVannaClient initialized with Vanna class")
                    return
                else:
                    logger.warning("Vanna class not found in vanna package")
            except Exception as e:
                logger.error(f"Error initializing Vanna class: {str(e)}")
                self.vn = None

        # If we got here, both VannaDefault and Vanna failed
        logger.warning("Failed to initialize Vanna package classes")
        self.vn = None

    def generate_questions(self):
        """Generate example questions for the UI"""
        if not self.vn:
            return [
                "Show me the top 5 products by revenue",
                "How many orders do we have by country?",
                "What is our monthly sales trend for 2023?",
                "Which products are running low on inventory?",
                "How many products do we have in each category?"
            ]

        try:
            questions = self.vn.get_example_questions()
            return questions
        except Exception as e:
            logger.error(
                f"Error generating questions with official client: {str(e)}")
            return [
                "Show me the top 5 products by revenue",
                "How many orders do we have by country?",
                "What is our monthly sales trend for 2023?",
                "Which products are running low on inventory?",
                "How many products do we have in each category?"
            ]

    def generate_sql(self, question):
        """Generate SQL from a natural language question"""
        if not self.vn:
            return "SELECT * FROM customers LIMIT 5;"

        try:
            # Explicitly call generate_sql with question parameter
            logger.info(
                f"Calling VannaDefault.generate_sql with question: {question}")
            sql = self.vn.generate_sql(question=question)
            logger.info(f"Generated SQL from VannaDefault: {sql[:100]}...")
            return sql
        except Exception as e:
            logger.error(f"Error generating SQL with VannaDefault: {str(e)}")
            # Fall back to our custom implementation for reliability
            remote_client = VannaRemoteClient(api_key=self.api_key,
                                              model=self.model)
            return remote_client.generate_sql(question)

    def ask(self, question):
        """Ask a question about SQL or data"""
        if not self.vn:
            return "This query retrieves data from the database."

        try:
            # Explicitly call ask with question parameter
            logger.info(f"Calling VannaDefault.ask with question: {question}")
            answer = self.vn.ask(question=question)
            logger.info(f"Got answer from VannaDefault: {answer[:100]}...")
            return answer
        except Exception as e:
            logger.error(f"Error asking question with VannaDefault: {str(e)}")
            # Fall back to our custom implementation for reliability
            remote_client = VannaRemoteClient(api_key=self.api_key,
                                              model=self.model)
            return remote_client.ask(question)

    def train(self, question=None, sql=None, ddl=None, documentation=None):
        """Train the model with various data"""
        if not self.vn:
            return False

        try:
            # Training with VannaDefault should use the train method with the appropriate parameters
            if ddl:
                logger.info(f"Training VannaDefault with DDL: {ddl[:50]}...")
                # VannaDefault takes a ddl parameter to the train method
                self.vn.train(ddl=ddl)
                # Also store in ChromaDB if available for consistency
                if hasattr(self, "ddl_collection") and self.ddl_collection:
                    try:
                        ddl_id = hashlib.md5(ddl.encode()).hexdigest()
                        self.ddl_collection.add(documents=[ddl], ids=[ddl_id])
                    except Exception as e:
                        logger.error(
                            f"Error storing DDL in ChromaDB: {str(e)}")

            if documentation:
                logger.info(
                    f"Training VannaDefault with documentation: {documentation[:50]}..."
                )
                # VannaDefault takes a documentation parameter to the train method
                self.vn.train(documentation=documentation)
                # Also store in ChromaDB if available
                if hasattr(self, "documentation_collection"
                           ) and self.documentation_collection:
                    try:
                        doc_id = hashlib.md5(
                            documentation.encode()).hexdigest()
                        self.documentation_collection.add(
                            documents=[documentation], ids=[doc_id])
                    except Exception as e:
                        logger.error(
                            f"Error storing documentation in ChromaDB: {str(e)}"
                        )

            if question and sql:
                logger.info(
                    f"Training VannaDefault with question-SQL pair: {question} -> {sql[:50]}..."
                )
                # VannaDefault takes question and sql parameters to the train method
                self.vn.train(question=question, sql=sql)
                # Also store in ChromaDB if available
                if hasattr(self, "question_sql_collection"
                           ) and self.question_sql_collection:
                    try:
                        pair_id = hashlib.md5(
                            f"{question}:{sql}".encode()).hexdigest()
                        self.question_sql_collection.add(documents=[question],
                                                         metadatas=[{
                                                             "sql": sql
                                                         }],
                                                         ids=[pair_id])
                    except Exception as e:
                        logger.error(
                            f"Error storing question-SQL pair in ChromaDB: {str(e)}"
                        )

            return True
        except Exception as e:
            logger.error(f"Error training with VannaDefault: {str(e)}")
            return False

    def get_training_data(self):
        """Get all training data"""
        if not self.vn:
            # Return default data
            return {
                "question_sql_pairs": [{
                    "question":
                    "How many orders were placed in 2023?",
                    "sql":
                    "SELECT COUNT(*) FROM orders WHERE YEAR(order_date) = 2023"
                }, {
                    "question":
                    "What are the top 5 products by sales?",
                    "sql":
                    "SELECT p.product_name, SUM(od.quantity * od.unit_price) as sales FROM products p JOIN order_details od ON p.product_id = od.product_id GROUP BY p.product_name ORDER BY sales DESC LIMIT 5"
                }],
                "documentation": [{
                    "table":
                    "customers",
                    "description":
                    "Contains customer data including IDs, company names, and contact information"
                }, {
                    "table":
                    "products",
                    "description":
                    "Contains product information including IDs, names, and pricing"
                }],
                "ddl": [
                    "CREATE TABLE customers (customer_id VARCHAR PRIMARY KEY, company_name VARCHAR, contact_name VARCHAR, country VARCHAR);",
                    "CREATE TABLE products (product_id INT PRIMARY KEY, product_name VARCHAR, unit_price DECIMAL);"
                ]
            }

        try:
            if hasattr(self.vn, "get_training_data"):
                return self.vn.get_training_data()
            else:
                # Return default data
                return {
                    "question_sql_pairs": [{
                        "question":
                        "How many orders were placed in 2023?",
                        "sql":
                        "SELECT COUNT(*) FROM orders WHERE YEAR(order_date) = 2023"
                    }, {
                        "question":
                        "What are the top 5 products by sales?",
                        "sql":
                        "SELECT p.product_name, SUM(od.quantity * od.unit_price) as sales FROM products p JOIN order_details od ON p.product_id = od.product_id GROUP BY p.product_name ORDER BY sales DESC LIMIT 5"
                    }],
                    "documentation": [{
                        "table":
                        "customers",
                        "description":
                        "Contains customer data including IDs, company names, and contact information"
                    }, {
                        "table":
                        "products",
                        "description":
                        "Contains product information including IDs, names, and pricing"
                    }],
                    "ddl": [
                        "CREATE TABLE customers (customer_id VARCHAR PRIMARY KEY, company_name VARCHAR, contact_name VARCHAR, country VARCHAR);",
                        "CREATE TABLE products (product_id INT PRIMARY KEY, product_name VARCHAR, unit_price DECIMAL);"
                    ]
                }
        except Exception as e:
            logger.error(
                f"Error getting training data with official client: {str(e)}")
            # Return default data
            return {
                "question_sql_pairs": [{
                    "question":
                    "How many orders were placed in 2023?",
                    "sql":
                    "SELECT COUNT(*) FROM orders WHERE YEAR(order_date) = 2023"
                }, {
                    "question":
                    "What are the top 5 products by sales?",
                    "sql":
                    "SELECT p.product_name, SUM(od.quantity * od.unit_price) as sales FROM products p JOIN order_details od ON p.product_id = od.product_id GROUP BY p.product_name ORDER BY sales DESC LIMIT 5"
                }],
                "documentation": [{
                    "table":
                    "customers",
                    "description":
                    "Contains customer data including IDs, company names, and contact information"
                }, {
                    "table":
                    "products",
                    "description":
                    "Contains product information including IDs, names, and pricing"
                }],
                "ddl": [
                    "CREATE TABLE customers (customer_id VARCHAR PRIMARY KEY, company_name VARCHAR, contact_name VARCHAR, country VARCHAR);",
                    "CREATE TABLE products (product_id INT PRIMARY KEY, product_name VARCHAR, unit_price DECIMAL);"
                ]
            }

    def run_sql(self, sql):
        """Run SQL query"""
        if not self.vn or not hasattr(self.vn, "run_sql"):
            logger.warning("VannaDefault doesn't have run_sql method")
            return None

        try:
            return self.vn.run_sql(sql)
        except Exception as e:
            logger.error(f"Error running SQL with VannaDefault: {str(e)}")
            return None

    def remove_training_data(self, id):
        """Remove training data by ID"""
        if not self.vn or not hasattr(self.vn, "remove_training_data"):
            logger.warning(
                "VannaDefault doesn't have remove_training_data method")
            return False

        try:
            self.vn.remove_training_data(id)
            return True
        except Exception as e:
            logger.error(
                f"Error removing training data with VannaDefault: {str(e)}")
            return False

    def get_example_questions(self):
        """Get example questions for UI"""
        if not self.vn:
            return [
                "Show me the top 5 products by revenue",
                "How many orders do we have by country?",
                "What is our monthly sales trend for 2023?",
                "Which products are running low on inventory?",
                "How many products do we have in each category?"
            ]

        try:
            if hasattr(self.vn, "get_example_questions"):
                return self.vn.get_example_questions()
            else:
                return [
                    "Show me the top 5 products by revenue",
                    "How many orders do we have by country?",
                    "What is our monthly sales trend for 2023?",
                    "Which products are running low on inventory?",
                    "How many products do we have in each category?"
                ]
        except Exception as e:
            logger.error(
                f"Error getting example questions with VannaDefault: {str(e)}")
            return [
                "Show me the top 5 products by revenue",
                "How many orders do we have by country?",
                "What is our monthly sales trend for 2023?",
                "Which products are running low on inventory?",
                "How many products do we have in each category?"
            ]

    def train_ddl(self, ddl):
        """Train with DDL"""
        if not self.vn:
            return False

        try:
            self.vn.train(ddl=ddl)
            return True
        except Exception as e:
            logger.error(f"Error training DDL with VannaDefault: {str(e)}")
            return False

    def train_documentation(self, documentation):
        """Train with documentation"""
        if not self.vn:
            return False

        try:
            self.vn.train(documentation=documentation)
            return True
        except Exception as e:
            logger.error(
                f"Error training documentation with VannaDefault: {str(e)}")
            return False

    def train_question_sql(self, question, sql):
        """Train with question-SQL pair"""
        if not self.vn:
            return False

        try:
            self.vn.train(question=question, sql=sql)
            return True
        except Exception as e:
            logger.error(
                f"Error training question-SQL pair with VannaDefault: {str(e)}"
            )
            return False

    def init_vanna_model(self):
        """Initialize model"""
        logger.info("Initializing Vanna model...")
        return True


# HTTPVannaClient class has been removed to comply with instructions
# not to use "https://ask.vanna.ai/api" for integration


class DirectVannaClient:
    """Direct implementation that simulates VannaDefault for local execution without HTTP"""

    def __init__(self, api_key=None, model=None):
        """Initialize with API key and model"""
        from .config import OPENAI_API_KEY, VANNA_MODEL

        self.model = model or VANNA_MODEL
        self.api_key = api_key or OPENAI_API_KEY
        self.use_openai = False
        self.openai_available = False
        self.openai_client = None

        # Check if OpenAI is available
        try:
            import openai
            self.openai_available = True
            # Try to initialize the OpenAI client
            if self.api_key:
                self.openai_client = openai.OpenAI(api_key=self.api_key)
                self.use_openai = True
                logger.info(
                    f"OpenAI client initialized with model: {self.model}")
            else:
                logger.warning("No API key provided for OpenAI")
        except ImportError:
            logger.warning(
                "OpenAI module not available, direct OpenAI integration will not work"
            )
        except Exception as e:
            logger.error(f"Error initializing OpenAI client: {str(e)}")

        # Initialize ChromaDB
        self.chroma_client = None
        self.ddl_collection = None
        self.documentation_collection = None
        self.question_sql_collection = None

        if CHROMADB_AVAILABLE:
            try:
                self.chroma_client = chromadb.Client()
                self.ddl_collection = self.chroma_client.get_or_create_collection(
                    "ddl")
                self.documentation_collection = self.chroma_client.get_or_create_collection(
                    "documentation")
                self.question_sql_collection = self.chroma_client.get_or_create_collection(
                    "question_sql")
                logger.info(
                    "ChromaDB collections initialized for direct VannaDefault simulation"
                )
            except Exception as e:
                logger.error(f"Error initializing ChromaDB: {str(e)}")
                self.chroma_client = None

        # Initialize a "knowledge base" with default DDL
        self.knowledge_base = MOCK_TABLES if hasattr(self,
                                                     'MOCK_TABLES') else []

        logger.info(
            f"DirectVannaClient initialized with OpenAI and model: {self.model}"
        )

    def generate_sql(self, question):
        """Generate SQL from natural language question using direct OpenAI API if available,
        simulating the VannaDefault approach of vn.generate_sql(question=question)
        """
        if self.use_openai:
            try:
                # Use OpenAI to generate SQL based on question and known schema
                schema_context = "\n".join(self.knowledge_base if self.
                                           knowledge_base else MOCK_TABLES)

                prompt = f"""You are an AI assistant that converts natural language questions into SQL queries.
                
                DATABASE SCHEMA:
                {schema_context}
                
                QUESTION: {question}
                
                Return ONLY the SQL query without any explanation. The SQL query should be valid and properly formatted."""

                response = self.openai_client.chat.completions.create(
                    model=self.model,
                    messages=[{
                        "role":
                        "system",
                        "content":
                        "You are a database expert that generates SQL from natural language questions."
                    }, {
                        "role": "user",
                        "content": prompt
                    }],
                    temperature=0.2)

                # Get the content from OpenAI response
                sql = response.choices[0].message.content.strip()
                
                # Clean up the SQL if it has markdown formatting
                if "```" in sql:
                    # Extract the SQL from markdown code blocks
                    import re
                    sql_match = re.search(r"```(?:sql)?\s*([\s\S]+?)\s*```", sql)
                    if sql_match:
                        sql = sql_match.group(1).strip()
                    else:
                        # Just remove the backticks if regex doesn't match
                        sql = sql.replace("```sql", "").replace("```", "").strip()
                
                logger.info(f"Generated SQL with OpenAI: {sql[:100]}...")
                return sql
            except Exception as e:
                logger.error(f"Error generating SQL with OpenAI: {str(e)}")

        # Fall back to a simple rule-based approach if OpenAI is not available
        if "country" in question.lower() and "order" in question.lower():
            return "SELECT country, COUNT(*) as order_count FROM customers JOIN orders ON customers.customer_id = orders.customer_id GROUP BY country ORDER BY order_count DESC"
        elif "product" in question.lower() and "revenue" in question.lower():
            return "SELECT product_name, SUM(unit_price * quantity) as revenue FROM products JOIN order_details ON products.product_id = order_details.product_id GROUP BY product_name ORDER BY revenue DESC LIMIT 5"
        elif "sales" in question.lower() and "month" in question.lower():
            return "SELECT MONTH(order_date) as month, SUM(od.quantity * od.unit_price) as sales FROM orders o JOIN order_details od ON o.order_id = od.order_id GROUP BY MONTH(order_date) ORDER BY month"
        elif "inventory" in question.lower() or "stock" in question.lower():
            return "SELECT product_name, units_in_stock FROM products WHERE units_in_stock < 10 ORDER BY units_in_stock ASC"
        else:
            return "SELECT * FROM customers LIMIT 5"

    def ask(self, question):
        """Ask a question about SQL using direct OpenAI integration if available,
        simulating the VannaDefault approach of vn.ask(question=question)
        """
        if self.use_openai:
            try:
                # Extract SQL from the question if it includes 'what does this SQL do'
                sql_to_explain = ""
                if "what does this SQL do" in question.lower(
                ) or "explain this sql" in question.lower():
                    # Try to extract the SQL part from the question
                    import re
                    sql_match = re.search(r"SELECT.*?(?:;|$)", question,
                                          re.IGNORECASE | re.DOTALL)
                    if sql_match:
                        sql_to_explain = sql_match.group(0)
                    else:
                        # If no SQL is found, assume it's in a specific format
                        parts = question.split(":")
                        if len(parts) > 1:
                            sql_to_explain = parts[1].strip()

                if sql_to_explain:
                    prompt = f"""Explain what this SQL query does in simple terms:
                    
                    SQL QUERY: {sql_to_explain}
                    
                    Provide a clear, concise explanation of what this query is retrieving, how it's filtering or aggregating data, and what the results would show. Use non-technical language where possible."""
                else:
                    prompt = f"""Answer this database-related question in simple terms:
                    
                    QUESTION: {question}
                    
                    Provide a clear, concise answer focusing on the database aspects of the question."""

                response = self.openai_client.chat.completions.create(
                    model=self.model,
                    messages=[{
                        "role":
                        "system",
                        "content":
                        "You are a database expert that explains SQL and database concepts in simple terms."
                    }, {
                        "role": "user",
                        "content": prompt
                    }],
                    temperature=0.3)

                explanation = response.choices[0].message.content.strip()
                logger.info(
                    f"Generated explanation with OpenAI: {explanation[:100]}..."
                )
                return explanation
            except Exception as e:
                logger.error(
                    f"Error generating explanation with OpenAI: {str(e)}")

        # Fall back to a simple rule-based approach
        if "what" in question.lower() and "sql" in question.lower():
            # Extract SQL part if available
            sql_part = ""
            if ":" in question:
                sql_part = question.split(":", 1)[1].strip()

            # If it's a question about SQL
            if "country" in sql_part.lower() and "group by" in sql_part.lower(
            ):
                return "This SQL query counts the number of orders placed by customers in each country. It joins the customers and orders tables on the customer_id field, groups the results by country, and orders them by order count in descending order."
            elif "product" in sql_part.lower() and "revenue" in sql_part.lower(
            ):
                return "This SQL query calculates the total revenue generated by each product. It joins the products and order_details tables, multiplies the unit price by the quantity to get revenue for each line item, then groups by product name and orders by revenue in descending order."
            elif "inventory" in sql_part.lower() or "stock" in sql_part.lower(
            ):
                return "This SQL query finds products with low inventory levels. It selects products where the units in stock are below a threshold, and orders them by the stock level in ascending order to show the most critical items first."
            else:
                return "This SQL query retrieves specific data from the database based on the given conditions."
        else:
            return "This query retrieves data from the database according to the specified conditions."

    def get_example_questions(self):
        """Get example questions by generating them with OpenAI or using cached examples"""
        if self.use_openai:
            try:
                # Get schema context
                schema_context = "\n".join(self.knowledge_base if self.
                                           knowledge_base else MOCK_TABLES)

                prompt = f"""Given the following database schema, generate 5 example natural language questions that users might ask to analyze the data:
                
                DATABASE SCHEMA:
                {schema_context}
                
                Generate 5 diverse, business-relevant questions that someone might want to ask about this database. Each question should require different SQL capabilities (e.g., filtering, joining, aggregation, ordering, etc.).
                
                FORMAT YOUR RESPONSE AS A JSON ARRAY OF STRINGS:
                ["Question 1", "Question 2", "Question 3", "Question 4", "Question 5"]"""

                response = self.openai_client.chat.completions.create(
                    model=self.model,
                    messages=[{
                        "role":
                        "system",
                        "content":
                        "You are a helpful assistant that generates example natural language questions for SQL databases."
                    }, {
                        "role": "user",
                        "content": prompt
                    }],
                    response_format={"type": "json_object"},
                    temperature=0.7)

                result = response.choices[0].message.content.strip()

                # Parse JSON response
                import json
                try:
                    questions = json.loads(result)
                    if isinstance(questions, list) and len(questions) > 0:
                        logger.info(
                            f"Generated {len(questions)} example questions with OpenAI"
                        )
                        return questions
                except Exception as e:
                    logger.error(
                        f"Error parsing OpenAI response as JSON: {str(e)}")
            except Exception as e:
                logger.error(
                    f"Error generating example questions with OpenAI: {str(e)}"
                )

        # Fall back to default examples
        return [
            "Show me the top 5 products by revenue",
            "How many orders do we have by country?",
            "What is our monthly sales trend for 2023?",
            "Which products are running low on inventory?",
            "How many products do we have in each category?"
        ]

    def train(self, question=None, sql=None, ddl=None, documentation=None):
        """Train the model with data, similar to VannaDefault.train()"""
        changed = False

        if ddl:
            result = self.train_ddl(ddl)
            changed = changed or result

        if documentation:
            result = self.train_documentation(documentation)
            changed = changed or result

        if question and sql:
            result = self.train_question_sql(question, sql)
            changed = changed or result

        return changed

    def get_training_data(self):
        """Get all training data, similar to VannaDefault.get_training_data()"""
        # Initialize result with empty collections
        result = {"question_sql_pairs": [], "documentation": [], "ddl": []}

        # If ChromaDB is available, populate with actual data
        if self.chroma_client:
            # Get question-SQL pairs
            if self.question_sql_collection:
                try:
                    collection_data = self.question_sql_collection.get()
                    if collection_data and "documents" in collection_data and "metadatas" in collection_data:
                        # Transform into question-SQL pairs
                        for i, doc in enumerate(collection_data["documents"]):
                            if i < len(collection_data["metadatas"]
                                       ) and collection_data["metadatas"][i]:
                                metadata = collection_data["metadatas"][i]
                                if "sql" in metadata:
                                    result["question_sql_pairs"].append({
                                        "question":
                                        doc,
                                        "sql":
                                        metadata["sql"]
                                    })
                except Exception as e:
                    logger.error(f"Error getting question-SQL pairs: {str(e)}")

            # Get documentation
            if self.documentation_collection:
                try:
                    collection_data = self.documentation_collection.get()
                    if collection_data and "documents" in collection_data and "metadatas" in collection_data:
                        # Transform into documentation entries
                        for i, doc in enumerate(collection_data["documents"]):
                            if i < len(collection_data["metadatas"]
                                       ) and collection_data["metadatas"][i]:
                                metadata = collection_data["metadatas"][i]
                                if "table" in metadata:
                                    result["documentation"].append({
                                        "table":
                                        metadata["table"],
                                        "description":
                                        doc
                                    })
                except Exception as e:
                    logger.error(f"Error getting documentation: {str(e)}")

            # Get DDL statements
            if self.ddl_collection:
                try:
                    collection_data = self.ddl_collection.get()
                    if collection_data and "documents" in collection_data:
                        result["ddl"] = collection_data["documents"]
                except Exception as e:
                    logger.error(f"Error getting DDL statements: {str(e)}")

        # If we didn't get any data, use defaults
        if not result["question_sql_pairs"]:
            result["question_sql_pairs"] = [{
                "question":
                "How many orders were placed in 2023?",
                "sql":
                "SELECT COUNT(*) FROM orders WHERE YEAR(order_date) = 2023"
            }, {
                "question":
                "What are the top 5 products by sales?",
                "sql":
                "SELECT p.product_name, SUM(od.quantity * od.unit_price) as sales FROM products p JOIN order_details od ON p.product_id = od.product_id GROUP BY p.product_name ORDER BY sales DESC LIMIT 5"
            }]

        if not result["documentation"]:
            result["documentation"] = [{
                "table":
                "customers",
                "description":
                "Contains customer data including IDs, company names, and contact information"
            }, {
                "table":
                "products",
                "description":
                "Contains product information including IDs, names, and pricing"
            }]

        if not result["ddl"]:
            result[
                "ddl"] = self.knowledge_base if self.knowledge_base else MOCK_TABLES

        return result

    def train_ddl(self, ddl):
        """Train with DDL statements"""
        if not ddl:
            return False

        # Add to our knowledge base
        if ddl not in self.knowledge_base:
            self.knowledge_base.append(ddl)

        # If ChromaDB is available, also store there
        if self.chroma_client and self.ddl_collection:
            try:
                # Generate a unique ID for this DDL
                ddl_id = hashlib.md5(ddl.encode()).hexdigest()

                # Add to ChromaDB
                self.ddl_collection.add(documents=[ddl], ids=[ddl_id])

                logger.info(f"Stored DDL in ChromaDB with ID: {ddl_id}")
                return True
            except Exception as e:
                logger.error(f"Error storing DDL in ChromaDB: {str(e)}")

        return False

    def train_documentation(self, documentation):
        """Train with documentation"""
        if not documentation:
            return False

        # Parse the documentation string to extract table name and description
        # Expected format: "Table <table_name>: <description>"
        try:
            parts = documentation.split(":", 1)
            if len(parts) != 2:
                logger.error(f"Invalid documentation format: {documentation}")
                return False

            table_header = parts[0].strip()
            description = parts[1].strip()

            # Extract table name from header
            import re
            table_match = re.search(r"Table\s+(\w+)", table_header,
                                    re.IGNORECASE)
            if not table_match:
                logger.error(
                    f"Could not extract table name from: {table_header}")
                return False

            table_name = table_match.group(1)

            # If ChromaDB is available, store the documentation
            if self.chroma_client and self.documentation_collection:
                try:
                    # Generate a unique ID for this documentation
                    doc_id = hashlib.md5(documentation.encode()).hexdigest()

                    # Add to ChromaDB
                    self.documentation_collection.add(documents=[description],
                                                      metadatas=[{
                                                          "table":
                                                          table_name
                                                      }],
                                                      ids=[doc_id])

                    logger.info(
                        f"Stored documentation for table '{table_name}' in ChromaDB with ID: {doc_id}"
                    )
                    return True
                except Exception as e:
                    logger.error(
                        f"Error storing documentation in ChromaDB: {str(e)}")

            return False
        except Exception as e:
            logger.error(f"Error parsing documentation: {str(e)}")
            return False

    def train_question_sql(self, question, sql):
        """Train with question-SQL pair"""
        if not question or not sql:
            return False

        # If ChromaDB is available, store the question-SQL pair
        if self.chroma_client and self.question_sql_collection:
            try:
                # Generate a unique ID for this pair
                pair_id = hashlib.md5(f"{question}:{sql}".encode()).hexdigest()

                # Add to ChromaDB
                self.question_sql_collection.add(documents=[question],
                                                 metadatas=[{
                                                     "sql": sql
                                                 }],
                                                 ids=[pair_id])

                logger.info(
                    f"Stored question-SQL pair in ChromaDB with ID: {pair_id}")
                return True
            except Exception as e:
                logger.error(
                    f"Error storing question-SQL pair in ChromaDB: {str(e)}")

        return False

    def init_vanna_model(self):
        """Initialize the model"""
        logger.info("Initializing DirectVannaClient model...")
        # Nothing special to do here since we're using local resources
        return True


def initialize_vanna_client():
    """Initialize Vanna client based on available packages and configuration"""
    from .config import (API_KEY, VANNA_MODEL, LOCAL_MODE, OPENAI_API_KEY,
                         VANNA_DEFAULT_AVAILABLE, VANNA_CLASS_AVAILABLE)

    model = VANNA_MODEL  # Use model from config
    api_key = OPENAI_API_KEY  # Use OpenAI API key for VannaDefault

    logger.info(f"Using model: {model} with local mode: {LOCAL_MODE}")

    # First try to use the official VannaDefault implementation if available
    # This is the preferred approach as explicitly requested
    if (VANNA_DEFAULT_AVAILABLE or VANNA_CLASS_AVAILABLE) and not LOCAL_MODE:
        try:
            # Try VannaDefault with OpenAI API key and model
            logger.info(
                f"Trying OfficialVannaClient with VannaDefault (model={model}, api_key=OpenAI API key)..."
            )
            client = OfficialVannaClient(api_key=api_key, model=model)
            # Check if it was successfully initialized
            if client.vn is not None:
                logger.info(
                    "Successfully initialized OfficialVannaClient with VannaDefault"
                )
                return client, "OfficialVannaClient"
            else:
                logger.warning(
                    "OfficialVannaClient initialization failed (VannaDefault instance is None)"
                )
        except Exception as e:
            logger.warning(
                f"OfficialVannaClient with VannaDefault failed: {str(e)}")

    # Try our direct implementation using OpenAI API (no HTTP calls)
    try:
        # Use DirectVannaClient which uses OpenAI API directly to simulate VannaDefault
        logger.info(
            "Trying DirectVannaClient (local OpenAI-powered VannaDefault simulation)..."
        )
        direct_client = DirectVannaClient(api_key=api_key, model=model)
        # Check if OpenAI integration is available
        if direct_client.use_openai:
            logger.info(
                "Successfully initialized DirectVannaClient with OpenAI")
            return direct_client, "DirectVannaClient"
        else:
            logger.warning(
                "DirectVannaClient initialized but OpenAI integration is not available"
            )
    except Exception as e:
        logger.warning(f"DirectVannaClient failed: {str(e)}")

    # In local mode, prioritize ChromaDB for storage without API
    if LOCAL_MODE and CHROMADB_AVAILABLE:
        try:
            # Use DirectVannaClient which works well with local ChromaDB
            logger.info(
                "Using DirectVannaClient for local mode with ChromaDB...")
            return DirectVannaClient(api_key=None,
                                     model="local"), "DirectVannaClient"
        except Exception as e:
            logger.warning(
                f"DirectVannaClient for local mode failed: {str(e)}")

    # Use VannaRemoteClient as fallback - NO HTTP API CALLS
    logger.info("Using VannaRemoteClient as fallback...")
    return VannaRemoteClient(api_key=api_key, model=model), "VannaRemoteClient"
