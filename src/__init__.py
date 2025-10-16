"""
src package initialization
--------------------------
Defines top-level imports for the Universal Camera SDK API based on the Harvesters SDK.
Configures a global logger for consistent output across modules.
"""

import logging

# Configure global logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S"
)

logger = logging.getLogger("harvestersSDK")

# Import base classes
from .base.camera_base import CameraBase
from .base.transport_harvesters import TransportHarvesters

# Import vendor-specific implementations
from .vendors.at_sensors_3d import CameraATSensors3D

__all__ = [
    "CameraBase",
    "TransportHarvesters",
    "CameraATSensors3D",
]
