import pytest
from unittest.mock import Mock, patch

from src.vendors.at_sensors_3d import CameraATSensors3D
from src.utils.error_handling import CameraError


class TestCameraATSensors3D:

    @pytest.fixture
    def mock_transport(self):
        """Mock transport layer."""
        transport = Mock()
        transport.is_connected = False
        transport.is_acquiring = False
        return transport

    @pytest.fixture
    def camera(self, basic_config, mock_transport):
        """Create AT Sensors 3D camera instance with mocked transport."""
        # Mock the parent __init__ to avoid hardware dependencies
        with patch('src.base.camera_base.CameraBase.__init__', return_value=None):
            camera = CameraATSensors3D.__new__(CameraATSensors3D)
            camera.config = basic_config
            camera.timeout_ms = basic_config.get("timeout_ms", 5000)
            camera.device_config = {
                'user_defined_name': basic_config.get('device_name', ''),
                'serial_number': basic_config.get('device_serial', ''),
                'id': basic_config.get('device_id', ''),
            }
            camera.device_config = {k: v for k, v in camera.device_config.items() if v}
            camera._transport = mock_transport
            return camera

    def test_initialization(self, basic_config, camera):
        """Test camera initialization."""
        assert camera.config == basic_config
        assert hasattr(camera, 'NODES')
        assert 'exposure' in camera.NODES
        assert 'gain' in camera.NODES
        assert 'pixel_format' in camera.NODES
        assert camera.NODES['exposure'] == 'ExposureTime'
        assert camera.NODES['gain'] == 'Gain'

    def test_set_exposure_time_not_connected(self, camera, mock_transport):
        """Test setting exposure time when not connected."""
        mock_transport.is_connected = False

        with pytest.raises(CameraError, match="Camera not connected"):
            camera.set_exposure_time(1000.0)

    def test_set_exposure_time_success(self, camera, mock_transport):
        """Test successful exposure time setting."""
        mock_transport.is_connected = True

        camera.set_exposure_time(1000.0)

        mock_transport.set_node_value.assert_called_once_with('ExposureTime', 1000.0)

    def test_get_exposure_time_not_connected(self, camera, mock_transport):
        """Test getting exposure time when not connected."""
        mock_transport.is_connected = False

        with pytest.raises(CameraError, match="Camera not connected"):
            camera.get_exposure_time()

    def test_get_exposure_time_success(self, camera, mock_transport):
        """Test successful exposure time retrieval."""
        mock_transport.is_connected = True
        mock_transport.get_node_value.return_value = 1000.0

        result = camera.get_exposure_time()

        assert result == 1000.0
        mock_transport.get_node_value.assert_called_once_with('ExposureTime')

    def test_set_gain_not_connected(self, camera, mock_transport):
        """Test setting gain when not connected."""
        mock_transport.is_connected = False

        with pytest.raises(CameraError, match="Camera not connected"):
            camera.set_gain(1.5)

    def test_set_gain_success(self, camera, mock_transport):
        """Test successful gain setting."""
        mock_transport.is_connected = True

        camera.set_gain(1.5)

        mock_transport.set_node_value.assert_called_once_with('Gain', 1.5)

    def test_get_gain_not_connected(self, camera, mock_transport):
        """Test getting gain when not connected."""
        mock_transport.is_connected = False

        with pytest.raises(CameraError, match="Camera not connected"):
            camera.get_gain()

    def test_get_gain_success(self, camera, mock_transport):
        """Test successful gain retrieval."""
        mock_transport.is_connected = True
        mock_transport.get_node_value.return_value = 1.5

        result = camera.get_gain()

        assert result == 1.5
        mock_transport.get_node_value.assert_called_once_with('Gain')

    def test_set_pixel_format_not_connected(self, camera, mock_transport):
        """Test setting pixel format when not connected."""
        mock_transport.is_connected = False

        with pytest.raises(CameraError, match="Camera not connected"):
            camera.set_pixel_format("Mono8")

    def test_set_pixel_format_success(self, camera, mock_transport):
        """Test successful pixel format setting."""
        mock_transport.is_connected = True

        camera.set_pixel_format("Mono8")

        mock_transport.set_node_value.assert_called_once_with('PixelFormat', "Mono8")

    def test_get_pixel_format_not_connected(self, camera, mock_transport):
        """Test getting pixel format when not connected."""
        mock_transport.is_connected = False

        with pytest.raises(CameraError, match="Camera not connected"):
            camera.get_pixel_format()

    def test_get_pixel_format_success(self, camera, mock_transport):
        """Test successful pixel format retrieval."""
        mock_transport.is_connected = True
        mock_transport.get_node_value.return_value = "Mono8"

        result = camera.get_pixel_format()

        assert result == "Mono8"
        mock_transport.get_node_value.assert_called_once_with('PixelFormat')

    def test_set_roi_not_connected(self, camera, mock_transport):
        """Test setting ROI when not connected."""
        mock_transport.is_connected = False

        with pytest.raises(CameraError, match="Camera not connected"):
            camera.set_roi(640, 480, 0, 0)

    def test_set_roi_success(self, camera, mock_transport):
        """Test successful ROI setting."""
        mock_transport.is_connected = True

        camera.set_roi(640, 480, 10, 20)

        assert mock_transport.set_node_value.call_count == 4
        mock_transport.set_node_value.assert_any_call('Width', 640)
        mock_transport.set_node_value.assert_any_call('Height', 480)
        mock_transport.set_node_value.assert_any_call('OffsetX', 10)
        mock_transport.set_node_value.assert_any_call('OffsetY', 20)

    def test_get_roi_not_connected(self, camera, mock_transport):
        """Test getting ROI when not connected."""
        mock_transport.is_connected = False

        with pytest.raises(CameraError, match="Camera not connected"):
            camera.get_roi()

    def test_get_roi_success(self, camera, mock_transport):
        """Test successful ROI retrieval."""
        mock_transport.is_connected = True
        mock_transport.get_node_value.side_effect = [640, 480, 10, 20]

        result = camera.get_roi()

        assert result == {
            "width": 640,
            "height": 480,
            "offset_x": 10,
            "offset_y": 20
        }

        assert mock_transport.get_node_value.call_count == 4
        mock_transport.get_node_value.assert_any_call('Width')
        mock_transport.get_node_value.assert_any_call('Height')
        mock_transport.get_node_value.assert_any_call('OffsetX')
        mock_transport.get_node_value.assert_any_call('OffsetY')