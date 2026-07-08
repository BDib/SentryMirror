import pytest
import os

@pytest.fixture
def temp_db():
    db_name = "test_temp.db"
    yield db_name
    if os.path.exists(db_name):
        os.remove(db_name)

