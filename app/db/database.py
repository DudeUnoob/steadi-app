import os
import logging
from sqlmodel import create_engine, Session, SQLModel
from sqlalchemy.exc import SQLAlchemyError

import app.models.data_models


import app.models.data_models


logger = logging.getLogger(__name__)


DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    
)


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