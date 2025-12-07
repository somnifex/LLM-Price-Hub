import os
from sqlmodel import SQLModel, create_engine, Session
from typing import Generator

# Helper to get DB URL with a fallback for local dev if needed, though docker-compose sets it
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db") 

# connect_args={"check_same_thread": False} is for SQLite only, 
# but for production MySQL we don't need it. 
# We'll check if it's sqlite to add it for local non-docker testing support if necessary.
connect_args = {}
if "sqlite" in DATABASE_URL:
    connect_args = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, echo=True, connect_args=connect_args)

def init_db():
    SQLModel.metadata.create_all(engine)

def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
