"""
Routes for the Flask application
"""
import os
import time
import traceback
import logging
from flask import request, jsonify

from .config import DEFAULT_EXAMPLES, REQUESTS_AVAILABLE, VANNA_AVAILABLE
from .cache import MemoryCache
from .data import get_mock_data_for_query
from .training import train_with_sample_schema
from .clients import initialize_vanna_client

# Initialize logging
logger = logging.getLogger(__name__)

# Create a cache instance
cache = MemoryCache()

# Initialize the client
vanna_client, client_type = initialize_vanna_client()
logger.info(f"Using Vanna client: {client_type}")

# Dictionary to store database connections
db_engines = {}

def register_routes(app):
    """Register all the routes for the Flask application"""
    
    @app.route('/api/health', methods=['GET'])
    def health_check():
        """Health check endpoint"""
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
            # Use our singleton vanna client instance
            client = vanna_client
            
            # Check if the client has the method
            if hasattr(client, "get_example_questions"):
                examples = client.get_example_questions()
                logger.info("Successfully fetched example questions")
            else:
                # Fallback to default examples
                examples = DEFAULT_EXAMPLES
                logger.warning("Using default example questions")
                
            return jsonify({"examples": examples})
        except Exception as e:
            logger.error(f"Error fetching example questions: {str(e)}")
            # Fallback to default examples on error
            return jsonify({"examples": DEFAULT_EXAMPLES})
            
    @app.route('/api/training-data', methods=['GET'])
    def get_training_data():
        """Return training data (question-SQL pairs, documentation, DDL)"""
        try:
            # Use our singleton vanna client instance
            client = vanna_client
            
            # Check if the client has the method
            if hasattr(client, "get_training_data"):
                training_data = client.get_training_data()
                logger.info("Successfully fetched training data")
                return jsonify(training_data)
            else:
                # Fall back to default empty response
                return jsonify({
                    "question_sql_pairs": [],
                    "documentation": [],
                    "ddl": []
                })
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
                
            # Use our singleton vanna client instance
            client = vanna_client
            success = False
                
            # Train the model with the provided data
            if 'ddl' in data and hasattr(client, "train_ddl"):
                client.train_ddl(data['ddl'])
                logger.info(f"Trained model with DDL: {data['ddl'][:50]}...")
                success = True
                
            if 'documentation' in data and hasattr(client, "train_documentation"):
                client.train_documentation(data['documentation'])
                logger.info(f"Trained model with documentation for: {data['documentation'][:50]}...")
                success = True
                
            if 'question' in data and 'sql' in data and hasattr(client, "train_question_sql"):
                client.train_question_sql(data['question'], data['sql'])
                logger.info(f"Trained model with question-SQL pair: {data['question']} -> {data['sql'][:30]}...")
                success = True
                
            if success:
                return jsonify({"status": "ok", "message": "Training data added successfully"})
            else:
                return jsonify({"warning": "No training was performed"}), 400
        except Exception as e:
            logger.error(f"Error adding training data: {str(e)}")
            return jsonify({"error": f"Error adding training data: {str(e)}"}), 500
    
    @app.route('/api/query', methods=['POST'])
    def process_query():
        """Process a natural language query and return SQL and results"""
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
            
            # Use our singleton vanna client instance
            client = vanna_client
            
            # Extract database schema information and train the model
            train_with_sample_schema(client)
            
            # Generate SQL from natural language
            try:
                logger.info(f"Generating SQL for query: {natural_language_query}")
                generated_sql = client.generate_sql(natural_language_query)
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
                    logger.info(f"Asking: Explain what this SQL query does: {generated_sql}")
                    explanation = client.ask(f"Explain what this SQL query does: {generated_sql}")
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
            
    return app