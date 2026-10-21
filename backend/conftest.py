"""
Root pytest conftest — shared fixtures will be added here as apps are built.
"""
import django
import pytest


@pytest.fixture(scope="session")
def django_db_setup():
    """Use in-memory SQLite for tests."""
    pass
