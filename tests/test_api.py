import pytest
from unittest.mock import Mock, patch

from harvestersSDK_api import create_camera, list_supported_cameras
from src.utils.error_handling import CameraError


class TestAPI:

    def test_list_supported_cameras(self):
        """Test listing supported camera types."""
        cameras = list_supported_cameras()

        assert isinstance(cameras, list)
        assert "at_sensors_3d" in cameras

    @patch('harvestersSDK_api._CAMERA_REGISTRY')
    def test_create_camera_invalid_type(self, mock_registry):
        """Test creating camera with invalid type."""
        mock_registry.get.return_value = None

        with pytest.raises(CameraError, match="Unsupported camera type"):
            create_camera("invalid_type")

    @patch('harvestersSDK_api._CAMERA_REGISTRY')
    @patch('harvestersSDK_api.ConfigLoader')
    def test_create_camera_with_config_paths(self, mock_config_loader, mock_registry):
        """Test creating camera with config paths."""
        mock_camera_class = Mock()
        mock_camera_instance = Mock()
        mock_camera_class.return_value = mock_camera_instance
        mock_registry.get.return_value = mock_camera_class

        mock_config = Mock()
        mock_loader_instance = Mock()
        mock_loader_instance.load.return_value = mock_config
        mock_config_loader.return_value = mock_loader_instance

        result = create_camera("at_sensors_3d", config_paths=("base.yaml", "camera.yaml"))

        mock_config_loader.assert_called_once_with(
            base_config_path="base.yaml",
            camera_config_path="camera.yaml"
        )
        mock_camera_class.assert_called_once_with(config=mock_config)
        assert result == mock_camera_instance

    @patch('harvestersSDK_api._CAMERA_REGISTRY')
    def test_create_camera_with_config_dict(self, mock_registry):
        """Test creating camera with config dictionary."""
        mock_camera_class = Mock()
        mock_camera_instance = Mock()
        mock_camera_class.return_value = mock_camera_instance
        mock_registry.get.return_value = mock_camera_class

        config_dict = {"cti_path": "/path/to/cti"}
        result = create_camera("at_sensors_3d", config_dict=config_dict)

        mock_camera_class.assert_called_once_with(config=config_dict)
        assert result == mock_camera_instance

    @patch('harvestersSDK_api._CAMERA_REGISTRY')
    def test_create_camera_no_config(self, mock_registry):
        """Test creating camera with no configuration."""
        mock_camera_class = Mock()
        mock_camera_instance = Mock()
        mock_camera_class.return_value = mock_camera_instance
        mock_registry.get.return_value = mock_camera_class

        result = create_camera("at_sensors_3d")

        mock_camera_class.assert_called_once_with(config={})
        assert result == mock_camera_instance

    @patch('harvestersSDK_api._CAMERA_REGISTRY')
    def test_create_camera_invalid_config_paths(self, mock_registry):
        """Test creating camera with invalid config paths tuple."""
        mock_registry.get.return_value = Mock()

        with pytest.raises(CameraError, match="config_paths must be a tuple"):
            create_camera("at_sensors_3d", config_paths="invalid")

    @patch('harvestersSDK_api._CAMERA_REGISTRY')
    def test_create_camera_initialization_failure(self, mock_registry):
        """Test camera creation when initialization fails."""
        mock_camera_class = Mock()
        mock_camera_class.side_effect = Exception("Init failed")
        mock_registry.get.return_value = mock_camera_class

        with pytest.raises(CameraError, match="Failed to initialize camera"):
            create_camera("at_sensors_3d")
