#!/usr/bin/env python3
"""
Migration script to convert VARCHAR(255) columns to TEXT type for better description storage.
This preserves all existing data while expanding the column capacity.
"""

import os
import sys
from sqlalchemy import create_engine, text
from datetime import datetime

def get_database_url():
    """Get database URL from environment or construct from .env file"""
    if os.getenv("DATABASE_URL"):
        return os.getenv("DATABASE_URL")
    
    # Try to load from .env file
    try:
        with open('../.env', 'r') as f:
            env_vars = {}
            for line in f:
                line = line.strip()
                if '=' in line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    # Remove quotes and comments
                    value = value.split('#')[0].strip().strip('"')
                    env_vars[key] = value
        
        if env_vars.get('DB_CONNECTION') == 'mysql':
            host = env_vars.get('DB_HOST', 'localhost')
            port = env_vars.get('DB_PORT', '3306')
            user = env_vars.get('DB_USER', 'root')
            password = env_vars.get('DB_PASSWORD', '')
            db_name = env_vars.get('DB_NAME', 'headless_pm')
            url = f"mysql+pymysql://{user}:{password}@{host}:{port}/{db_name}"
            return url
    except FileNotFoundError:
        pass
    return "sqlite:///./headless-pm.db"

def migrate_to_text_columns():
    """Convert VARCHAR(255) columns to TEXT type"""
    db_url = get_database_url()
    engine = create_engine(db_url)
    
    print(f"Migrating database: {db_url}")
    print(f"Started at: {datetime.now()}")
    
    # For SQLite, we need to recreate tables since ALTER COLUMN is limited
    # For MySQL/PostgreSQL, we can use ALTER TABLE directly
    
    if "mysql" in db_url or "postgresql" in db_url:
        print(f"\nMySQL/PostgreSQL detected - using ALTER TABLE approach")
        migrate_mysql_postgres(engine)
    else:
        print(f"\nSQLite detected - using table recreation approach")
        migrate_sqlite(engine)
    
    print(f"\nMigration completed at: {datetime.now()}")

def migrate_sqlite(engine):
    """SQLite migration using table recreation"""
    with engine.begin() as conn:
        # Enable foreign keys
        conn.execute(text("PRAGMA foreign_keys=OFF"))
        
        # List of tables and columns to migrate
        migrations = [
            ("epic", "description"),
            ("feature", "description"),
            ("task", "description"),
            ("task", "notes"),
            ("taskevaluation", "comment"),
            ("changelog", "notes"),
            ("document", "content")
        ]
        
        for table, column in migrations:
            print(f"\nMigrating {table}.{column} to TEXT...")
            
            # Get current table schema
            result = conn.execute(text(f"PRAGMA table_info({table})"))
            columns = result.fetchall()
            
            # Create new table with TEXT type
            create_stmt = f"CREATE TABLE {table}_new ("
            col_defs = []
            
            for col in columns:
                col_name = col[1]
                col_type = col[2]
                col_notnull = col[3]
                col_default = col[4]
                col_pk = col[5]
                
                # Change VARCHAR to TEXT for our target column
                if col_name == column and "VARCHAR" in col_type.upper():
                    col_type = "TEXT"
                
                col_def = f"{col_name} {col_type}"
                if col_pk:
                    col_def += " PRIMARY KEY"
                if col_notnull and not col_pk:
                    col_def += " NOT NULL"
                if col_default is not None:
                    col_def += f" DEFAULT {col_default}"
                
                col_defs.append(col_def)
            
            create_stmt += ", ".join(col_defs) + ")"
            
            # Create new table
            conn.execute(text(create_stmt))
            
            # Copy data
            conn.execute(text(f"INSERT INTO {table}_new SELECT * FROM {table}"))
            
            # Drop old table and rename new
            conn.execute(text(f"DROP TABLE {table}"))
            conn.execute(text(f"ALTER TABLE {table}_new RENAME TO {table}"))
            
            print(f"✓ Migrated {table}.{column}")
        
        # Re-enable foreign keys
        conn.execute(text("PRAGMA foreign_keys=ON"))

def migrate_mysql_postgres(engine):
    """MySQL/PostgreSQL migration using ALTER TABLE"""
    with engine.begin() as conn:
        migrations = [
            ("epic", "description"),
            ("feature", "description"),
            ("task", "description"),
            ("task", "notes"),
            ("taskevaluation", "comment"),
            ("changelog", "notes"),
            ("document", "content")
        ]
        
        for table, column in migrations:
            print(f"\nMigrating {table}.{column} to TEXT...")
            
            if "mysql" in engine.dialect.name:
                # MySQL syntax
                conn.execute(text(f"ALTER TABLE {table} MODIFY COLUMN {column} TEXT"))
            else:
                # PostgreSQL syntax
                conn.execute(text(f"ALTER TABLE {table} ALTER COLUMN {column} TYPE TEXT"))
            
            print(f"✓ Migrated {table}.{column}")

if __name__ == "__main__":
    try:
        migrate_to_text_columns()
        print("\n✅ Migration completed successfully!")
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        sys.exit(1)
