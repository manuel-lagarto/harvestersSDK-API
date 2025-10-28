import pytest
from unittest.mock import Mock, patch

@pytest.fixture
def basic_config():
    """Provide camera configuration for tests."""
    return {
        "cti_path": "/path/to/producer.cti",
        "device_name": "TestCamera",
        "device_serial": "123456",
        "device_id": "::ID->AB-CD-EF-01-23-45::192.168.0.2",
        "timeout_ms": 1000
    }

@pytest.fixture
def mock_transport():
    """Mock transport layer."""
    transport = Mock()
    transport.is_connected = False
    transport.is_acquiring = False
    return transport