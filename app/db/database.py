import os
import logging
from sqlmodel import create_engine, Session, SQLModel
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import event
from sqlalchemy.pool import QueuePool
from dotenv import load_dotenv
import time

import app.models.data_models

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

# Get database URL from environment variable
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set")

# Optimize connection pool settings for Supabase
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {
        "check_same_thread": False,
        "timeout": 20,
    }
elif DATABASE_URL.startswith("postgresql"):
    # Supabase-specific connection arguments
    connect_args = {
        "connect_timeout": 10,
        "application_name": "steadi-app",
        "options": "-c timezone=utc"
    }

engine = create_engine(
    DATABASE_URL, 
    echo=False,
    pool_pre_ping=True,  
    pool_recycle=3600,    # Recycle connections every hour
    pool_size=10,         # Reduced for Supabase limits
    max_overflow=20,      # Reduced for Supabase limits
    pool_timeout=30,      # Timeout for getting connection from pool
    poolclass=QueuePool,  # Use QueuePool for better performance
    connect_args=connect_args
)

# Add query performance monitoring
@event.listens_for(engine, "before_cursor_execute")
def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    context._query_start_time = time.time()

@event.listens_for(engine, "after_cursor_execute")
def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    total = time.time() - context._query_start_time
    if total > 0.5:  # Log slow queries (> 500ms)
        logger.warning(f"Slow query ({total:.3f}s): {statement[:200]}...")

def get_db():
    """Database session with automatic connection management"""
    db = Session(engine)
    try:
        yield db
    except SQLAlchemyError as e:
        logger.error(f"Database error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def init_db():
    """Initialize database with tables"""
    try:
        SQLModel.metadata.create_all(engine)
        logger.info("Database initialized successfully")
        
        # Test connection pool
        with engine.connect() as conn:
            #result = conn.execute("SELECT 1")
            logger.info("Database connection test successful")
            
    except SQLAlchemyError as e:
        logger.error(f"Database initialization failed: {e}")
        raise

# Database health check
def check_db_health():
    """Check database connection health"""
    try:
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False 