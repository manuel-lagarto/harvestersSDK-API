"""
src package initialization
--------------------------
Defines top-level imports for the Universal Camera SDK API based on the Harvesters SDK.
Configures a global logger for consistent output across modules.
"""

from .utils.logging_utils import setup_logging, get_logger
import logging

# Initialize logging
setup_logging(
    level=logging.DEBUG,
    log_file="logs/harvesters_sdk.log"
)

# Import base classes
from .base.camera_base import CameraBase
from .base.transport_harvesters import TransportHarvesters

# Import vendor-specific implementations
from .vendors.at_sensors_3d import CameraATSensors3D

__all__ = [
    "CameraBase",
    "TransportHarvesters",
    "CameraATSensors3D",
    "setup_logging",
    "get_logger",
]