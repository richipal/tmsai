"""
Memory cache for storing query results
"""
import hashlib

class MemoryCache:
    """Simple in-memory cache for storing query results and other data"""
    
    def __init__(self):
        """Initialize an empty cache"""
        self.cache = {}
    
    def generate_id(self, **kwargs):
        """Generate a unique ID based on the input parameters"""
        # Concatenate all parameter values
        concat_str = "".join([str(val) for val in kwargs.values()])
        # Create a hash of the concatenated string
        hash_obj = hashlib.md5(concat_str.encode())
        # Return the hexadecimal digest as the ID
        return hash_obj.hexdigest()
    
    def set(self, id, field, value):
        """Set a value in the cache"""
        # Initialize the ID in the cache if it doesn't exist
        if id not in self.cache:
            self.cache[id] = {}
        # Set the field value
        self.cache[id][field] = value
        return True
    
    def get(self, id, field):
        """Get a value from the cache"""
        # Return None if the ID doesn't exist
        if id not in self.cache:
            return None
        # Return None if the field doesn't exist
        if field not in self.cache[id]:
            return None
        # Return the cached value
        return self.cache[id][field]
    
    def clear(self, id=None):
        """Clear the cache for a specific ID or the entire cache"""
        if id is None:
            # Clear the entire cache
            self.cache = {}
        elif id in self.cache:
            # Clear the cache for the specified ID
            del self.cache[id]
        return True