"""
Harvesters SDK API
--------------------
Public high-level API for the Universal Camera SDK based on Harvesters.

This module provides a high-level interface to create and manage cameras,
abstracting away the internal implementation details.
"""

from typing import Optional, List, Dict, Any, Tuple

from src.vendors.at_sensors_3d import CameraATSensors3D
from src.base.camera_base import CameraBase
from src.base.transport_harvesters import TransportHarvesters
from src.utils.error_handling import CameraError
from src.utils.config_loader import ConfigLoader
from src.utils.logging_utils import get_logger


# Logging configuration
logger = get_logger("API")

# Supported cameras registry (add more as needed...)
_CAMERA_REGISTRY = {
    "at_sensors_3d": CameraATSensors3D,
}


# ---------------------------------------------------------------------
# Factory function
# ---------------------------------------------------------------------
def create_camera(
    camera_type: str,
    config_paths: Optional[Tuple[str, str]] = None,
    config_dict: Optional[Dict[str, Any]] = None
) -> CameraBase:
    """
    Factory function to create a camera instance based on vendor type.

    Args:
        camera_type (str): Camera vendor identifier (e.g., "at_sensors_3d").
        config_paths (Tuple[str, str], optional): Tuple with (base_config_path, camera_config_path).
        config_dict (Dict[str, Any], optional): Configuration dictionary (alternative to YAML files).

    Returns:
        CameraBase: Initialized camera object ready for configuration and acquisition.

    Raises:
        CameraError: If camera type is unsupported or initialization fails.

    Example:
        >>> config = {"cti_path": "/path/to/producer.cti", "device_name": "Camera1"}
        >>> camera = create_camera("at_sensors_3d", config_dict=config)
        >>> camera.setup(dual_configuration=False, device_selectors=[0])
    """
    logger.info(f"Creating camera of type: {camera_type}")

    camera_class = _CAMERA_REGISTRY.get(camera_type.lower())
    if not camera_class:
        raise CameraError(
            f"Unsupported camera type: '{camera_type}'. "
            f"Supported types: {list_supported_cameras()}"
        )

    # Load configuration
    if config_paths:
        if not isinstance(config_paths, tuple) or len(config_paths) != 2:
            raise CameraError("config_paths must be a tuple: (base_config_path, camera_config_path)")
        base_config_path, camera_config_path = config_paths
        loader = ConfigLoader(base_config_path=base_config_path, camera_config_path=camera_config_path)
        config = loader.load()
        logger.info(f"Configuration loaded from YAML files: {config_paths}")
    elif config_dict:
        config = config_dict
        logger.info("Configuration loaded from provided dictionary.")
    else:
        config = {}
        logger.warning("No configuration provided; using empty default.")

    # Create and return camera instance
    try:
        camera = camera_class(config=config)
        logger.info(f"Camera '{camera_type}' created successfully.")
        return camera
    except Exception as e:
        logger.exception("Camera initialization failed.")
        raise CameraError(f"Failed to initialize camera '{camera_type}': {e}")


# ---------------------------------------------------------------------
# Device discovery
# ---------------------------------------------------------------------
def list_supported_cameras() -> List[str]:
    """
    List all supported camera vendor types.

    Returns:
        List[str]: List of supported camera type identifiers.

    Example:
        >>> cameras = list_supported_cameras()
        >>> print(cameras)
        ['at_sensors_3d']
    """
    return list(_CAMERA_REGISTRY.keys())


def discover_devices(cti_path: str, raise_on_error: bool = True) -> List[Dict[str, Any]]:
    """
    Discover all available GenICam devices connected to the system.

    Args:
        cti_path (str): Path to GenTL Producer (.cti) file.
        raise_on_error (bool): If True, raise exceptions; if False, return empty list.

    Returns:
        List[Dict[str, Any]]: List of discovered device information dictionaries.
                             Each dict contains: index, id, vendor, model, serial_number, user_defined_name.

    Raises:
        CameraError: If initialization fails and raise_on_error is True.

    Example:
        >>> devices = discover_devices("/path/to/producer.cti")
        >>> for dev in devices:
        ...     print(f"Device: {dev['user_defined_name']} (S/N: {dev['serial_number']})")
    """
    logger.info(f"Discovering devices using CTI: {cti_path}")
    try:
        transport = TransportHarvesters(cti_path)
        devices = transport.list_devices(raise_on_error=raise_on_error)
        logger.info(f"Discovered {len(devices)} device(s).")
        return devices
    except Exception as e:
        logger.exception("Device discovery failed.")
        if raise_on_error:
            raise CameraError(f"Failed to discover devices: {e}")
        return []


# ---------------------------------------------------------------------
# Parameter configuration
# ---------------------------------------------------------------------
def configure_camera(
    camera: CameraBase,
    parameters: Dict[str, Any],
    acquirer_index: int = 0
) -> None:
    """
    Configure multiple camera parameters at once.

    Args:
        camera (CameraBase): Initialized camera instance.
        parameters (Dict[str, Any]): Dictionary of parameter names and values.
                                    Parameter names should match GenICam node names.
        acquirer_index (int): Sensor index to configure (default 0 = primary).

    Raises:
        CameraError: If any parameter configuration fails.

    Example:
        >>> params = {"ExposureTime": 2000.0, "Gain": 1.5, "PixelFormat": "Mono8"}
        >>> configure_camera(camera, params, acquirer_index=0)
    """
    logger.info(f"Configuring {len(parameters)} parameter(s) on acquirer {acquirer_index}...")
    try:
        for param_name, value in parameters.items():
            camera.set_parameter(param_name, value, acquirer_index=acquirer_index)
            logger.info(f"  {param_name} configured successfully with {value} value")
    except Exception as e:
        logger.exception("Camera configuration failed.")
        raise CameraError(f"Failed to configure camera: {e}")


def get_camera_info(camera: CameraBase) -> Dict[str, Any]:
    """
    Retrieve camera state and configuration information.

    Args:
        camera (CameraBase): Initialized camera instance.

    Returns:
        Dict[str, Any]: Dictionary with keys:
            - connected: bool - Camera is connected and has acquirers
            - acquiring: bool - Acquisition currently active
            - num_sensors: int - Number of configured sensors/acquirers
            - timeout_ms: int - Frame fetch timeout in milliseconds
            - strict_mode: bool - Error handling mode

    Example:
        >>> info = get_camera_info(camera)
        >>> print(f"Connected: {info['connected']}, Sensors: {info['num_sensors']}")
    """
    logger.info("Retrieving camera information...")
    try:
        info = {
            "connected": camera.connected,
            "acquiring": camera.acquiring,
            "num_sensors": len(camera._acquirers),
            "timeout_ms": camera.timeout_ms,
            "strict_mode": camera.strict,
        }
        logger.info(f"Camera information: {info}")
        return info
    except Exception as e:
        logger.exception("Failed to retrieve camera information.")
        raise CameraError(f"Failed to get camera info: {e}")
