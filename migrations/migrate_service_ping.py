"""
Migration script to add ping_url and related fields to Service table
"""

import os
from sqlmodel import create_engine, Session, text
from dotenv import load_dotenv

load_dotenv()

# Get database URL
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./headless-pm.db")

def migrate():
    engine = create_engine(DATABASE_URL)
    
    with Session(engine) as session:
        # Check if we're using SQLite or MySQL
        is_sqlite = "sqlite" in DATABASE_URL.lower()
        
        if is_sqlite:
            # SQLite migrations
            migrations = [
                "ALTER TABLE service ADD COLUMN ping_url TEXT;",
                "ALTER TABLE service ADD COLUMN last_ping_at DATETIME;",
                "ALTER TABLE service ADD COLUMN last_ping_success BOOLEAN;"
            ]
        else:
            # MySQL migrations
            migrations = [
                "ALTER TABLE service ADD COLUMN ping_url VARCHAR(500) NOT NULL DEFAULT '';",
                "ALTER TABLE service ADD COLUMN last_ping_at DATETIME NULL;",
                "ALTER TABLE service ADD COLUMN last_ping_success BOOLEAN NULL;"
            ]
        
        for migration in migrations:
            try:
                session.exec(text(migration))
                print(f"✅ Executed: {migration}")
            except Exception as e:
                print(f"⚠️  Skipped (column may already exist): {migration}")
                print(f"   Error: {e}")
        
        session.commit()
        print("\n✅ Migration completed!")

if __name__ == "__main__":
    migrate()