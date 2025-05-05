"""
Vanna AI client module
"""
import os
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class VannaClient:
    """Vanna AI client wrapper"""
    
    def __init__(self):
        """Initialize the Vanna client"""
        self.client = None
        self.initialize()
        
    def initialize(self):
        """Initialize the Vanna client based on environment variables"""
        try:
            from vanna.remote import VannaDefault
            
            model = os.environ.get('VANNA_MODEL', 'demo')
            api_key = os.environ.get('VANNA_API_KEY', '')
            
            self.client = VannaDefault(model=model, api_key=api_key)
            
            self._connect_to_database()
            
            logger.info(f"Vanna client initialized with model: {model}")
            return True
        except ImportError:
            logger.error("Failed to import Vanna. Make sure it's installed.")
            return False
        except Exception as e:
            logger.error(f"Failed to initialize Vanna client: {str(e)}")
            return False
    
    def _connect_to_database(self):
        """Connect to the database if credentials are provided"""
        db_type = os.environ.get('DB_TYPE')
        
        if not db_type:
            logger.info("No database connection configured")
            return
        
        try:
            if db_type.lower() == 'snowflake':
                self.client.connect_to_snowflake(
                    account=os.environ.get('SNOWFLAKE_ACCOUNT', ''),
                    username=os.environ.get('SNOWFLAKE_USERNAME', ''),
                    password=os.environ.get('SNOWFLAKE_PASSWORD', ''),
                    database=os.environ.get('SNOWFLAKE_DATABASE', ''),
                    warehouse=os.environ.get('SNOWFLAKE_WAREHOUSE', '')
                )
            elif db_type.lower() in ['postgresql', 'postgres']:
                self.client.connect_to_postgres(
                    host=os.environ.get('DB_HOST', 'localhost'),
                    port=int(os.environ.get('DB_PORT', 5432)),
                    user=os.environ.get('DB_USER', 'postgres'),
                    password=os.environ.get('DB_PASSWORD', 'postgres'),
                    database=os.environ.get('DB_NAME', 'postgres')
                )
            
            logger.info(f"Connected to {db_type} database")
        except Exception as e:
            logger.error(f"Failed to connect to database: {str(e)}")
    
    def generate_questions(self):
        """Generate example questions"""
        try:
            return self.client.generate_questions()
        except Exception as e:
            logger.error(f"Error generating questions: {str(e)}")
            return []
    
    def generate_sql(self, question):
        """Generate SQL from natural language question"""
        try:
            return self.client.generate_sql(question=question)
        except Exception as e:
            logger.error(f"Error generating SQL: {str(e)}")
            return ""
    
    def run_sql(self, sql):
        """Run SQL query"""
        try:
            return self.client.run_sql(sql=sql)
        except Exception as e:
            logger.error(f"Error running SQL: {str(e)}")
            raise e
    
    def generate_plotly_code(self, question, sql, df_metadata):
        """Generate Plotly code for visualization"""
        try:
            return self.client.generate_plotly_code(
                question=question, 
                sql=sql, 
                df_metadata=df_metadata
            )
        except Exception as e:
            logger.error(f"Error generating Plotly code: {str(e)}")
            return ""
    
    def get_plotly_figure(self, plotly_code, df, dark_mode=False):
        """Get Plotly figure from code"""
        try:
            return self.client.get_plotly_figure(
                plotly_code=plotly_code, 
                df=df, 
                dark_mode=dark_mode
            )
        except Exception as e:
            logger.error(f"Error getting Plotly figure: {str(e)}")
            raise e
    
    def generate_followup_questions(self, question, sql, df):
        """Generate followup questions"""
        try:
            return self.client.generate_followup_questions(
                question=question, 
                sql=sql, 
                df=df
            )
        except Exception as e:
            logger.error(f"Error generating followup questions: {str(e)}")
            return []
    
    def get_training_data(self):
        """Get training data"""
        try:
            return self.client.get_training_data()
        except Exception as e:
            logger.error(f"Error getting training data: {str(e)}")
            return []
    
    def remove_training_data(self, id):
        """Remove training data"""
        try:
            return self.client.remove_training_data(id=id)
        except Exception as e:
            logger.error(f"Error removing training data: {str(e)}")
            return False
    
    def train(self, question=None, sql=None, ddl=None, documentation=None):
        """Train the model"""
        try:
            return self.client.train(
                question=question, 
                sql=sql, 
                ddl=ddl, 
                documentation=documentation
            )
        except Exception as e:
            logger.error(f"Error training model: {str(e)}")
            raise e

vanna_client = VannaClient()
