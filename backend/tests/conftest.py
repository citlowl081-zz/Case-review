"""Pytest configuration — asyncio mode for async tests."""
import pytest

pytest_plugins = ["pytest_asyncio"]


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"
