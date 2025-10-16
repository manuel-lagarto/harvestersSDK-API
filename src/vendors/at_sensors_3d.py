"""
Vendor-specific implementation: AT Sensors 3D
---------------------------------------------
Implements camera-specific logic using the Harvesters transport layer.
"""

import logging
from src.base.camera_base import CameraBase
from src.utils.error_handling import CameraError
from src.base.transport_harvesters import TransportHarvesters

logger = logging.getLogger("harvestersSDK.ATSensors3D")


class CameraATSensors3D(CameraBase):
    """
    AT Sensors 3D camera implementation using the Harvesters transport layer.
    """

    def __init__(self, config: dict):
        super().__init__(config=config)
        self.cti_path = config.get("cti_path", "/opt/gentl/producer.cti")
        self.device_id = config.get("device_id", None)
        self.transport = TransportHarvesters(self.cti_path)
        self.connected = False
        logger.info(f"CameraATSensors3D initialized with CTI: {self.cti_path}")

    def connect(self):
        try:
            self.transport.initialize()
            self.transport.connect_device(self.device_id)
            self.connected = True
            logger.info("CameraATSensors3D connected successfully.")
        except Exception as e:
            raise CameraError(f"Failed to connect AT Sensors 3D camera: {e}")

    def disconnect(self):
        try:
            self.transport.disconnect_device()
            self.connected = False
            logger.info("CameraATSensors3D disconnected.")
        except Exception as e:
            raise CameraError(f"Failed to disconnect camera: {e}")

    def start_acquisition(self):
        self.transport.start_acquisition()

    def stop_acquisition(self):
        self.transport.stop_acquisition()

    def get_frame(self):
        return self.transport.get_frame()

    def configure(self, settings: dict):
        self.config.update(settings)
        logger.info("Camera configuration updated: %s", settings)
