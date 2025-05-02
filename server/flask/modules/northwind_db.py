"""
Northwind database module for accessing real PostgreSQL data
"""
import os
import json
import logging
import time
from typing import List, Dict, Any, Optional, Tuple

# Initialize logging
logger = logging.getLogger(__name__)

# Try to import psycopg to connect to PostgreSQL
try:
    import psycopg
    PSYCOPG_AVAILABLE = True
    logger.info("psycopg is available for PostgreSQL connections")
except ImportError:
    PSYCOPG_AVAILABLE = False
    logger.warning("psycopg not available, using mock data")

# Database connection details from environment
DB_URL = os.environ.get("DATABASE_URL")

# Tables in the Northwind database
NORTHWIND_TABLES = [
    "categories",
    "customers", 
    "employees",
    "suppliers",
    "products",
    "shippers",
    "orders",
    "order_details"
]

class NorthwindDB:
    """
    Class for interacting with the Northwind PostgreSQL database
    """
    def __init__(self):
        """Initialize the database connection"""
        self.connection = None
        self.last_connection_attempt = 0
        self.connection_retry_interval = 5  # seconds
        self._connect()
    
    def _connect(self) -> bool:
        """Connect to the PostgreSQL database"""
        # If we recently tried to connect and failed, don't try again immediately
        current_time = time.time()
        if current_time - self.last_connection_attempt < self.connection_retry_interval:
            return False
        
        self.last_connection_attempt = current_time
        
        # Close any existing connection that might be stale
        self._close_connection()
        
        if not PSYCOPG_AVAILABLE or not DB_URL:
            logger.warning("Cannot connect to PostgreSQL: missing dependencies or connection string")
            return False
        
        try:
            # Create autocommit connection to avoid transaction issues
            self.connection = psycopg.connect(DB_URL, autocommit=True)
            logger.info("Successfully connected to PostgreSQL database")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {str(e)}")
            self.connection = None
            return False
    
    def _close_connection(self):
        """Close the current connection if it exists"""
        if self.connection:
            try:
                self.connection.close()
                logger.debug("Closed existing database connection")
            except Exception as e:
                logger.warning(f"Error closing connection: {str(e)}")
            self.connection = None
    
    def execute_query(self, sql: str) -> Tuple[List[Dict[str, Any]], List[str]]:
        """
        Execute a SQL query and return results
        
        Args:
            sql: SQL query to execute
            
        Returns:
            Tuple of (results, column_names)
        """
        # Try to ensure we have a valid connection
        if not self.connection:
            if not self._connect():
                # Return empty result if connection fails
                return self._get_empty_result(sql)
        
        try:
            # Record start time for query execution
            start_time = time.time()
            
            try:
                # First attempt with existing connection
                with self.connection.cursor() as cursor:
                    cursor.execute(sql)
                    
                    # Get column names
                    columns = [desc[0] for desc in cursor.description] if cursor.description else []
                    
                    # Fetch all rows
                    rows = cursor.fetchall()
                    
                    # Convert rows to dictionaries
                    results = []
                    for row in rows:
                        result_dict = {}
                        for i, column_name in enumerate(columns):
                            value = row[i]
                            # Convert non-serializable types to strings
                            if hasattr(value, 'isoformat'):  # For dates and times
                                value = value.isoformat()
                            result_dict[column_name] = value
                        results.append(result_dict)
                    
                    # Calculate execution time
                    execution_time = int((time.time() - start_time) * 1000)  # Convert to milliseconds
                    logger.info(f"Query executed in {execution_time}ms: {sql[:100]}...")
                    
                    return results, columns
            except Exception as e:
                # If the connection is closed, try to reconnect once
                if "connection is closed" in str(e) or "terminating connection" in str(e):
                    logger.warning(f"Connection issue: {str(e)}. Attempting to reconnect...")
                    
                    # Try to reconnect
                    if self._connect():
                        # Retry the query with the new connection
                        with self.connection.cursor() as cursor:
                            cursor.execute(sql)
                            
                            # Get column names
                            columns = [desc[0] for desc in cursor.description] if cursor.description else []
                            
                            # Fetch all rows
                            rows = cursor.fetchall()
                            
                            # Convert rows to dictionaries
                            results = []
                            for row in rows:
                                result_dict = {}
                                for i, column_name in enumerate(columns):
                                    value = row[i]
                                    # Convert non-serializable types to strings
                                    if hasattr(value, 'isoformat'):  # For dates and times
                                        value = value.isoformat()
                                    result_dict[column_name] = value
                                results.append(result_dict)
                            
                            # Calculate execution time
                            execution_time = int((time.time() - start_time) * 1000)  # Convert to milliseconds
                            logger.info(f"Query executed in {execution_time}ms after reconnection: {sql[:100]}...")
                            
                            return results, columns
                    else:
                        # Reconnection failed
                        logger.error("Failed to reconnect to database")
                        return self._get_empty_result(sql)
                else:
                    # It's not a connection issue, so re-raise
                    raise
                        
        except Exception as e:
            logger.error(f"Error executing query: {str(e)}")
            logger.error(f"SQL: {sql}")
            # Return empty result on error
            return self._get_empty_result(sql)
    
    def get_table_schema(self, table_name: str) -> List[Dict[str, Any]]:
        """
        Get schema information for a table
        
        Args:
            table_name: Name of the table
            
        Returns:
            List of column information dictionaries
        """
        if not self.connection:
            if not self._connect():
                return []
        
        try:
            schema_query = """
            SELECT 
                column_name, 
                data_type, 
                is_nullable, 
                column_default
            FROM 
                information_schema.columns
            WHERE 
                table_name = %s
            ORDER BY 
                ordinal_position
            """
            
            with self.connection.cursor() as cursor:
                cursor.execute(schema_query, (table_name,))
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
                
                schema_info = []
                for row in rows:
                    schema_dict = {}
                    for i, column_name in enumerate(columns):
                        schema_dict[column_name] = row[i]
                    schema_info.append(schema_dict)
                
                return schema_info
        except Exception as e:
            logger.error(f"Error getting schema for {table_name}: {str(e)}")
            return []
    
    def get_table_relationships(self) -> List[Dict[str, str]]:
        """
        Get foreign key relationships between tables
        
        Returns:
            List of relationship dictionaries
        """
        if not self.connection:
            if not self._connect():
                return []
        
        try:
            relationships_query = """
            SELECT
                tc.table_name AS table_name,
                kcu.column_name AS column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name
            FROM
                information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                    ON tc.constraint_name = kcu.constraint_name
                    AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage AS ccu
                    ON ccu.constraint_name = tc.constraint_name
                    AND ccu.table_schema = tc.table_schema
            WHERE
                tc.constraint_type = 'FOREIGN KEY'
            """
            
            with self.connection.cursor() as cursor:
                cursor.execute(relationships_query)
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
                
                relationships = []
                for row in rows:
                    rel_dict = {}
                    for i, column_name in enumerate(columns):
                        rel_dict[column_name] = row[i]
                    relationships.append(rel_dict)
                
                return relationships
        except Exception as e:
            logger.error(f"Error getting relationships: {str(e)}")
            return []
    
    def check_table_exists(self, table_name: str) -> bool:
        """
        Check if a table exists in the database
        
        Args:
            table_name: Name of the table to check
            
        Returns:
            True if the table exists, False otherwise
        """
        if not self.connection:
            if not self._connect():
                return False
        
        try:
            exists_query = """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = %s
            )
            """
            
            with self.connection.cursor() as cursor:
                cursor.execute(exists_query, (table_name,))
                return cursor.fetchone()[0]
        except Exception as e:
            logger.error(f"Error checking if table {table_name} exists: {str(e)}")
            return False
    
    def get_schema_ddl(self) -> List[str]:
        """
        Get DDL statements for all Northwind tables
        
        Returns:
            List of DDL statements
        """
        ddl_statements = []
        
        for table in NORTHWIND_TABLES:
            if self.check_table_exists(table):
                schema_info = self.get_table_schema(table)
                if schema_info:
                    column_defs = []
                    for column in schema_info:
                        column_name = column["column_name"]
                        data_type = column["data_type"]
                        nullable = "NULL" if column["is_nullable"] == "YES" else "NOT NULL"
                        column_defs.append(f"{column_name} {data_type} {nullable}")
                    
                    ddl = f"CREATE TABLE {table} (\n  " + ",\n  ".join(column_defs) + "\n);"
                    ddl_statements.append(ddl)
        
        # Add relationship information
        relationships = self.get_table_relationships()
        for rel in relationships:
            fk_statement = f"""
            ALTER TABLE {rel['table_name']} 
            ADD FOREIGN KEY ({rel['column_name']}) 
            REFERENCES {rel['foreign_table_name']}({rel['foreign_column_name']});
            """
            ddl_statements.append(fk_statement.strip())
        
        return ddl_statements
    
    def get_database_documentation(self) -> List[Dict[str, str]]:
        """
        Generate documentation for all tables
        
        Returns:
            List of table documentation dictionaries
        """
        documentation = []
        
        for table in NORTHWIND_TABLES:
            if self.check_table_exists(table):
                # Get primary key columns
                pk_query = """
                SELECT a.attname
                FROM   pg_index i
                JOIN   pg_attribute a ON a.attrelid = i.indrelid
                                    AND a.attnum = ANY(i.indkey)
                WHERE  i.indrelid = %s::regclass
                AND    i.indisprimary
                """
                
                pk_columns = []
                try:
                    with self.connection.cursor() as cursor:
                        cursor.execute(pk_query, (table,))
                        pk_columns = [row[0] for row in cursor.fetchall()]
                except Exception:
                    pass
                
                # Generate description based on table name
                description = ""
                if table == "categories":
                    description = "Contains product categories with names and descriptions. Primary key is category_id."
                elif table == "customers":
                    description = "Contains customer information including company name, contact person, and address details. Primary key is customer_id."
                elif table == "employees":
                    description = "Contains employee information including personal details, title, and reporting structure. Primary key is employee_id."
                elif table == "suppliers":
                    description = "Contains supplier information including company name, contact person, and address details. Primary key is supplier_id."
                elif table == "products":
                    description = "Contains product information including name, supplier, category, pricing, and inventory details. Primary key is product_id."
                elif table == "shippers":
                    description = "Contains shipping company information. Primary key is shipper_id."
                elif table == "orders":
                    description = "Contains order header information including customer, employee, order date, and shipping details. Primary key is order_id."
                elif table == "order_details":
                    description = "Contains order line items with product, quantity, price, and discount information. Composite primary key (order_id, product_id)."
                else:
                    pk_info = f"Primary key: {', '.join(pk_columns)}" if pk_columns else ""
                    description = f"Contains {table} data. {pk_info}"
                
                documentation.append({
                    "table": table,
                    "description": description
                })
        
        return documentation
    
    def _get_empty_result(self, sql: str) -> Tuple[List[Dict[str, Any]], List[str]]:
        """
        Return empty result when database is unavailable
        
        Args:
            sql: SQL query
            
        Returns:
            Tuple of (empty_results, basic_columns)
        """
        logger.error(f"Database unavailable for query: {sql[:100]}...")
        
        # Return empty result set
        return [], ["error"]

# Singleton instance
northwind_db = NorthwindDB()