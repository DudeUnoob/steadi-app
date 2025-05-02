import os
import logging
from sqlmodel import create_engine, Session, SQLModel
from sqlalchemy.exc import SQLAlchemyError

# Set up logging
logger = logging.getLogger(__name__)

# Get database URL from environment variables
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://neondb_owner:npg_fJaKY45kiMbh@ep-red-butterfly-a4516s6r-pooler.us-east-1.aws.neon.tech/neondb?sslmode=require"
)

# Create SQLAlchemy engine with connection pooling configuration
engine = create_engine(
    DATABASE_URL, 
    echo=False,
    pool_pre_ping=True,  # Test connections before using them
    pool_recycle=300,    # Recycle connections every 5 minutes
    pool_size=5,         # Maximum pool size
    max_overflow=10      # Allow up to 10 extra connections
)

def get_db():
    """Database session dependency"""
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