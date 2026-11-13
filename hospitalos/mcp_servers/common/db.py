"""
mcp_servers/common/db.py — Shared Database Access Helper for all MCP servers.

Why does this file exist?
Instead of copy-pasting database connection code into every MCP server
(beds, patients, appointments, pharmacy, lab, billing), they all import
`get_db_session` and `models` from here.

1. Adds the hospitalos/ folder to sys.path, so `import backend` works no matter
   where the server is started from.
2. Reuses the engine from backend/database.py (one place decides which database
   file/URL is used, so the API and all servers always share the same data).
3. `get_db_session()` opens a session, rolls back on error, and always closes it.
"""

import sys
from contextlib import contextmanager
from pathlib import Path

HOSPITALOS_ROOT = Path(__file__).resolve().parents[2]
if str(HOSPITALOS_ROOT) not in sys.path:
    sys.path.insert(0, str(HOSPITALOS_ROOT))

from backend import models  # noqa: E402
from backend.database import Base, DATABASE_URL, SessionLocal, engine  # noqa: E402

# Make sure all 8 tables exist (an empty database then gives "not found" answers, not crashes)
Base.metadata.create_all(bind=engine)


@contextmanager
def get_db_session():
    """
    Context manager that yields a SQLAlchemy database session.

    Example inside an MCP tool:
        with get_db_session() as db:
            patient = db.query(models.Patient).filter_by(id=1).first()
    """
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


__all__ = ["get_db_session", "models", "engine", "HOSPITALOS_ROOT", "DATABASE_URL"]
