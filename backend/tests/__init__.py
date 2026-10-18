"""
backend/tests package initialiser.

Ensures that the backend/ directory is on sys.path so that test modules can
import application code (app, database, *_service, etc.) with bare names,
regardless of which working directory unittest discover is launched from.
"""
import sys
import os

# Insert the backend/ directory (parent of this tests/ package) at the front
# of sys.path so every test file can do `import app`, `import database`, etc.
_backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

import shutil
import tempfile
import atexit

# Test Database Isolation:
# Creates a temporary isolated copy of foodverse.db (or initializes an empty one if absent)
# and points FOODVERSE_DB_PATH to it so tests NEVER mutate the production database.
_prod_db = os.path.join(_backend_dir, "foodverse.db")
_test_tmp_dir = tempfile.mkdtemp(prefix="foodverse_test_db_")
_test_db_path = os.path.join(_test_tmp_dir, "foodverse.test.db")

if os.path.exists(_prod_db):
    shutil.copy2(_prod_db, _test_db_path)

os.environ["FOODVERSE_DB_PATH"] = _test_db_path

def _cleanup_test_db():
    try:
        if os.path.exists(_test_tmp_dir):
            shutil.rmtree(_test_tmp_dir, ignore_errors=True)
    except Exception:
        pass

atexit.register(_cleanup_test_db)

