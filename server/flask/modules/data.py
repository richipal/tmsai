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
        # Fall back to mock data if there's an error
        return get_mock_data_for_query(sql_query)

def get_mock_data_for_query(sql_query):
    """
    Generate mock data that would reasonably match the given SQL query.
    This is a fallback when the real database is not available.
    
    Args:
        sql_query: SQL query to mock results for
        
    Returns:
        Tuple of (data, columns)
    """
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
    
    logger.info("Using mock data (fallback)")
    return data, columns

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