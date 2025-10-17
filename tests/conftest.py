import pytest
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../app'))

@pytest.fixture(autouse=True)
def setup_test_environment():
    """Setup test environment"""
    # You can add test setup code here
    yield
    # Cleanup code here