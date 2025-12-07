import os
from sqlmodel import SQLModel, create_engine, Session
from typing import Generator

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db") 

connect_args = {}
if "sqlite" in DATABASE_URL:
    # SQLite specific configuration
    connect_args = {"check_same_thread": False}

ECHO_SQL = os.getenv("ECHO_SQL", "False").lower() == "true"
engine = create_engine(DATABASE_URL, echo=ECHO_SQL, connect_args=connect_args)

def init_db():
    SQLModel.metadata.create_all(engine)

def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
