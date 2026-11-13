"""
database.py — Database Connection & Session Setup for HospitalOS.

This file connects Python (SQLAlchemy) to our database.
By default it uses SQLite (a single file: hospitalos/hospitalos.db).
Change DATABASE_URL in .env to a PostgreSQL link and the same code works with PostgreSQL.

This is the ONE place the database engine is created. The FastAPI backend, the
seed script and all MCP servers (via mcp_servers/common/db.py) import it from here.
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# hospitalos/ folder (this file lives in hospitalos/backend/)
PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Load hospitalos/.env if it exists. Missing .env is fine: we fall back to defaults.
load_dotenv(PROJECT_ROOT / ".env")

DEFAULT_SQLITE_URL = f"sqlite:///{(PROJECT_ROOT / 'hospitalos.db').as_posix()}"


def resolve_database_url(raw_url: str | None) -> str:
    """
    Return a usable database URL.
    - Empty / missing -> default SQLite file in hospitalos/.
    - Relative SQLite path (e.g. sqlite:///./hospitalos.db) -> anchored to hospitalos/,
      so every program uses the SAME file no matter which folder you start it from.
    """
    url = (raw_url or "").strip()
    if not url:
        return DEFAULT_SQLITE_URL
    prefix = "sqlite:///"
    if url.startswith(prefix) and url != "sqlite:///:memory:":
        path = Path(url[len(prefix):])
        if not path.is_absolute():
            return prefix + (PROJECT_ROOT / path).resolve().as_posix()
    return url


DATABASE_URL = resolve_database_url(os.getenv("DATABASE_URL"))

# SQLite needs check_same_thread=False so FastAPI can use it from several threads.
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

# The engine is the core connection to the database
engine = create_engine(DATABASE_URL, connect_args=connect_args)

# SessionLocal creates a new database "conversation" for each request / tool call
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base is the parent class that all 8 table models inherit from
Base = declarative_base()


def get_db():
    """
    FastAPI dependency: opens a session when a request starts and always
    closes it when the request finishes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
