#!/usr/bin/env python3
"""
Migration script to add connection_type column to agent table.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sqlmodel import Session, create_engine, text
from src.models.database import DATABASE_URL
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate():
    """Add connection_type column to agent table"""
    engine = create_engine(DATABASE_URL)
    
    with Session(engine) as session:
        try:
            # Check if column already exists (MySQL syntax)
            result = session.exec(text("""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = 'agent' 
                AND COLUMN_NAME = 'connection_type'
            """))
            
            if result.first():
                logger.info("Column 'connection_type' already exists in agent table")
                return
            
            # Add the column with default value
            logger.info("Adding connection_type column to agent table...")
            session.exec(text("""
                ALTER TABLE agent 
                ADD COLUMN connection_type VARCHAR(10) DEFAULT 'client'
            """))
            
            # Update existing records to have 'client' as connection_type
            session.exec(text("""
                UPDATE agent 
                SET connection_type = 'client' 
                WHERE connection_type IS NULL
            """))
            
            session.commit()
            logger.info("Migration completed successfully!")
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            session.rollback()
            raise

if __name__ == "__main__":
    migrate()
