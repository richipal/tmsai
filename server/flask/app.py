from flask import Flask, request, jsonify
from flask_cors import CORS
import vanna
import sqlalchemy
import pandas as pd
import traceback
import time
import os
import logging

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Vanna AI with API key from environment variable
VANNA_API_KEY = os.environ.get('VANNA_API_KEY', '')
if not VANNA_API_KEY:
    logger.warning("VANNA_API_KEY not set in environment variables")

# Create a dictionary to store database connections
db_engines = {}

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok", "vanna_initialized": bool(VANNA_API_KEY)})

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
        
        # Initialize Vanna AI with the API key
        vn = vanna.Vanna()
        if VANNA_API_KEY:
            vn.set_openai_key(VANNA_API_KEY)
        
        # Extract database schema information
        try:
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
        
        # Execute the generated SQL
        try:
            df = pd.read_sql(generated_sql, engine)
            result_data = df.to_dict(orient='records')
            
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
                "columns": df.columns.tolist(),
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
