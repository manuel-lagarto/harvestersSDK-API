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
from src.utils.error_handling import CameraError
from src.utils.config_loader import ConfigLoader
from src.utils.logging_utils import get_logger


# Logging configuration
logger = get_logger("API")

# Supported cameras registry (add more as needed...)
_CLASS_REGISTRY: Dict[tuple, type] = {
    ("at-automation technology gmbh", "linescan3d", "dual_sensor"): CameraATSensors3D,
    # ("hikrobot", "linescan2d", "single_sensor"): CameraHikrobotLineScan,
}

def _norm(s: Optional[str]) -> str:
    return (s or "").strip().lower()

def _pick_class(vendor: str, scan_type: str, topology: str) -> type:
    key = (_norm(vendor), _norm(scan_type), _norm(topology))
    cls = _CLASS_REGISTRY.get(key)
    if not cls:
        supported = [f"{v}|{st}|{tp}" for (v, st, tp) in _CLASS_REGISTRY.keys()]
        raise CameraError(
            f"Unsupported camera: vendor='{vendor}', scanType='{scan_type}', topology='{topology}'. "
            f"Supported cameras: {supported}"
        )
    return cls


# ---------------------------------------------------------------------
# Factory function
# ---------------------------------------------------------------------
def create_camera(
    device_name_base: str,
    config_path: Optional[str] = None,
    vendor: Optional[str] = None,
    scan_type: Optional[str] = None,
    topology: Optional[str] = None
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
    if not device_name_base:
            raise CameraError("create_camera requires device_name_base.")

    logger.info(f"Creating camera for the specified device name: {device_name_base}")

    if config_path:
        # Load .json configuration file from path
        config_loader = ConfigLoader(config_path)
        config_loader.load()

        # Get configuration dictionaries
        api_config_dict: Dict[str, Any]     = config_loader.get_api_config(device_name_base)
        device_data_dict: Dict[str, Any]    = config_loader.get_device_data(device_name_base)
        device_genicam_dict: Dict[str, Any] = config_loader.get_device_genicam(device_name_base)

        # Get camera vendor specifications
        vendor   = device_data_dict.get("vendor")
        scanType = device_data_dict.get("scanType")
        topology = device_data_dict.get("topology")
    else:
        logger.warning("No configuration file path provided! Using values from arguments.")

    # Create and return camera instance
    try:
        camera_cls = _pick_class(vendor, scanType, topology) # type: ignore
        camera = camera_cls(
            api_config_dict=api_config_dict,
            device_data_dict=device_data_dict,
            device_genicam_dict=device_genicam_dict
        )
        logger.info(f"Camera '{device_name_base}' was initialized successfully!")
        logger.debug(f"Camera info: vendor='{vendor}', scanType='{scanType}', topology='{topology}'")        
        logger.debug(f"Camera configuration: '{device_data_dict}'")
        return camera
    except Exception as e:
        logger.exception("Camera initialization failed!")
        raise CameraError(f"Failed to initialize camera '{device_name_base}': {e}")


# ---------------------------------------------------------------------
# Device discovery
# ---------------------------------------------------------------------
def list_supported_cameras():
    """
    List all supported camera vendor types.

    Returns:
        List[str]: List of supported camera type identifiers.

    Example:
        >>> cameras = list_supported_cameras()
        >>> print(cameras)
        ['at_sensors_3d']
    """
    return list(_CLASS_REGISTRY.keys())


def discover_devices(cti_path: str, raise_on_error: bool = True):
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
    # TODO: Request list of devices from CameraBase
    pass


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
