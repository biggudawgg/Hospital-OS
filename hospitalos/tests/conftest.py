"""
tests/conftest.py — Shared pytest setup (runs before any test file).

1. Points DATABASE_URL at a TEMPORARY database, so tests never touch your real hospitalos.db.
2. Seeds it once and keeps a clean copy ("pristine").
3. Before EVERY test, copies the clean database back, so each test starts from the same data.
"""

import os
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TMP_DIR = Path(tempfile.mkdtemp(prefix="hospitalos_test_"))
TEST_DB = TMP_DIR / "test.db"
PRISTINE_DB = TMP_DIR / "pristine.db"
TEST_DB_URL = f"sqlite:///{TEST_DB.as_posix()}"

# Must happen BEFORE importing backend / mcp_servers (they read DATABASE_URL at import time)
os.environ["DATABASE_URL"] = TEST_DB_URL
os.environ["HOSPITALOS_DISABLE_MCP"] = "1"     # API tests don't start MCP subprocesses
sys.path.insert(0, str(ROOT))

import pytest  # noqa: E402

from backend.database import engine  # noqa: E402
from data.seed import seed_database  # noqa: E402

seed_database()
engine.dispose()
shutil.copy(TEST_DB, PRISTINE_DB)


@pytest.fixture(autouse=True)
def fresh_db():
    """Restore the clean seeded database before each test."""
    engine.dispose()                 # close open connections so the file can be replaced
    shutil.copy(PRISTINE_DB, TEST_DB)
    yield
