import os
import logging
from sqlmodel import SQLModel, create_engine, Session
from typing import Generator

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")

connect_args = {}
if "sqlite" in DATABASE_URL:
    # SQLite specific configuration
    connect_args = {"check_same_thread": False}

ECHO_SQL = os.getenv("ECHO_SQL", "False").lower() == "true"
engine = create_engine(DATABASE_URL, echo=ECHO_SQL, connect_args=connect_args)

logger = logging.getLogger("llm_price_hub.database")


def init_db():
    # Import models to ensure they are registered on the metadata
    from app import models
    import time
    from sqlalchemy.exc import OperationalError

    logger.info("Creating or ensuring database tables exist")

    max_retries = 10
    retry_interval = 3

    for i in range(max_retries):
        try:
            SQLModel.metadata.create_all(engine)
            logger.info("Database tables created successfully.")
            return
        except OperationalError as e:
            if i < max_retries - 1:
                logger.warning(
                    "Database connection failed, retrying in %s seconds... (%d/%d)",
                    retry_interval,
                    i + 1,
                    max_retries,
                )
                logger.debug("OperationalError: %s", e)
                time.sleep(retry_interval)
            else:
                logger.error("Failed to connect to database after multiple retries.")
                raise e


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
