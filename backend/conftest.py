import pytest


@pytest.fixture
def anyio_backend():
    """
    Configures pytest-anyio to run async tests exclusively against the asyncio backend,
    preventing missing 'trio' dependency errors in CI runner environments.
    """
    return "asyncio"
