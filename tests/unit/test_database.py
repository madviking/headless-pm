"""
Unit tests for database module
"""
import pytest
import os
from sqlmodel import Session, SQLModel, create_engine
from src.models.database import get_database_url, get_session, engine, create_db_and_tables


class TestDatabase:
    """Test database configuration and connection"""
    
    def test_get_database_url_sqlite_default(self):
        """Test getting SQLite database URL with default settings"""
        # Temporarily set environment to use SQLite
        original_db_connection = os.environ.get("DB_CONNECTION")
        os.environ["DB_CONNECTION"] = "sqlite"
        
        try:
            db_url = get_database_url()
            assert db_url is not None
            assert "sqlite" in db_url
        finally:
            # Restore original environment
            if original_db_connection:
                os.environ["DB_CONNECTION"] = original_db_connection
            elif "DB_CONNECTION" in os.environ:
                del os.environ["DB_CONNECTION"]
                
    def test_get_database_url_mysql(self):
        """Test getting MySQL database URL configuration"""
        # Set environment variables for MySQL
        original_values = {}
        mysql_env_vars = {
            "DB_CONNECTION": "mysql",
            "DB_HOST": "localhost",
            "DB_PORT": "3306", 
            "DB_NAME": "test_db",
            "DB_USER": "test_user",
            "DB_PASSWORD": "test_pass"
        }
        
        # Save original values and set test values
        for key, value in mysql_env_vars.items():
            original_values[key] = os.environ.get(key)
            os.environ[key] = value
            
        try:
            db_url = get_database_url()
            assert db_url is not None
            assert "mysql" in db_url
            assert "test_db" in db_url
            assert "test_user" in db_url
        finally:
            # Restore original environment
            for key, original_value in original_values.items():
                if original_value:
                    os.environ[key] = original_value
                elif key in os.environ:
                    del os.environ[key]
                    
    def test_get_session(self):
        """Test getting database session"""
        session_gen = get_session()
        session = next(session_gen)
        assert isinstance(session, Session)
        session.close()
                
    def test_create_db_and_tables(self):
        """Test database table creation"""
        # This should not raise an exception
        create_db_and_tables()
        
    def test_engine_exists(self):
        """Test that engine is created"""
        assert engine is not None
        assert hasattr(engine, 'url')