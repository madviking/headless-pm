#!/usr/bin/env python3
"""
Script to clear SQLAlchemy metadata cache after enum changes
"""

import sys
import os
sys.path.append('/Users/trailo/dev/headless-pm')

from src.models.database import engine
from sqlalchemy import MetaData

def clear_cache():
    """Clear SQLAlchemy metadata cache"""
    print("Clearing SQLAlchemy metadata cache...")
    
    # Clear the existing metadata
    metadata = MetaData()
    metadata.reflect(bind=engine)
    metadata.clear()
    
    # Clear any cached table definitions
    if hasattr(engine, '_metadata'):
        engine._metadata.clear()
    
    # Force garbage collection to clear any cached objects
    import gc
    gc.collect()
    
    print("✅ Metadata cache cleared successfully!")
    print("🔄 Please restart the application now.")

if __name__ == "__main__":
    clear_cache()