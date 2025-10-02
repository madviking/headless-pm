from sqlmodel import SQLModel, create_engine, Session
from typing import Generator
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def get_database_url() -> str:
    """Get database URL based on DB_CONNECTION setting in .env"""
    db_connection = os.getenv("DB_CONNECTION", "sqlite").lower()
    
    if db_connection == "mysql":
        db_host = os.getenv("DB_HOST", "localhost")
        db_port = os.getenv("DB_PORT", "3306")
        db_name = os.getenv("DB_NAME", "headless_pm")
        db_user = os.getenv("DB_USER", "root")
        db_password = os.getenv("DB_PASSWORD", "")
        return f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    else:
        # Default to SQLite
        return os.getenv("DATABASE_URL", "sqlite:///./headless-pm.db")

DATABASE_URL = get_database_url()

engine = create_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session