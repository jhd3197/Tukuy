import pytest
from tukuy import ToolsTransformer

@pytest.fixture
def transformer():
    """Fixture that provides a ToolsTransformer instance for tests."""
    return ToolsTransformer()