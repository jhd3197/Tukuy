import pytest
from tukuy import TukuyTransformer
from tukuy.registry import reset_shared_registry
from tukuy.core.unified import reset_unified_registry


@pytest.fixture(autouse=True)
def _fresh_shared_registry():
    """Reset the shared registry before each test.

    This guarantees test isolation: plugins registered by one test
    cannot leak into another.  The shared registry is lazily
    re-populated on next access, so built-in plugins remain available.
    """
    reset_shared_registry()
    reset_unified_registry()
    yield
    reset_shared_registry()
    reset_unified_registry()


@pytest.fixture
def transformer():
    """Fixture that provides a TukuyTransformer instance for tests."""
    return TukuyTransformer()