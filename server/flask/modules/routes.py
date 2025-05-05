"""
Routes for the Flask application
"""
import os
import time
import traceback
import logging
from flask import request, jsonify, Response
from flask_cors import CORS

from .cache import MemoryCache
from .vanna_client import vanna_client

# Initialize logging
logger = logging.getLogger(__name__)

# Create a cache instance
cache = MemoryCache()

def register_routes(app):
    """Register all the routes for the Flask application"""
    CORS(app)
    
    @app.route('/api/health', methods=['GET'])
    def health_check():
        """Health check endpoint"""
        return jsonify({"status": "ok"})
    
    @app.route('/api/v0/generate_questions', methods=['GET'])
    def generate_questions():
        """Generate example questions"""
        return jsonify({
            "type": "question_list", 
            "questions": vanna_client.generate_questions(),
            "header": "Here are some questions you can ask:"
        })
    
    @app.route('/api/v0/generate_sql', methods=['GET'])
    def generate_sql():
        """Generate SQL from natural language question"""
        question = request.args.get('question')
        
        if question is None:
            return jsonify({"type": "error", "error": "No question provided"})
        
        id = cache.generate_id(question=question)
        sql = vanna_client.generate_sql(question=question)
        
        cache.set(id=id, field='question', value=question)
        cache.set(id=id, field='sql', value=sql)
        
        return jsonify({
            "type": "sql", 
            "id": id,
            "text": sql,
        })
    
    @app.route('/api/v0/run_sql', methods=['GET'])
    def run_sql():
        """Run SQL query"""
        id = request.args.get('id')
        
        if id is None:
            return jsonify({"type": "error", "error": "No id provided"})
        
        sql = cache.get(id=id, field='sql')
        
        if sql is None:
            return jsonify({"type": "error", "error": "No SQL found for this ID"})
        
        try:
            df = vanna_client.run_sql(sql=sql)
            
            cache.set(id=id, field='df', value=df)
            
            return jsonify({
                "type": "df", 
                "id": id,
                "df": df.head(10).to_json(orient='records'),
            })
        except Exception as e:
            return jsonify({"type": "error", "error": str(e)})
    
    @app.route('/api/v0/download_csv', methods=['GET'])
    def download_csv():
        """Download results as CSV"""
        id = request.args.get('id')
        
        if id is None:
            return jsonify({"type": "error", "error": "No id provided"})
        
        df = cache.get(id=id, field='df')
        
        if df is None:
            return jsonify({"type": "error", "error": "No data found for this ID"})
        
        csv = df.to_csv()
        
        return Response(
            csv,
            mimetype="text/csv",
            headers={"Content-disposition": f"attachment; filename={id}.csv"}
        )
    
    @app.route('/api/v0/generate_plotly_figure', methods=['GET'])
    def generate_plotly_figure():
        """Generate Plotly figure for visualization"""
        id = request.args.get('id')
        
        if id is None:
            return jsonify({"type": "error", "error": "No id provided"})
        
        df = cache.get(id=id, field='df')
        question = cache.get(id=id, field='question')
        sql = cache.get(id=id, field='sql')
        
        if df is None or question is None or sql is None:
            return jsonify({"type": "error", "error": "Missing data for this ID"})
        
        try:
            code = vanna_client.generate_plotly_code(
                question=question, 
                sql=sql, 
                df_metadata=f"Running df.dtypes gives:\n {df.dtypes}"
            )
            fig = vanna_client.get_plotly_figure(plotly_code=code, df=df, dark_mode=False)
            fig_json = fig.to_json()
            
            cache.set(id=id, field='fig_json', value=fig_json)
            
            return jsonify({
                "type": "plotly_figure", 
                "id": id,
                "fig": fig_json,
            })
        except Exception as e:
            traceback.print_exc()
            return jsonify({"type": "error", "error": str(e)})
    
    @app.route('/api/v0/get_training_data', methods=['GET'])
    def get_training_data():
        """Get training data"""
        df = vanna_client.get_training_data()
        
        return jsonify({
            "type": "df", 
            "id": "training_data",
            "df": df.head(25).to_json(orient='records'),
        })
    
    @app.route('/api/v0/remove_training_data', methods=['POST'])
    def remove_training_data():
        """Remove training data"""
        id = request.json.get('id')
        
        if id is None:
            return jsonify({"type": "error", "error": "No id provided"})
        
        if vanna_client.remove_training_data(id=id):
            return jsonify({"success": True})
        else:
            return jsonify({"type": "error", "error": "Couldn't remove training data"})
    
    @app.route('/api/v0/train', methods=['POST'])
    def add_training_data():
        """Add training data"""
        question = request.json.get('question')
        sql = request.json.get('sql')
        ddl = request.json.get('ddl')
        documentation = request.json.get('documentation')
        
        try:
            id = vanna_client.train(
                question=question, 
                sql=sql, 
                ddl=ddl, 
                documentation=documentation
            )
            
            return jsonify({"id": id})
        except Exception as e:
            print("TRAINING ERROR", e)
            return jsonify({"type": "error", "error": str(e)})
    
    @app.route('/api/v0/generate_followup_questions', methods=['GET'])
    def generate_followup_questions():
        """Generate followup questions"""
        id = request.args.get('id')
        
        if id is None:
            return jsonify({"type": "error", "error": "No id provided"})
        
        df = cache.get(id=id, field='df')
        question = cache.get(id=id, field='question')
        sql = cache.get(id=id, field='sql')
        
        if df is None or question is None or sql is None:
            return jsonify({"type": "error", "error": "Missing data for this ID"})
        
        followup_questions = vanna_client.generate_followup_questions(
            question=question, 
            sql=sql, 
            df=df
        )
        
        cache.set(id=id, field='followup_questions', value=followup_questions)
        
        return jsonify({
            "type": "question_list", 
            "id": id,
            "questions": followup_questions,
            "header": "Here are some followup questions you can ask:"
        })
    
    @app.route('/api/v0/load_question', methods=['GET'])
    def load_question():
        """Load a question and its results"""
        id = request.args.get('id')
        
        if id is None:
            return jsonify({"type": "error", "error": "No id provided"})
        
        question = cache.get(id=id, field='question')
        sql = cache.get(id=id, field='sql')
        df = cache.get(id=id, field='df')
        fig_json = cache.get(id=id, field='fig_json')
        followup_questions = cache.get(id=id, field='followup_questions')
        
        if question is None or sql is None or df is None or fig_json is None or followup_questions is None:
            return jsonify({"type": "error", "error": "Missing data for this ID"})
        
        try:
            return jsonify({
                "type": "question_cache", 
                "id": id,
                "question": question,
                "sql": sql,
                "df": df.head(10).to_json(orient='records'),
                "fig": fig_json,
                "followup_questions": followup_questions,
            })
        except Exception as e:
            return jsonify({"type": "error", "error": str(e)})
    
    @app.route('/api/v0/get_question_history', methods=['GET'])
    def get_question_history():
        """Get question history"""
        return jsonify({
            "type": "question_history", 
            "questions": cache.get_all(field_list=['question'])
        })
    
    @app.route('/api/examples', methods=['GET'])
    def get_example_questions():
        """Return example questions for the UI"""
        questions = vanna_client.generate_questions()
        return jsonify({"examples": questions})
    
    @app.route('/api/query', methods=['POST'])
    def process_query():
        """Process a natural language query and return SQL and results"""
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        natural_language_query = data.get('query')
        if not natural_language_query:
            return jsonify({"error": "No query provided"}), 400
        
        # Generate a unique ID for this query
        query_id = cache.generate_id(question=natural_language_query)
        
        # Generate SQL from natural language
        try:
            generated_sql = vanna_client.generate_sql(natural_language_query)
            cache.set(id=query_id, field='sql', value=generated_sql)
        except Exception as e:
            return jsonify({"error": f"SQL generation error: {str(e)}"}), 500
        
        # Execute the SQL query
        try:
            df = vanna_client.run_sql(generated_sql)
            
            # Cache the results
            cache.set(id=query_id, field='df', value=df)
            cache.set(id=query_id, field='question', value=natural_language_query)
            
            result_data = df.to_dict(orient='records')
            columns = df.columns.tolist()
            
            # Generate an explanation of the query
            try:
                explanation = f"This query {natural_language_query} returns data about {', '.join(columns)}"
            except Exception:
                explanation = "No explanation available."
            
            return jsonify({
                "id": query_id,
                "sql": generated_sql,
                "data": result_data,
                "columns": columns,
                "explanation": explanation
            })
        except Exception as e:
            return jsonify({
                "id": query_id,
                "sql": generated_sql,
                "error": f"SQL execution error: {str(e)}"
            }), 500
    
    @app.route('/')
    def root():
        return app.send_static_file('index.html')
    
    return app
