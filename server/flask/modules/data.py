"""
Data generation and retrieval functionality for the Flask application.
"""
import logging
from .northwind_db import northwind_db

# Initialize logging
logger = logging.getLogger(__name__)

def execute_query(sql_query):
    """
    Execute a SQL query against the Northwind database
    
    Args:
        sql_query: SQL query to execute
        
    Returns:
        Tuple of (results, column_names)
    """
    try:
        # Use the Northwind database connection to execute the query
        logger.info(f"Executing SQL query: {sql_query[:100]}...")
        return northwind_db.execute_query(sql_query)
    except Exception as e:
        logger.error(f"Error executing SQL query: {str(e)}")
        # Return empty result if there's an error
        return get_empty_result(sql_query)

def get_empty_result(sql_query):
    """
    Returns empty result set when database query fails
    
    Args:
        sql_query: SQL query that failed
        
    Returns:
        Tuple of (empty_data, basic_columns)
    """
    logger.error(f"Query failed, returning empty result: {sql_query[:100]}...")
    return [], ["error"]

def get_database_schema():
    """
    Get the Northwind database schema as DDL statements
    
    Returns:
        List of DDL statements
    """
    try:
        return northwind_db.get_schema_ddl()
    except Exception as e:
        logger.error(f"Error getting database schema: {str(e)}")
        # Fallback to default schema from config
        from .config import NORTHWIND_SCHEMA
        return NORTHWIND_SCHEMA

def get_database_documentation():
    """
    Get documentation for tables in the Northwind database
    
    Returns:
        List of table documentation dictionaries
    """
    try:
        return northwind_db.get_database_documentation()
    except Exception as e:
        logger.error(f"Error getting database documentation: {str(e)}")
        # Return empty list as fallback
        return []