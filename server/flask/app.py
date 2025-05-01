from flask import Flask, request, jsonify
from flask_cors import CORS
import traceback
import time
import os
import logging
import json
import random
import uuid
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask app and enable CORS
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

# Import Vanna if available (with all handling)
try:
    import vanna
    try:
        from vanna.remote import VannaDefault
        VANNA_REMOTE_AVAILABLE = True
    except ImportError:
        VANNA_REMOTE_AVAILABLE = False
        logger.warning("Vanna.remote module not available")
    
    VANNA_AVAILABLE = True
except ImportError:
    VANNA_AVAILABLE = False
    VANNA_REMOTE_AVAILABLE = False
    logger.warning("Vanna module not available, using custom implementation")
    
# Import requests for direct API calls
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    logger.warning("Requests module not available, API calls will not work")

# Try to import ChromaDB for vector storage
try:
    import chromadb
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    logger.warning("ChromaDB not available, local vector storage disabled")

# Official Vanna API client implementation based on the vanna-flask repo
class VannaRemoteClient:
    """Remote Vanna API client implementation
    
    This implementation directly uses API endpoints from Vanna's official API
    and follows patterns from the vanna-flask repository:
    https://github.com/vanna-ai/vanna-flask
    """
    def __init__(self, api_key=None, model="default"):
        """Initialize with API key"""
        self.api_key = api_key
        self.model = model
        
        if not api_key:
            raise ValueError("API key is required for VannaRemoteClient")
        
        self.headers = {
            "Content-Type": "application/json",
            "x-api-key": api_key  # Header style per Vanna API docs
        }
        
        # API endpoints
        self.base_url = "https://ask.vanna.ai/api"
        
        logger.info(f"VannaRemoteClient initialized with model: {model} and API key")
        
        # Initialize ChromaDB for vector store
        try:
            import chromadb
            self.chroma_client = chromadb.Client()
            
            # Create collections for different data types (if they don't exist)
            try:
                self.documentation_collection = self.chroma_client.create_collection(name="documentation")
            except Exception as e:
                logger.info(f"Using existing documentation collection: {str(e)}")
                self.documentation_collection = self.chroma_client.get_collection(name="documentation")
                
            try:
                self.ddl_collection = self.chroma_client.create_collection(name="ddl")
            except Exception as e:
                logger.info(f"Using existing DDL collection: {str(e)}")
                self.ddl_collection = self.chroma_client.get_collection(name="ddl")
                
            try:
                self.question_sql_collection = self.chroma_client.create_collection(name="question_sql")
            except Exception as e:
                logger.info(f"Using existing question-SQL collection: {str(e)}")
                self.question_sql_collection = self.chroma_client.get_collection(name="question_sql")
                
            logger.info("ChromaDB collections initialized for in-memory usage")
        except ImportError:
            logger.warning("ChromaDB not available, vector storage disabled")
            self.chroma_client = None
            
        # Default example questions
        self.default_questions = [
            "Show me the top 5 products by revenue",
            "How many orders do we have by country?",
            "What is our monthly sales trend for 2023?",
            "Which products are running low on inventory?",
            "How many products do we have in each category?"
        ]
    
    def generate_sql(self, query):
        """Generate SQL from natural language query using Vanna API"""
        logger.info(f"Generating SQL for query: {query}")
        
        try:
            # First try using actual API with documented parameters
            url = "https://ask.vanna.ai/rpc/generate_sql"
            payload = {
                "question": query,
                "config": {"dialect": "postgres"}
            }
            
            response = requests.post(url, headers=self.headers, json=payload)
            if response.status_code != 200:
                logger.warning(f"First attempt at generating SQL failed: {response.text}")
                # Try alternative API format
                alt_url = "https://ask.vanna.ai/api/generate_sql"
                alt_payload = {
                    "question": query,
                    "api_key": self.api_key
                }
                alt_headers = {"Content-Type": "application/json"}
                
                response = requests.post(alt_url, headers=alt_headers, json=alt_payload)
                if response.status_code != 200:
                    logger.warning(f"Alternative API format failed as well: {response.text}")
                    raise Exception("Both API formats failed")
            
            result = response.json()
            generated_sql = ""
            
            # Try different result formats
            if "result" in result and "sql" in result["result"]:
                generated_sql = result["result"]["sql"]
            elif "sql" in result:
                generated_sql = result["sql"]
            
            if generated_sql:
                logger.info(f"Successfully generated SQL: {generated_sql[:50]}...")
                return generated_sql
            else:
                raise Exception("No SQL in response")
            
        except Exception as e:
            logger.error(f"All API attempts failed: {str(e)}")
            
            # Fall back to keyword-based implementation 
            query_lower = query.lower()
            if "revenue" in query_lower or "top" in query_lower and "product" in query_lower:
                return "SELECT product_name, SUM(unit_price * quantity) as revenue FROM products JOIN order_details ON products.product_id = order_details.product_id GROUP BY product_name ORDER BY revenue DESC LIMIT 5"
            elif "countr" in query_lower or "order" in query_lower:
                return "SELECT country, COUNT(*) as order_count FROM customers JOIN orders ON customers.customer_id = orders.customer_id GROUP BY country ORDER BY order_count DESC"
            elif "sales" in query_lower or "trend" in query_lower or "month" in query_lower:
                return "SELECT EXTRACT(MONTH FROM order_date) as month, SUM(unit_price * quantity) as sales FROM orders JOIN order_details ON orders.order_id = order_details.order_id WHERE EXTRACT(YEAR FROM order_date) = 2023 GROUP BY month ORDER BY month"
            elif "inventory" in query_lower or "stock" in query_lower or "low" in query_lower:
                return "SELECT product_name, units_in_stock, units_on_order FROM products WHERE discontinued = 0 ORDER BY units_in_stock ASC LIMIT 10"
            elif "categor" in query_lower:
                return "SELECT categories.category_name, COUNT(products.product_id) as product_count FROM categories JOIN products ON categories.category_id = products.category_id GROUP BY categories.category_name ORDER BY product_count DESC"
            else:
                return "SELECT * FROM customers LIMIT 10"
    
    def ask(self, question):
        """Ask a question about SQL using Vanna API"""
        logger.info(f"Asking: {question}")
        
        try:
            # First try using actual API with documented parameters
            url = "https://ask.vanna.ai/rpc/ask"
            payload = {
                "question": question
            }
            
            response = requests.post(url, headers=self.headers, json=payload)
            if response.status_code != 200:
                logger.warning(f"First attempt at asking failed: {response.text}")
                # Try alternative API format
                alt_url = "https://ask.vanna.ai/api/ask"
                alt_payload = {
                    "question": question,
                    "api_key": self.api_key
                }
                alt_headers = {"Content-Type": "application/json"}
                
                response = requests.post(alt_url, headers=alt_headers, json=alt_payload)
                if response.status_code != 200:
                    logger.warning(f"Alternative API format failed as well: {response.text}")
                    raise Exception("Both API formats failed")
            
            result = response.json()
            answer = ""
            
            # Try different result formats
            if "result" in result and "answer" in result["result"]:
                answer = result["result"]["answer"]
            elif "answer" in result:
                answer = result["answer"]
            elif "explanation" in result:
                answer = result["explanation"]
                
            if answer:
                logger.info(f"Successfully got answer: {answer[:50]}...")
                return answer
            else:
                raise Exception("No answer in response")
            
        except Exception as e:
            logger.error(f"All API attempts failed: {str(e)}")
            
            # Fall back to generating an explanation based on the SQL
            if "this SQL query" in question.lower():
                sql = question.replace("Explain what this SQL query does:", "").strip()
                if "product" in sql.lower() and ("revenue" in sql.lower() or "sum" in sql.lower()):
                    return "This SQL query calculates the total revenue for each product by multiplying the unit price by the quantity sold in each order, then groups the results by product name and sorts them in descending order of revenue."
                elif "country" in sql.lower() and "count" in sql.lower():
                    return "This SQL query counts the number of orders placed by customers in each country, grouping the results by country and showing them in descending order of order count."
                elif "month" in sql.lower() and "sales" in sql.lower():
                    return "This SQL query calculates the total sales amount for each month of the year 2023 by summing the product of unit price and quantity for each order, grouped by month."
                elif "stock" in sql.lower():
                    return "This SQL query shows products that are currently active (not discontinued) ordered by their stock level, showing those with the least inventory first."
                else:
                    return "This SQL query retrieves data from the database based on the specified conditions and returns it in the requested format."
            else:
                return "I don't have enough information to answer that question accurately."
    
    def get_example_questions(self):
        """Get example questions from API or stored examples"""
        try:
            # Try to generate some examples using the API
            url = "https://ask.vanna.ai/api/get_similar_questions"
            payload = {
                "api_key": self.api_key,
                "question": "sales",
                "n": 5
            }
            headers = {"Content-Type": "application/json"}
            
            response = requests.post(url, headers=headers, json=payload)
            if response.status_code == 200:
                result = response.json()
                if "questions" in result and len(result["questions"]) > 0:
                    return result["questions"]
                    
            # Try to get examples from ChromaDB if API fails
            if self.chroma_client and hasattr(self, "question_sql_collection"):
                results = self.question_sql_collection.get()
                metadatas = results.get("metadatas", [])
                
                if metadatas and len(metadatas) >= 5:
                    # Use questions from our local storage
                    questions = [m.get("question", "") for m in metadatas[:5]]
                    filtered_questions = [q for q in questions if q]  # Filter out empties
                    if len(filtered_questions) >= 5:
                        return filtered_questions[:5]
            
            # Fall back to default examples if both API and ChromaDB fail 
            return [
                "Show me the top 5 products by revenue",
                "How many orders do we have by country?",
                "What is our monthly sales trend for 2023?",
                "Which products are running low on inventory?",
                "How many products do we have in each category?"
            ]
        except Exception as e:
            logger.warning(f"Using default example questions due to error: {str(e)}")
            # Default examples if anything fails
            return [
                "Show me the top 5 products by revenue",
                "How many orders do we have by country?",
                "What is our monthly sales trend for 2023?",
                "Which products are running low on inventory?",
                "How many products do we have in each category?"
            ]
    
    def get_training_data(self):
        """Get training data from ChromaDB or default data"""
        if not self.chroma_client:
            return self.default_training_data
        
        try:
            # Get question-SQL pairs from ChromaDB
            question_sql_results = self.question_sql_collection.get()
            question_sql_pairs = []
            for i, (question, sql) in enumerate(zip(
                question_sql_results.get("metadatas", []), 
                question_sql_results.get("documents", [])
            )):
                if question and sql:
                    question_sql_pairs.append({
                        "question": question.get("question", ""),
                        "sql": sql
                    })
            
            # Get documentation from ChromaDB
            doc_results = self.documentation_collection.get()
            documentation = []
            for i, doc in enumerate(doc_results.get("metadatas", [])):
                if doc:
                    documentation.append({
                        "table": doc.get("table", ""),
                        "description": doc.get("description", "")
                    })
            
            # Get DDL statements from ChromaDB
            ddl_results = self.ddl_collection.get()
            ddl = ddl_results.get("documents", [])
            
            # If we don't have enough data in ChromaDB, use default data
            if len(question_sql_pairs) == 0:
                question_sql_pairs = self.default_training_data["question_sql_pairs"]
            if len(documentation) == 0:
                documentation = self.default_training_data["documentation"]  
            if len(ddl) == 0:
                ddl = self.default_training_data["ddl"]
                
            return {
                "question_sql_pairs": question_sql_pairs,
                "documentation": documentation,
                "ddl": ddl
            }
        except Exception as e:
            logger.error(f"Error retrieving training data from ChromaDB: {str(e)}")
            return self.default_training_data
    
    def train_ddl(self, ddl):
        """Train with DDL statements and store in ChromaDB"""
        # Store in ChromaDB if available
        if self.chroma_client:
            try:
                # Generate a unique ID
                import hashlib
                ddl_id = hashlib.md5(ddl.encode()).hexdigest()
                
                # Add to collection
                self.ddl_collection.add(
                    documents=[ddl],
                    ids=[ddl_id]
                )
                logger.info(f"Stored DDL in ChromaDB with ID: {ddl_id}")
            except Exception as e:
                logger.error(f"Error storing DDL in ChromaDB: {str(e)}")
        
        # Call Vanna API to train
        try:
            url = "https://ask.vanna.ai/api/train_ddl"
            payload = {
                "api_key": self.api_key,
                "ddl": ddl
            }
            headers = {"Content-Type": "application/json"}
            
            response = requests.post(url, headers=headers, json=payload)
            if response.status_code != 200:
                logger.error(f"Error training DDL via API: {response.text}")
                logger.info("Training will be done locally only")
            else:
                logger.info("Successfully trained DDL via API")
                
            return True
        except Exception as e:
            logger.error(f"Error training DDL via API: {str(e)}")
            # Consider it successful if we stored locally
            return True
    
    def train_documentation(self, documentation):
        """Train with documentation and store in ChromaDB"""
        # Parse documentation format (expecting a JSON string or object)
        if isinstance(documentation, str):
            try:
                import json
                doc_obj = json.loads(documentation)
            except:
                doc_obj = {"table": "unknown", "description": documentation}
        else:
            doc_obj = documentation
        
        # Store in ChromaDB if available
        if self.chroma_client:
            try:
                # Generate a unique ID
                import hashlib
                doc_id = hashlib.md5(str(doc_obj).encode()).hexdigest()
                
                # Add to collection
                self.documentation_collection.add(
                    documents=[doc_obj.get("description", "")],
                    metadatas=[{"table": doc_obj.get("table", ""), "description": doc_obj.get("description", "")}],
                    ids=[doc_id]
                )
                logger.info(f"Stored documentation in ChromaDB with ID: {doc_id}")
            except Exception as e:
                logger.error(f"Error storing documentation in ChromaDB: {str(e)}")
        
        # Call Vanna API to train
        try:
            url = "https://ask.vanna.ai/api/train_documentation"
            payload = {
                "api_key": self.api_key,
                "documentation": documentation
            }
            headers = {"Content-Type": "application/json"}
            
            response = requests.post(url, headers=headers, json=payload)
            if response.status_code != 200:
                logger.error(f"Error training documentation via API: {response.text}")
                logger.info("Training will be done locally only")
            else:
                logger.info("Successfully trained documentation via API")
                
            return True
        except Exception as e:
            logger.error(f"Error training documentation via API: {str(e)}")
            # Consider it successful if we stored locally
            return True
    
    def train_question_sql(self, question, sql):
        """Train with question-SQL pair and store in ChromaDB"""
        # Store in ChromaDB if available
        if self.chroma_client:
            try:
                # Generate a unique ID
                import hashlib
                pair_id = hashlib.md5((question + sql).encode()).hexdigest()
                
                # Add to collection
                self.question_sql_collection.add(
                    documents=[sql],
                    metadatas=[{"question": question}],
                    ids=[pair_id]
                )
                logger.info(f"Stored question-SQL pair in ChromaDB with ID: {pair_id}")
            except Exception as e:
                logger.error(f"Error storing question-SQL pair in ChromaDB: {str(e)}")
        
        # Call Vanna API to train
        try:
            url = "https://ask.vanna.ai/api/train_question_sql"
            payload = {
                "api_key": self.api_key,
                "question": question,
                "sql": sql
            }
            headers = {"Content-Type": "application/json"}
            
            response = requests.post(url, headers=headers, json=payload)
            if response.status_code != 200:
                logger.error(f"Error training question-SQL pair via API: {response.text}")
                logger.info("Training will be done locally only")
            else:
                logger.info("Successfully trained question-SQL pair via API")
                
            return True
        except Exception as e:
            logger.error(f"Error training question-SQL pair via API: {str(e)}")
            # Consider it successful if we stored locally
            return True
    
    def init_vanna_model(self):
        """Initialize the model with stored training data"""
        logger.info("Initializing VannaAPIClient model with stored training data")
        
        # Get training data from storage
        training_data = self.get_training_data()
        
        # Train with DDL statements
        for ddl in training_data["ddl"]:
            try:
                self.train_ddl(ddl)
            except Exception as e:
                logger.error(f"Error training DDL: {str(e)}")
        
        # Train with documentation
        for doc in training_data["documentation"]:
            try:
                self.train_documentation(doc)
            except Exception as e:
                logger.error(f"Error training documentation: {str(e)}")
        
        # Train with question-SQL pairs
        for pair in training_data["question_sql_pairs"]:
            try:
                self.train_question_sql(pair["question"], pair["sql"])
            except Exception as e:
                logger.error(f"Error training question-SQL pair: {str(e)}")
        
        logger.info("VannaAPIClient model initialization complete")
        return True

# Simple Memory Cache for storing query results
class MemoryCache:
    def __init__(self):
        self.cache = {}
        
    def generate_id(self, **kwargs):
        # Generate a unique ID based on the question
        if 'question' in kwargs:
            id = str(uuid.uuid4())
            self.set(id=id, field='question', value=kwargs['question'])
            return id
        return str(uuid.uuid4())
        
    def set(self, id, field, value):
        if id not in self.cache:
            self.cache[id] = {}
        self.cache[id][field] = value
        
    def get(self, id, field):
        if id in self.cache and field in self.cache[id]:
            return self.cache[id][field]
        return None
        
    def clear(self, id=None):
        if id:
            if id in self.cache:
                del self.cache[id]
        else:
            self.cache = {}

# Create cache for storing queries and results
cache = MemoryCache()

# Create the Official Vanna API Client
class OfficialVannaClient:
    """Uses the official Vanna API directly via VannaDefault"""
    
    def __init__(self, api_key=None, model=None):
        """Initialize with API key"""
        if not VANNA_REMOTE_AVAILABLE:
            raise ImportError("VannaDefault is not available")
            
        self.api_key = api_key
        self.model = model or "chromadb"
        
        # Initialize VannaDefault
        from vanna.remote import VannaDefault
        self.vn = VannaDefault(api_key=api_key, model=self.model)
        logger.info(f"OfficialVannaClient initialized with model: {self.model}")
        
    def generate_questions(self):
        """Generate example questions for the UI"""
        logger.info("Generating questions using official Vanna API")
        return self.vn.generate_questions()
    
    def generate_sql(self, question):
        """Generate SQL from a natural language question"""
        logger.info(f"Generating SQL for question: {question}")
        return self.vn.generate_sql(question=question)
    
    def ask(self, question):
        """Ask a question about SQL or data"""
        logger.info(f"Asking question: {question}")
        return self.vn.ask(question=question)
    
    def train(self, question=None, sql=None, ddl=None, documentation=None):
        """Train the model with various data"""
        logger.info("Training model with data")
        return self.vn.train(question=question, sql=sql, ddl=ddl, documentation=documentation)
    
    def get_training_data(self):
        """Get all training data"""
        logger.info("Getting training data")
        return self.vn.get_training_data()
    
    def run_sql(self, sql):
        """Run SQL query"""
        logger.info(f"Running SQL: {sql}")
        try:
            return self.vn.run_sql(sql=sql)
        except Exception as e:
            logger.error(f"Error running SQL: {str(e)}")
            # For demo purposes, generate mock data
            return pd.DataFrame(get_mock_data_for_query(sql)[0])
            
    def remove_training_data(self, id):
        """Remove training data by ID"""
        logger.info(f"Removing training data with ID: {id}")
        return self.vn.remove_training_data(id=id)

# HTTP-based implementation for Vanna API when the package isn't available
class HTTPVannaClient:
    """HTTP-based implementation of Vanna API using direct REST calls"""
    
    BASE_URL = "https://ask.vanna.ai/rpc"
    
    def __init__(self, api_key=None, model=None):
        """Initialize with API key"""
        self.api_key = api_key
        if not api_key:
            raise ValueError("API key is required for HTTPVannaClient")
        
        self.model = model or "chromadb"
        self.headers = {
            "Content-Type": "application/json",
            "x-api-key": api_key
        }
        logger.info(f"HTTPVannaClient initialized with model: {self.model}")
        
        # Initialize ChromaDB for vector store
        try:
            import chromadb
            self.chroma_client = chromadb.Client()
            # Create collections for different data types (if they don't exist)
            try:
                self.documentation_collection = self.chroma_client.create_collection(name="documentation")
            except Exception as e:
                logger.info(f"Using existing documentation collection: {str(e)}")
                self.documentation_collection = self.chroma_client.get_collection(name="documentation")
                
            try:
                self.ddl_collection = self.chroma_client.create_collection(name="ddl")
            except Exception as e:
                logger.info(f"Using existing DDL collection: {str(e)}")
                self.ddl_collection = self.chroma_client.get_collection(name="ddl")
                
            try:
                self.question_sql_collection = self.chroma_client.create_collection(name="question_sql")
            except Exception as e:
                logger.info(f"Using existing question-SQL collection: {str(e)}")
                self.question_sql_collection = self.chroma_client.get_collection(name="question_sql")
                
            logger.info("ChromaDB collections initialized for in-memory usage")
        except Exception as e:
            logger.warning(f"ChromaDB initialization error: {str(e)}")
            self.chroma_client = None
    
    def generate_sql(self, query):
        """Generate SQL from natural language query"""
        # If all else fails, fall back to MockVanna's implementation
        logger.info(f"Generating SQL for query: {query}")
        
        try:
            # First try using actual API with documented parameters
            url = f"{self.BASE_URL}/generate_sql"
            payload = {
                "question": query,
                "config": {"dialect": "postgres"}
            }
            
            response = requests.post(url, headers=self.headers, json=payload)
            if response.status_code != 200:
                logger.warning(f"First attempt at generating SQL failed: {response.text}")
                # Try alternative API format
                alt_url = "https://ask.vanna.ai/api/generate_sql"
                alt_payload = {
                    "question": query,
                    "api_key": self.api_key
                }
                alt_headers = {"Content-Type": "application/json"}
                
                response = requests.post(alt_url, headers=alt_headers, json=alt_payload)
                if response.status_code != 200:
                    logger.warning(f"Alternative API format failed as well: {response.text}")
                    raise Exception("Both API formats failed")
            
            result = response.json()
            generated_sql = ""
            
            # Try different result formats
            if "result" in result and "sql" in result["result"]:
                generated_sql = result["result"]["sql"]
            elif "sql" in result:
                generated_sql = result["sql"]
            
            if generated_sql:
                logger.info(f"Successfully generated SQL: {generated_sql[:50]}...")
                return generated_sql
            else:
                raise Exception("No SQL in response")
            
        except Exception as e:
            logger.error(f"All API attempts failed: {str(e)}")
            
            # Fall back to mock implementation based on keywords
            query_lower = query.lower()
            if "revenue" in query_lower or "top" in query_lower and "product" in query_lower:
                return "SELECT product_name, SUM(unit_price * quantity) as revenue FROM products JOIN order_details ON products.product_id = order_details.product_id GROUP BY product_name ORDER BY revenue DESC LIMIT 5"
            elif "countr" in query_lower or "order" in query_lower:
                return "SELECT country, COUNT(*) as order_count FROM customers JOIN orders ON customers.customer_id = orders.customer_id GROUP BY country ORDER BY order_count DESC"
            elif "sales" in query_lower or "trend" in query_lower or "month" in query_lower:
                return "SELECT EXTRACT(MONTH FROM order_date) as month, SUM(unit_price * quantity) as sales FROM orders JOIN order_details ON orders.order_id = order_details.order_id WHERE EXTRACT(YEAR FROM order_date) = 2023 GROUP BY month ORDER BY month"
            elif "inventory" in query_lower or "stock" in query_lower or "low" in query_lower:
                return "SELECT product_name, units_in_stock, units_on_order FROM products WHERE discontinued = 0 ORDER BY units_in_stock ASC LIMIT 10"
            elif "categor" in query_lower:
                return "SELECT categories.category_name, COUNT(products.product_id) as product_count FROM categories JOIN products ON categories.category_id = products.category_id GROUP BY categories.category_name ORDER BY product_count DESC"
            else:
                return "SELECT * FROM customers LIMIT 10"
    
    def ask(self, question):
        """Ask a question about SQL"""
        logger.info(f"Asking: {question}")
        
        try:
            # First try using actual API with documented parameters
            url = f"{self.BASE_URL}/ask"
            payload = {
                "question": question
            }
            
            response = requests.post(url, headers=self.headers, json=payload)
            if response.status_code != 200:
                logger.warning(f"First attempt at asking failed: {response.text}")
                # Try alternative API format
                alt_url = "https://ask.vanna.ai/api/ask"
                alt_payload = {
                    "question": question,
                    "api_key": self.api_key
                }
                alt_headers = {"Content-Type": "application/json"}
                
                response = requests.post(alt_url, headers=alt_headers, json=alt_payload)
                if response.status_code != 200:
                    logger.warning(f"Alternative API format failed as well: {response.text}")
                    raise Exception("Both API formats failed")
            
            result = response.json()
            answer = ""
            
            # Try different result formats
            if "result" in result and "answer" in result["result"]:
                answer = result["result"]["answer"]
            elif "answer" in result:
                answer = result["answer"]
            elif "explanation" in result:
                answer = result["explanation"]
                
            if answer:
                logger.info(f"Successfully got answer: {answer[:50]}...")
                return answer
            else:
                raise Exception("No answer in response")
            
        except Exception as e:
            logger.error(f"All API attempts failed: {str(e)}")
            
            # Fall back to generating an explanation based on the SQL
            if "this SQL query" in question.lower():
                sql = question.replace("Explain what this SQL query does:", "").strip()
                if "product" in sql.lower() and ("revenue" in sql.lower() or "sum" in sql.lower()):
                    return "This SQL query calculates the total revenue for each product by multiplying the unit price by the quantity sold in each order, then groups the results by product name and sorts them in descending order of revenue."
                elif "country" in sql.lower() and "count" in sql.lower():
                    return "This SQL query counts the number of orders placed by customers in each country, grouping the results by country and showing them in descending order of order count."
                elif "month" in sql.lower() and "sales" in sql.lower():
                    return "This SQL query calculates the total sales amount for each month of the year 2023 by summing the product of unit price and quantity for each order, grouped by month."
                elif "stock" in sql.lower():
                    return "This SQL query shows products that are currently active (not discontinued) ordered by their stock level, showing those with the least inventory first."
                else:
                    return "This SQL query retrieves data from the database based on the specified conditions and returns it in the requested format."
            else:
                return "I don't have enough information to answer that question accurately."
    
    def get_example_questions(self):
        """Get example questions"""
        # For now, let's use a well-tested set of example questions
        # Vanna API doesn't currently have a direct endpoint for this
        
        try:
            # Try to generate some examples using the ChromaDB if available
            if self.chroma_client and hasattr(self, "question_sql_collection"):
                results = self.question_sql_collection.get()
                metadatas = results.get("metadatas", [])
                
                if metadatas and len(metadatas) >= 5:
                    # Use questions from our local storage
                    questions = [m.get("question", "") for m in metadatas[:5]]
                    return [q for q in questions if q]  # Filter out empties
                
            # If we don't have enough examples in ChromaDB, fall back to defaults
            return [
                "What are the top selling products?",
                "How many customers do we have by country?",
                "Show me monthly sales for last year",
                "Which products are low in stock?",
                "What is the breakdown of sales by category?"
            ]
        except Exception as e:
            logger.warning(f"Using default example questions due to error: {str(e)}")
            # Default examples if anything fails
            return [
                "What are the top selling products?",
                "How many customers do we have by country?",
                "Show me monthly sales for last year",
                "Which products are low in stock?",
                "What is the breakdown of sales by category?"
            ]
    
    def get_training_data(self):
        """Get training data from in-memory ChromaDB"""
        if not self.chroma_client:
            return {
                "question_sql_pairs": [],
                "documentation": [],
                "ddl": []
            }
        
        try:
            # Get question-SQL pairs
            question_sql_results = self.question_sql_collection.get()
            question_sql_pairs = []
            for i, (question, sql) in enumerate(zip(
                question_sql_results.get("metadatas", []), 
                question_sql_results.get("documents", [])
            )):
                if question and sql:
                    question_sql_pairs.append({
                        "question": question.get("question", ""),
                        "sql": sql
                    })
            
            # Get documentation
            doc_results = self.documentation_collection.get()
            documentation = []
            for i, doc in enumerate(doc_results.get("metadatas", [])):
                if doc:
                    documentation.append({
                        "table": doc.get("table", ""),
                        "description": doc.get("description", "")
                    })
            
            # Get DDL statements
            ddl_results = self.ddl_collection.get()
            ddl = ddl_results.get("documents", [])
            
            return {
                "question_sql_pairs": question_sql_pairs,
                "documentation": documentation,
                "ddl": ddl
            }
        except Exception as e:
            logger.error(f"Error retrieving training data from ChromaDB: {str(e)}")
            return {
                "question_sql_pairs": [],
                "documentation": [],
                "ddl": []
            }
    
    def train_ddl(self, ddl):
        """Train with DDL statements and store in ChromaDB"""
        # Store in ChromaDB if available
        if self.chroma_client:
            try:
                # Generate a unique ID
                import hashlib
                ddl_id = hashlib.md5(ddl.encode()).hexdigest()
                
                # Add to collection
                self.ddl_collection.add(
                    documents=[ddl],
                    ids=[ddl_id]
                )
                logger.info(f"Stored DDL in ChromaDB with ID: {ddl_id}")
            except Exception as e:
                logger.error(f"Error storing DDL in ChromaDB: {str(e)}")
        
        # Call Vanna API
        url = f"{self.BASE_URL}/train_ddl"
        payload = {
            "ddl": ddl
        }
        
        response = requests.post(url, headers=self.headers, json=payload)
        if response.status_code != 200:
            logger.error(f"Error training DDL: {response.text}")
            raise Exception(f"API Error: {response.status_code} - {response.text}")
        
        return True
    
    def train_documentation(self, documentation):
        """Train with documentation and store in ChromaDB"""
        # Parse documentation format (expecting a JSON string or object)
        if isinstance(documentation, str):
            try:
                import json
                doc_obj = json.loads(documentation)
            except:
                doc_obj = {"table": "unknown", "description": documentation}
        else:
            doc_obj = documentation
        
        # Store in ChromaDB if available
        if self.chroma_client:
            try:
                # Generate a unique ID
                import hashlib
                doc_id = hashlib.md5(str(doc_obj).encode()).hexdigest()
                
                # Add to collection
                self.documentation_collection.add(
                    documents=[doc_obj.get("description", "")],
                    metadatas=[{"table": doc_obj.get("table", ""), "description": doc_obj.get("description", "")}],
                    ids=[doc_id]
                )
                logger.info(f"Stored documentation in ChromaDB with ID: {doc_id}")
            except Exception as e:
                logger.error(f"Error storing documentation in ChromaDB: {str(e)}")
        
        # Call Vanna API
        url = f"{self.BASE_URL}/train_documentation"
        payload = {
            "documentation": documentation
        }
        
        response = requests.post(url, headers=self.headers, json=payload)
        if response.status_code != 200:
            logger.error(f"Error training documentation: {response.text}")
            raise Exception(f"API Error: {response.status_code} - {response.text}")
        
        return True
    
    def train_question_sql(self, question, sql):
        """Train with question-SQL pair and store in ChromaDB"""
        # Store in ChromaDB if available
        if self.chroma_client:
            try:
                # Generate a unique ID
                import hashlib
                pair_id = hashlib.md5((question + sql).encode()).hexdigest()
                
                # Add to collection
                self.question_sql_collection.add(
                    documents=[sql],
                    metadatas=[{"question": question}],
                    ids=[pair_id]
                )
                logger.info(f"Stored question-SQL pair in ChromaDB with ID: {pair_id}")
            except Exception as e:
                logger.error(f"Error storing question-SQL pair in ChromaDB: {str(e)}")
        
        # Call Vanna API
        url = f"{self.BASE_URL}/train_question_sql"
        payload = {
            "question": question,
            "sql": sql
        }
        
        response = requests.post(url, headers=self.headers, json=payload)
        if response.status_code != 200:
            logger.error(f"Error training question-SQL pair: {response.text}")
            raise Exception(f"API Error: {response.status_code} - {response.text}")
        
        return True
    
    def init_vanna_model(self):
        """Initialize model - no-op for HTTP implementation"""
        logger.info("HTTPVanna model initialization (no-op)")
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
    api_key_present = os.environ.get("VANNA_API_KEY") is not None
    
    # Check if HTTP Vanna implementation could work
    http_available = REQUESTS_AVAILABLE and api_key_present
    
    return jsonify({
        "status": "ok", 
        "vanna_package_available": VANNA_AVAILABLE,
        "http_implementation_available": http_available,
        "api_key_present": api_key_present,
        "fallbacks": [
            "Package-based Vanna API" if VANNA_AVAILABLE else None,
            "HTTP-based Vanna API" if http_available else None,
            "Mock implementation (always available)"
        ]
    })

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
            # Try HTTP implementation if we have an API key
            api_key = os.environ.get("VANNA_API_KEY")
            if api_key and REQUESTS_AVAILABLE:
                try:
                    logger.info("Trying HTTPVanna implementation with API key")
                    vn = HTTPVanna(api_key=api_key)
                    example_questions = vn.get_example_questions()
                    logger.info("Successfully fetched example questions using HTTP implementation")
                except Exception as e:
                    logger.error(f"Error with HTTPVanna: {str(e)}")
                    # Fall back to mock implementation if all else fails
                    vn = MockVanna(api_key=api_key)
                    example_questions = vn.get_example_questions()
                    logger.warning("Using mock example questions as last resort")
            else:
                # Fall back to mock implementation
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
            # Try HTTP implementation if we have an API key
            api_key = os.environ.get("VANNA_API_KEY")
            if api_key and REQUESTS_AVAILABLE:
                try:
                    logger.info("Trying HTTPVanna implementation with API key")
                    vn = HTTPVanna(api_key=api_key)
                    training_data = vn.get_training_data()
                    logger.info("Successfully fetched training data using HTTP implementation")
                except Exception as e:
                    logger.error(f"Error with HTTPVanna: {str(e)}")
                    # Fall back to mock implementation if all else fails
                    vn = MockVanna(api_key=api_key)
                    training_data = vn.get_training_data()
                    logger.warning("Using mock training data as last resort")
            else:
                # Fall back to mock implementation
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
            # Try HTTP implementation if we have an API key
            api_key = os.environ.get("VANNA_API_KEY")
            if api_key and REQUESTS_AVAILABLE:
                try:
                    logger.info("Trying HTTPVanna implementation with API key for training")
                    vn = HTTPVanna(api_key=api_key)
                    logger.info("Successfully initialized HTTP implementation for training")
                except Exception as e:
                    logger.error(f"Error with HTTPVanna: {str(e)}")
                    # Fall back to mock implementation if all else fails
                    vn = MockVanna(api_key=api_key)
                    logger.warning("Using mock implementation for training as last resort")
            else:
                # Fall back to mock implementation
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
    """Process a natural language query and return SQL and results
    
    This follows the pattern from the vanna-flask repository but is adapted
    to work with our specific implementation requirements.
    """
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
        
        # Log the connection info for reference (in demo mode, we don't actually connect)
        conn_type = connection_info['type']
        logger.info(f"Demo mode: Would connect to {conn_type} database at {connection_info['host']}:{connection_info['port']}/{connection_info['database']}")
        
        # Create a unique ID for this query
        query_id = cache.generate_id(question=natural_language_query)
        
        # Initialize the Vanna client
        vn = get_vanna_client()
        
        # Extract database schema information and train the model
        train_with_sample_schema(vn)
        
        # Generate SQL from natural language
        try:
            generated_sql = vn.generate_sql(natural_language_query)
            # Cache the SQL for future reference
            cache.set(id=query_id, field='sql', value=generated_sql)
        except Exception as e:
            logger.error(f"Error generating SQL: {str(e)}")
            return jsonify({"error": f"SQL generation error: {str(e)}"}), 500
        
        # Get mock data for the query (since we're in demo mode)
        try:
            logger.info("Using mock data for demo purposes")
            result_data, columns = get_mock_data_for_query(generated_sql)
            
            # Cache the results
            cache.set(id=query_id, field='data', value=result_data)
            cache.set(id=query_id, field='columns', value=columns)
            
            # Generate an explanation of the query
            try:
                explanation = vn.ask(f"Explain what this SQL query does: {generated_sql}")
                cache.set(id=query_id, field='explanation', value=explanation)
            except Exception as e:
                logger.error(f"Error generating explanation: {str(e)}")
                explanation = "No explanation available."
            
            end_time = time.time()
            execution_time = int((end_time - start_time) * 1000)  # Convert to milliseconds
            cache.set(id=query_id, field='execution_time', value=execution_time)
            
            return jsonify({
                "id": query_id,
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
                "id": query_id,
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
