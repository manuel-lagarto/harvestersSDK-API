"""
harvestersSDK_api.py
--------------------
Public entry point for the Universal Camera SDK API based on the Harvesters SDK.

This module provides a high-level interface to create and manage cameras,
abstracting away the internal implementation details.
"""

import logging
import yaml
from typing import Optional

from src.vendors.at_sensors_3d import CameraATSensors3D
from src.utils.error_handling import CameraError
from src.utils.config_loader import ConfigLoader

# ---------------------------------------------------------------------
# Logging configuration
# ---------------------------------------------------------------------
logger = logging.getLogger("harvestersSDK.API")

# ---------------------------------------------------------------------
# Supported cameras registry
# ---------------------------------------------------------------------
_CAMERA_REGISTRY = {
    "at_sensors_3d": CameraATSensors3D,
}

# ---------------------------------------------------------------------
# Factory function
# ---------------------------------------------------------------------
def create_camera(
    camera_type: str,
    config_paths: Optional["tuple[str, str]"] = None,
    config_dict: Optional[dict] = None
):
    """
    Factory function to create a camera instance based on the given type.

    Args:
        camera_type (str): Identifier of the camera vendor (e.g. "at_sensors_3d").
        config_paths (tuple, optional): Tuple with paths (base_config_path, camera_config_path).
        config_dict (dict, optional): Configuration dictionary (alternative to YAML files).

    Returns:
        CameraBase: Initialized camera object.

    Raises:
        CameraError: If the camera type is unsupported or initialization fails.
    """
    logger.info(f"Creating camera of type: {camera_type}")

    camera_class = _CAMERA_REGISTRY.get(camera_type.lower())
    if not camera_class:
        raise CameraError(f"Unsupported camera type: '{camera_type}'")

    # Load config
    if config_paths:
        if len(config_paths) != 2:
            raise CameraError("config_paths must be a tuple: (base_config_path, camera_config_path)")
        base_config_path, camera_config_path = config_paths
        loader = ConfigLoader(base_config_path=base_config_path, camera_config_path=camera_config_path)
        config = loader.load()
        logger.info(f"Configuration loaded from: {config_paths}")
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
# Utility functions
# ---------------------------------------------------------------------
def list_supported_cameras():
    """
    Returns a list of supported camera types.
    """
    return list(_CAMERA_REGISTRY.keys())
