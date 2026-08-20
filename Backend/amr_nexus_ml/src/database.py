import sys
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from src.core.config import settings
from src.utils.logger import logger

try:
    engine = create_engine(
        url=settings.DATABASE_URL,
        pool_size=20,
        max_overflow=10,
        pool_timeout=30,
        pool_recycle=1800,
        pool_pre_ping=True,
    )
    SessionLocal = sessionmaker(
        autocommit=False, 
        autoflush=False, 
        bind=engine
    )
    Base = declarative_base()
except Exception as e:
    logger.critical(f"Database connection engine instantiation failed: {str(e)}")
    sys.exit(1)


def get_db() -> Generator[Session, None, None]:
    db: Session = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session boundary error intercepted: {str(e)}")
        raise
    finally:
        db.close()
