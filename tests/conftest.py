import os
import pytest
from db.db import init_db
from db.models import get_engine, metadata

# CoPilot helped guide through monkey patch use.


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    # Create a temporary directory and override DB_FILE
    test_db = tmp_path / "data_cleaning.db"
    monkeypatch.setattr("db.models.DB_FILE", str(test_db))
    # Ensure no DB exists
    if os.path.exists(test_db):
        os.remove(test_db)
    # Initialize fresh DB
    init_db()
    # File should now exist
    assert os.path.exists(test_db)
    # Re-bind SQLAlchemy engine to this file
    engine = get_engine()  # first call will pick up patched DB_FILE
    metadata.create_all(engine)
    # Ensure connection to new path
    yield str(test_db)
