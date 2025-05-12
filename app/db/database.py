import os
import logging
from sqlmodel import create_engine, Session, SQLModel
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv

import app.models.data_models

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

# Get database URL from environment variable
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set")

engine = create_engine(
    DATABASE_URL, 
    echo=False,
    pool_pre_ping=True,  
    pool_recycle=300,    
    pool_size=5,         
    max_overflow=10      
)

def get_db():
    """Database session"""
    db = Session(engine)
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize database with tables"""
    try:
        SQLModel.metadata.create_all(engine)
        logger.info("Database initialized successfully")
    except SQLAlchemyError as e:
        logger.error(f"Database initialization failed: {e}")
        raise 