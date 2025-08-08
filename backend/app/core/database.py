"""Database configuration and session management."""

import logging
from typing import Generator, Optional
from contextlib import contextmanager

from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
import redis
from redis.exceptions import RedisError

from app.core.config import settings

logger = logging.getLogger(__name__)

# PostgreSQL Database Configuration
def create_database_engine():
    """Create database engine with proper configuration."""
    try:
        engine = create_engine(
            settings.DATABASE_URL,
            pool_pre_ping=True,
            pool_recycle=300,
            pool_size=10,
            max_overflow=20,
            echo=settings.DEBUG,
            connect_args={
                "connect_timeout": 10,
                "application_name": "supermon"
            }
        )
        
        # Add event listeners for debugging
        if settings.DEBUG:
            @event.listens_for(engine, "connect")
            def set_sqlite_pragma(dbapi_connection, connection_record):
                """Set SQLite pragmas for better performance."""
                if "sqlite" in settings.DATABASE_URL:
                    cursor = dbapi_connection.cursor()
                    cursor.execute("PRAGMA journal_mode=WAL")
                    cursor.execute("PRAGMA synchronous=NORMAL")
                    cursor.execute("PRAGMA cache_size=10000")
                    cursor.execute("PRAGMA temp_store=MEMORY")
                    cursor.close()
        
        return engine
    except Exception as e:
        logger.error(f"Failed to create database engine: {e}")
        raise


# Create engine and session factory
try:
    engine = create_database_engine()
    SessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
        expire_on_commit=False
    )
    Base = declarative_base()
except Exception as e:
    logger.error(f"Database initialization failed: {e}")
    raise

# Redis Configuration
def create_redis_client():
    """Create Redis client with proper configuration."""
    try:
        client = redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True,
            health_check_interval=30
        )
        
        # Test connection
        client.ping()
        logger.info("Redis connection established")
        return client
    except RedisError as e:
        logger.error(f"Failed to connect to Redis: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error connecting to Redis: {e}")
        raise


# Create Redis client
try:
    redis_client = create_redis_client()
except Exception as e:
    logger.warning(f"Redis connection failed: {e}")
    redis_client = None


def get_db() -> Generator[Session, None, None]:
    """Dependency to get database session with proper error handling."""
    db = SessionLocal()
    try:
        yield db
    except SQLAlchemyError as e:
        logger.error(f"Database error: {e}")
        db.rollback()
        raise
    except Exception as e:
        logger.error(f"Unexpected database error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def get_redis():
    """Dependency to get Redis client."""
    if redis_client is None:
        raise RuntimeError("Redis client not available")
    return redis_client


@contextmanager
def get_db_session():
    """Context manager for database sessions."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_db() -> None:
    """Initialize database tables with error handling."""
    try:
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except SQLAlchemyError as e:
        logger.error(f"Failed to create database tables: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during database initialization: {e}")
        raise


def check_db_connection() -> bool:
    """Check if database connection is working."""
    try:
        with engine.connect() as connection:
            connection.execute("SELECT 1")
        return True
    except Exception as e:
        logger.error(f"Database connection check failed: {e}")
        return False


def check_redis_connection() -> bool:
    """Check if Redis connection is working."""
    if redis_client is None:
        return False
    
    try:
        redis_client.ping()
        return True
    except Exception as e:
        logger.error(f"Redis connection check failed: {e}")
        return False


def get_connection_info() -> dict:
    """Get database and Redis connection information."""
    return {
        "database": {
            "connected": check_db_connection(),
            "url": settings.DATABASE_URL.replace(
                settings.DATABASE_URL.split("@")[0].split(":")[-1],
                "***"
            ) if "@" in settings.DATABASE_URL else settings.DATABASE_URL
        },
        "redis": {
            "connected": check_redis_connection(),
            "url": settings.REDIS_URL
        }
    }


def close_connections() -> None:
    """Close all database and Redis connections."""
    try:
        if engine:
            engine.dispose()
        if redis_client:
            redis_client.close()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error closing connections: {e}") 