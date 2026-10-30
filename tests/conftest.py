"""Pytest configuration and shared fixtures for Basha Pass tests."""

import pytest


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db: None) -> None:
    """Fixture ensuring database access is available for all tests."""
    pass
