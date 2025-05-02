"""
Training functionality for the Flask application
"""
import logging
import hashlib

from .data import get_database_schema, get_database_documentation

# Initialize logging
logger = logging.getLogger(__name__)

def train_with_sample_schema(vn):
    """
    Train the model with real database schema and documentation
    
    Args:
        vn: Vanna client instance
        
    Returns:
        True on success
    """
    # Get schema DDL and documentation from the database
    schema_ddl = get_database_schema()
    table_docs = get_database_documentation()
    
    logger.info(f"Training with {len(schema_ddl)} DDL statements and {len(table_docs)} documentation entries")
    
    # Train with schema DDL statements
    try:
        if hasattr(vn, "chroma_client") and vn.chroma_client:
            logger.info("Using ChromaDB for schema storage")
            for ddl in schema_ddl:
                try:
                    # Store in ChromaDB
                    if hasattr(vn, "ddl_collection"):
                        ddl_id = hashlib.md5(ddl.encode()).hexdigest()
                        vn.ddl_collection.add(documents=[ddl], ids=[ddl_id])
                except Exception as e:
                    logger.error(f"Error storing DDL in ChromaDB: {str(e)}")
                    
            # Store table documentation in ChromaDB
            if hasattr(vn, "documentation_collection"):
                for doc in table_docs:
                    try:
                        doc_id = hashlib.md5(f"{doc['table']}:{doc['description']}".encode()).hexdigest()
                        vn.documentation_collection.add(
                            documents=[doc['description']],
                            metadatas=[{"table": doc['table']}],
                            ids=[doc_id]
                        )
                    except Exception as e:
                        logger.error(f"Error storing documentation in ChromaDB: {str(e)}")
                        
        elif hasattr(vn, "train_ddl") and hasattr(vn, "train_documentation"):
            # For API-based implementations
            for ddl in schema_ddl:
                vn.train_ddl(ddl)
                
            # Train with table documentation
            for doc in table_docs:
                doc_str = f"Table {doc['table']}: {doc['description']}"
                vn.train_documentation(doc_str)
                
    except Exception as e:
        logger.error(f"Error training with schema: {str(e)}")
        
    return True