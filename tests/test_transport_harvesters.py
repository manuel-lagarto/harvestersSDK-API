import pytest
from unittest.mock import Mock, patch, MagicMock
from harvesters.core import Harvester, ImageAcquirer

from src.base.transport_harvesters import TransportHarvesters
from src.utils.error_handling import CameraError


class TestTransportHarvesters:

    @pytest.fixture
    def cti_path(self):
        return "/path/to/test.cti"

    @pytest.fixture
    def transport(self, cti_path):
        return TransportHarvesters(cti_path)

    def test_initialization(self, cti_path, transport):
        """Test transport initialization."""
        assert transport.cti_path == cti_path
        assert transport.harvester is None
        assert transport.image_acquirer is None
        assert not transport.is_connected
        assert not transport.is_acquiring
        assert transport.devices_list == []

    @patch('src.base.transport_harvesters.Harvester')
    def test_initialize_success(self, mock_harvester_class, transport):
        """Test successful harvester initialization."""
        mock_harvester = Mock()
        mock_harvester_class.return_value = mock_harvester

        transport.initialize()

        mock_harvester_class.assert_called_once()
        mock_harvester.add_file.assert_called_once_with(transport.cti_path)
        mock_harvester.update.assert_called_once()
        assert transport.harvester == mock_harvester

    @patch('src.base.transport_harvesters.Harvester')
    def test_initialize_already_initialized(self, mock_harvester_class, transport, caplog):
        """Test initialization when already initialized."""
        transport.harvester = Mock()

        transport.initialize()

        mock_harvester_class.assert_not_called()
        assert "Harvester already initialized" in caplog.text

    @patch('src.base.transport_harvesters.Harvester')
    def test_initialize_failure(self, mock_harvester_class, transport):
        """Test harvester initialization failure."""
        mock_harvester_class.side_effect = Exception("Init failed")

        with pytest.raises(CameraError, match="Failed to initialize Harvester"):
            transport.initialize()

    @patch('src.base.transport_harvesters.Harvester')
    def test_list_devices_success(self, mock_harvester_class, transport):
        """Test successful device listing."""
        # Mock harvester and device info
        mock_harvester = Mock()
        mock_harvester_class.return_value = mock_harvester

        mock_device_info = Mock()
        mock_device_info.id_ = "test_id"
        mock_device_info.vendor = "TestVendor"
        mock_device_info.model = "TestModel"
        mock_device_info.serial_number = "12345"
        mock_device_info.user_defined_name = "TestCamera"

        mock_harvester.device_info_list = [mock_device_info]

        devices = transport.list_devices()

        assert len(devices) == 1
        assert devices[0]['id'] == "test_id"
        assert devices[0]['vendor'] == "TestVendor"
        assert devices[0]['model'] == "TestModel"
        assert devices[0]['serial_number'] == "12345"
        assert devices[0]['user_defined_name'] == "TestCamera"

    @patch('src.base.transport_harvesters.Harvester')
    def test_list_devices_no_devices(self, mock_harvester_class, transport):
        """Test device listing when no devices found."""
        mock_harvester = Mock()
        mock_harvester_class.return_value = mock_harvester
        mock_harvester.device_info_list = []

        devices = transport.list_devices()

        assert devices == []

    @patch('src.base.transport_harvesters.Harvester')
    def test_connect_device_first_available(self, mock_harvester_class, transport):
        """Test connecting to first available device when no config provided."""
        mock_harvester = Mock()
        mock_harvester_class.return_value = mock_harvester

        mock_device_info = Mock()
        mock_harvester.device_info_list = [mock_device_info]

        mock_acquirer = Mock()
        mock_harvester.create.return_value = mock_acquirer

        result = transport.connect_device()

        mock_harvester.create.assert_called_once_with(0)
        assert result == mock_acquirer
        assert transport.image_acquirer == mock_acquirer
        assert transport._is_connected
        # Note: connecting doesn't automatically start acquisition
        assert not transport._is_acquiring

    @patch('src.base.transport_harvesters.Harvester')
    def test_connect_device_by_name(self, mock_harvester_class, transport):
        """Test connecting to device by user defined name."""
        mock_harvester = Mock()
        mock_harvester_class.return_value = mock_harvester

        # Mock device info
        mock_device_info = Mock()
        mock_device_info.id_ = "test_id"
        mock_device_info.vendor = "TestVendor"
        mock_device_info.model = "TestModel"
        mock_device_info.serial_number = "12345"
        mock_device_info.user_defined_name = "TargetCamera"

        mock_harvester.device_info_list = [mock_device_info]

        mock_acquirer = Mock()
        mock_harvester.create.return_value = mock_acquirer

        device_config = {'user_defined_name': 'TargetCamera'}
        result = transport.connect_device(device_config)

        mock_harvester.create.assert_called_once_with(0)
        assert result == mock_acquirer
        assert transport._is_connected
        # Note: connecting doesn't start acquisition automatically
        assert not transport._is_acquiring

    def test_connect_device_already_connected(self, transport, caplog):
        """Test connecting when already connected."""
        transport._is_connected = True
        transport.image_acquirer = Mock()

        result = transport.connect_device()

        assert result == transport.image_acquirer
        assert "Device already connected" in caplog.text

    @patch('src.base.transport_harvesters.Harvester')
    def test_connect_device_not_found(self, mock_harvester_class, transport):
        """Test connecting to non-existent device."""
        mock_harvester = Mock()
        mock_harvester_class.return_value = mock_harvester
        mock_harvester.device_info_list = []

        device_config = {'user_defined_name': 'NonExistent'}

        with pytest.raises(CameraError, match="Failed to connect device"):
            transport.connect_device(device_config)

    def test_start_acquisition_not_connected(self, transport):
        """Test starting acquisition when not connected."""
        with pytest.raises(CameraError, match="No device connected"):
            transport.start_acquisition()

    def test_start_acquisition_already_started(self, transport, caplog):
        """Test starting acquisition when already started."""
        transport._is_connected = True
        transport._is_acquiring = True
        transport.image_acquirer = Mock()

        transport.start_acquisition()

        transport.image_acquirer.start.assert_not_called()
        assert "Acquisition already started" in caplog.text

    def test_start_acquisition_success(self, transport):
        """Test successful acquisition start."""
        transport._is_connected = True
        transport.image_acquirer = Mock()

        transport.start_acquisition()

        transport.image_acquirer.start.assert_called_once()
        assert transport._is_acquiring

    def test_stop_acquisition_not_connected(self, transport):
        """Test stopping acquisition when not connected."""
        with pytest.raises(CameraError, match="No device connected"):
            transport.stop_acquisition()

    def test_stop_acquisition_not_started(self, transport, caplog):
        """Test stopping acquisition when not started."""
        transport._is_connected = True
        transport.image_acquirer = Mock()

        transport.stop_acquisition()

        transport.image_acquirer.stop.assert_not_called()
        assert "Acquisition not active" in caplog.text

    def test_stop_acquisition_success(self, transport):
        """Test successful acquisition stop."""
        transport._is_connected = True
        transport._is_acquiring = True
        transport.image_acquirer = Mock()

        transport.stop_acquisition()

        transport.image_acquirer.stop.assert_called_once()
        assert not transport._is_acquiring

    def test_get_frame_not_connected(self, transport):
        """Test getting frame when not connected."""
        with pytest.raises(CameraError, match="No device connected"):
            transport.get_frame()

    def test_get_frame_not_acquiring(self, transport):
        """Test getting frame when not acquiring."""
        transport._is_connected = True

        with pytest.raises(CameraError, match="Acquisition not started"):
            transport.get_frame()

    def test_get_frame_success(self, transport):
        """Test successful frame retrieval."""
        transport._is_connected = True
        transport._is_acquiring = True
        transport.image_acquirer = Mock()

        mock_buffer = Mock()
        mock_payload = Mock()
        mock_payload.components = ["component1", "component2"]
        mock_buffer.payload = mock_payload

        mock_context = Mock()
        mock_context.__enter__ = Mock(return_value=mock_buffer)
        mock_context.__exit__ = Mock(return_value=None)
        transport.image_acquirer.fetch.return_value = mock_context

        components = transport.get_frame()

        assert components == ["component1", "component2"]

    def test_get_frame_no_payload(self, transport):
        """Test frame retrieval when buffer has no payload."""
        transport._is_connected = True
        transport._is_acquiring = True
        transport.image_acquirer = Mock()

        mock_buffer = Mock()
        mock_buffer.payload = None

        mock_context = Mock()
        mock_context.__enter__ = Mock(return_value=mock_buffer)
        mock_context.__exit__ = Mock(return_value=None)
        transport.image_acquirer.fetch.return_value = mock_context

        with pytest.raises(CameraError, match="Fetched buffer has no payload"):
            transport.get_frame()

    def test_disconnect_device_success(self, transport):
        """Test successful device disconnection."""
        transport._is_connected = True
        transport._is_acquiring = True
        mock_acquirer = Mock()
        transport.image_acquirer = mock_acquirer
        mock_harvester = Mock()
        transport.harvester = mock_harvester

        transport.disconnect_device()

        mock_acquirer.stop.assert_called_once()
        mock_acquirer.destroy.assert_called_once()
        mock_harvester.reset.assert_called_once()
        assert transport.image_acquirer is None
        assert transport.harvester is None
        assert not transport._is_acquiring
        assert not transport._is_connected

    def test_set_node_value_success(self, transport):
        """Test successful node value setting."""
        transport.image_acquirer = Mock()
        mock_node = Mock()
        mock_node.is_writable = True
        transport.image_acquirer.remote_device.node_map.get_node.return_value = mock_node

        transport.set_node_value("TestNode", 42)

        assert mock_node.value == 42

    def test_set_node_value_not_connected(self, transport):
        """Test setting node value when not connected."""
        with pytest.raises(CameraError, match="Device not connected"):
            transport.set_node_value("TestNode", 42)

    def test_set_node_value_not_writable(self, transport):
        """Test setting node value when node is not writable."""
        transport.image_acquirer = Mock()
        mock_node = Mock()
        mock_node.is_writable = False
        transport.image_acquirer.remote_device.node_map.get_node.return_value = mock_node

        with pytest.raises(CameraError, match="Node TestNode is not writable"):
            transport.set_node_value("TestNode", 42)

    def test_get_node_value_success(self, transport):
        """Test successful node value retrieval."""
        transport.image_acquirer = Mock()
        mock_node = Mock()
        mock_node.is_readable = True
        mock_node.value = 42
        transport.image_acquirer.remote_device.node_map.get_node.return_value = mock_node

        result = transport.get_node_value("TestNode")

        assert result == 42

    def test_get_node_value_not_connected(self, transport):
        """Test getting node value when not connected."""
        with pytest.raises(CameraError, match="Device not connected"):
            transport.get_node_value("TestNode")

    def test_get_node_value_not_readable(self, transport):
        """Test getting node value when node is not readable."""
        transport.image_acquirer = Mock()
        mock_node = Mock()
        mock_node.is_readable = False
        transport.image_acquirer.remote_device.node_map.get_node.return_value = mock_node

        with pytest.raises(CameraError, match="Node TestNode is not readable"):
            transport.get_node_value("TestNode")

    def test_context_manager(self, transport):
        """Test context manager functionality."""
        transport._is_connected = False
        transport.image_acquirer = None

        with patch.object(transport, 'connect_device') as mock_connect, \
             patch.object(transport, 'disconnect_device') as mock_disconnect:

            with transport:
                pass

            mock_connect.assert_called_once()
            mock_disconnect.assert_called_once()

    def test_context_manager_with_acquisition(self, transport):
        """Test context manager with acquisition context."""
        transport._is_connected = True
        transport._is_acquiring = False

        with patch.object(transport, 'start_acquisition') as mock_start, \
             patch.object(transport, 'stop_acquisition') as mock_stop:

            with transport.acquisition_context():
                pass

            mock_start.assert_called_once()
            mock_stop.assert_called_once()