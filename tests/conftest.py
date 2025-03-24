import pytest
from tukuy import TukuyTransformer

@pytest.fixture
def transformer():
    """Fixture that provides a TukuyTransformer instance for tests."""
    return TukuyTransformer()