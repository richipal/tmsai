"""
Training functionality for the Flask application
"""
import logging
import hashlib

from .config import MOCK_TABLES

# Initialize logging
logger = logging.getLogger(__name__)

def train_with_sample_schema(vn):
    """Train the model with sample schema information"""
    # Try to train with sample tables
    try:
        if hasattr(vn, "chroma_client") and vn.chroma_client:
            logger.info("Using ChromaDB for schema storage")
            for ddl in MOCK_TABLES:
                try:
                    # This will only store locally in ChromaDB
                    if hasattr(vn, "ddl_collection"):
                        ddl_id = hashlib.md5(ddl.encode()).hexdigest()
                        vn.ddl_collection.add(documents=[ddl], ids=[ddl_id])
                except Exception as e:
                    logger.error(f"Error storing DDL in ChromaDB: {str(e)}")
        elif hasattr(vn, "train_ddl"):
            # For API-based implementations
            for ddl in MOCK_TABLES:
                vn.train_ddl(ddl)
    except Exception as e:
        logger.error(f"Error training with sample schema: {str(e)}")
        
    return True