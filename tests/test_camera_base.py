import pytest
from unittest.mock import Mock, patch

from src.base.camera_base import CameraBase
from src.utils.error_handling import CameraError


class TestCamera(CameraBase):
    """Concrete implementation of CameraBase for testing."""

    def __init__(self, config):
        # Skip the parent __init__ for testing
        self.config = config
        self.timeout_ms = config.get("timeout_ms", 5000)
        self.device_config = {
            'user_defined_name': config.get('device_name', ''),
            'serial_number': config.get('device_serial', ''),
            'id': config.get('device_id', ''),
        }
        # Remove empty values
        self.device_config = {k: v for k, v in self.device_config.items() if v}


class TestCameraBase:

    @pytest.fixture
    def mock_transport(self):
        """Mock transport layer."""
        transport = Mock()
        transport.is_connected = False
        transport.is_acquiring = False
        return transport

    @pytest.fixture
    def camera(self, basic_config, mock_transport):
        """Create test camera instance with mocked transport."""
        camera = TestCamera(basic_config)
        camera._transport = mock_transport
        return camera

    def test_initialization(self, basic_config, camera):
        """Test camera initialization."""
        assert camera.config == basic_config
        assert camera.timeout_ms == basic_config.get("timeout_ms", 5000)
        assert camera.device_config == {
            'user_defined_name': basic_config['device_name'],
            'serial_number': basic_config['device_serial'],
            'id': basic_config['device_id'],
        }

    def test_properties_connected(self, camera, mock_transport):
        """Test connected property."""
        mock_transport.is_connected = True
        assert camera.connected

        mock_transport.is_connected = False
        assert not camera.connected

    def test_properties_acquiring(self, camera, mock_transport):
        """Test acquiring property."""
        mock_transport.is_acquiring = True
        assert camera.acquiring

        mock_transport.is_acquiring = False
        assert not camera.acquiring

    def test_connect_success(self, camera, mock_transport):
        """Test successful camera connection."""
        camera.connect()

        mock_transport.initialize.assert_called_once()
        mock_transport.connect_device.assert_called_once_with(camera.device_config)

    def test_connect_no_transport(self, camera):
        """Test connecting when transport is not set."""
        camera._transport = None

        with pytest.raises(CameraError, match="Transport layer not initialized"):
            camera.connect()

    def test_disconnect_success(self, camera, mock_transport):
        """Test successful camera disconnection."""
        mock_transport.is_acquiring = True
        mock_transport.is_connected = True

        camera.disconnect()

        mock_transport.stop_acquisition.assert_called_once()
        mock_transport.disconnect_device.assert_called_once()

    def test_disconnect_no_transport(self, camera):
        """Test disconnecting when transport is not set."""
        camera._transport = None

        with pytest.raises(CameraError, match="Transport layer not initialized"):
            camera.disconnect()

    def test_start_acquisition_not_connected(self, camera, mock_transport):
        """Test starting acquisition when not connected."""
        mock_transport.is_connected = False

        with pytest.raises(CameraError, match="Camera not connected"):
            camera.start_acquisition()

    def test_start_acquisition_success(self, camera, mock_transport):
        """Test successful acquisition start."""
        mock_transport.is_connected = True

        camera.start_acquisition()

        mock_transport.start_acquisition.assert_called_once()

    def test_stop_acquisition_not_connected(self, camera, mock_transport):
        """Test stopping acquisition when not connected."""
        mock_transport.is_connected = False

        with pytest.raises(CameraError, match="Camera not connected"):
            camera.stop_acquisition()

    def test_stop_acquisition_success(self, camera, mock_transport):
        """Test successful acquisition stop."""
        mock_transport.is_connected = True

        camera.stop_acquisition()

        mock_transport.stop_acquisition.assert_called_once()

    def test_get_frame_not_connected(self, camera, mock_transport):
        """Test getting frame when not connected."""
        mock_transport.is_connected = False

        with pytest.raises(CameraError, match="Camera not connected"):
            camera.get_frame()

    def test_get_frame_not_acquiring(self, camera, mock_transport):
        """Test getting frame when not acquiring."""
        mock_transport.is_connected = True
        mock_transport.is_acquiring = False

        with pytest.raises(CameraError, match="Acquisition not started"):
            camera.get_frame()

    def test_get_frame_success(self, camera, mock_transport):
        """Test successful frame retrieval."""
        mock_transport.is_connected = True
        mock_transport.is_acquiring = True
        mock_frame = Mock()
        mock_transport.get_frame.return_value = mock_frame

        result = camera.get_frame()

        assert result == mock_frame
        mock_transport.get_frame.assert_called_once()

    def test_get_frame_with_timeout(self, camera, mock_transport):
        """Test frame retrieval with custom timeout."""
        mock_transport.is_connected = True
        mock_transport.is_acquiring = True
        mock_frame = Mock()
        mock_transport.get_frame.return_value = mock_frame

        result = camera.get_frame(timeout_ms=2000)

        assert result == mock_frame
        mock_transport.get_frame.assert_called_once_with(timeout_ms=2000)

    def test_set_parameter_not_connected(self, camera, mock_transport):
        """Test setting parameter when not connected."""
        mock_transport.is_connected = False

        with pytest.raises(CameraError, match="Camera not connected"):
            camera.set_parameter("TestParam", 42)

    def test_set_parameter_success(self, camera, mock_transport):
        """Test successful parameter setting."""
        mock_transport.is_connected = True

        camera.set_parameter("TestParam", 42)

        mock_transport.set_node_value.assert_called_once_with("TestParam", 42)

    def test_get_parameter_not_connected(self, camera, mock_transport):
        """Test getting parameter when not connected."""
        mock_transport.is_connected = False

        with pytest.raises(CameraError, match="Camera not connected"):
            camera.get_parameter("TestParam")

    def test_get_parameter_success(self, camera, mock_transport):
        """Test successful parameter retrieval."""
        mock_transport.is_connected = True
        mock_transport.get_node_value.return_value = 42

        result = camera.get_parameter("TestParam")

        assert result == 42
        mock_transport.get_node_value.assert_called_once_with("TestParam")

    def test_context_manager_enter_not_connected(self, camera, mock_transport):
        """Test context manager __enter__ when not connected."""
        mock_transport.is_connected = False

        with patch.object(camera, 'connect') as mock_connect:
            with camera:
                mock_connect.assert_called_once()

    def test_context_manager_enter_already_connected(self, camera, mock_transport):
        """Test context manager __enter__ when already connected."""
        mock_transport.is_connected = True

        with patch.object(camera, 'connect') as mock_connect:
            with camera:
                mock_connect.assert_not_called()

    def test_context_manager_exit(self, camera, mock_transport):
        """Test context manager __exit__."""
        mock_transport.is_acquiring = True
        mock_transport.is_connected = True

        with patch.object(camera, 'stop_acquisition') as mock_stop, \
             patch.object(camera, 'disconnect') as mock_disconnect:

            with camera:
                pass

            mock_stop.assert_called_once()
            mock_disconnect.assert_called_once()

    def test_context_manager_exit_not_acquiring(self, camera, mock_transport):
        """Test context manager __exit__ when not acquiring."""
        mock_transport.is_acquiring = False
        mock_transport.is_connected = True

        with patch.object(camera, 'stop_acquisition') as mock_stop, \
             patch.object(camera, 'disconnect') as mock_disconnect:

            with camera:
                pass

            mock_stop.assert_not_called()
            mock_disconnect.assert_called_once()

    def test_destructor_cleanup(self, camera, mock_transport):
        """Test destructor cleanup."""
        mock_transport.is_acquiring = True
        mock_transport.is_connected = True

        with patch.object(camera, 'stop_acquisition') as mock_stop, \
             patch.object(camera, 'disconnect') as mock_disconnect:

            camera.__del__()

            mock_stop.assert_called_once()
            mock_disconnect.assert_called_once()