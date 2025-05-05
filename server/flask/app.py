"""
Flask application for the Vanna AI SQL Assistant

This is the main application file that initializes the Flask app
and registers all the routes. It uses a modular structure with
separate modules for different functionality.
"""
import os
import logging
from flask import Flask
from dotenv import load_dotenv

from modules.routes import register_routes

load_dotenv()

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create the Flask app
app = Flask(__name__, static_url_path='', static_folder='static')
app.config['JSON_SORT_KEYS'] = False

# Register routes
app = register_routes(app)

# Run the app if this file is executed directly
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=True)
