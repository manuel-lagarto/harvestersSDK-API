"""
Transport layer using Harvesters SDK
------------------------------------
Provides device discovery, connection, and image acquisition via the GenTL interface.
"""

import logging
from typing import Optional
from harvesters.core import Harvester

from src.utils.error_handling import CameraError

logger = logging.getLogger("harvestersSDK.TransportHarvesters")


class TransportHarvesters:
    """
    Transport layer implemented using the Harvesters library.
    Handles GenTL Producer (.cti) loading, device connection, and frame retrieval.
    """

    def __init__(self, cti_path: str):
        """
        Initialize the Harvesters transport layer.

        Args:
            cti_path (str): Path to the GenTL Producer (.cti) file.
        """
        self.cti_path = cti_path
        self.harvester = None
        self.image_acquirer = None
        logger.info(f"TransportHarvesters initialized with CTI: {cti_path}")


    def initialize(self) -> None:
        """Initialize Harvester and load CTI file."""
        try:
            logger.info(f"Loading CTI file: {self.cti_path}")
            self.harvester = Harvester()
            self.harvester.add_file(self.cti_path)
            self.harvester.update()
            logger.info("Harvester initialized successfully.")
        except Exception as e:
            logger.exception("Failed to initialize Harvester.")
            raise CameraError(f"Failed to initialize Harvester: {e}")


    def list_devices(self):
        """Return a list of available devices."""
        if not self.harvester:
            raise CameraError("Harvester not initialized.")
        return self.harvester.device_info_list


    def connect_device(self, device_id: Optional[str] = None):
        """
        Connect to a device by id number (device_id) or by index 0 if None.

        Args:
            device_id (str, optional): ID number of the target device.
        """
        try:
            if self.harvester is None:
                self.initialize()
            assert self.harvester is not None

            if not self.harvester.device_info_list:
                raise CameraError("No devices found by Harvester.")

            if device_id:
                logger.info(f"Connecting to device with id: {device_id}")
                self.image_acquirer = self.harvester.create({'user_defined_name ': device_id})
            else:
                logger.info("Connecting to first available device.")
                self.image_acquirer = self.harvester.create(0)

            logger.info("Device connected successfully via Harvesters.")
            return self.image_acquirer
        except Exception as e:
            logger.exception("Failed to connect device via Harvesters.")
            raise CameraError(f"Failed to connect device: {e}")


    def disconnect_device(self):
        """Disconnect from device and release resources."""
        try:
            if self.image_acquirer:
                self.image_acquirer.destroy()
                self.image_acquirer = None
            if self.harvester:
                self.harvester.reset()
                self.harvester = None
            logger.info("TransportHarvesters disconnected and reset.")
        except Exception as e:
            logger.exception("Error during transport disconnect.")
            raise CameraError(f"Failed to disconnect transport: {e}")


    def start_acquisition(self):
        """Start acquisition."""
        if not self.image_acquirer:
            raise CameraError("No device connected.")
        
        try:
            self.image_acquirer.start()
            logger.info("Acquisition started.")
        except Exception as e:
            raise CameraError(f"Failed to start acquisition: {e}")


    def stop_acquisition(self):
        """Stop acquisition."""
        if not self.image_acquirer:
            raise CameraError("No device connected.")
        
        try:
            self.image_acquirer.stop()
            logger.info("Acquisition stopped.")
        except Exception as e:
            raise CameraError(f"Failed to stop acquisition: {e}")


    def get_frame(self):
        """Fetch a single frame and return the list of components from the buffer."""
        if not self.image_acquirer:
            raise CameraError("No device connected.")

        try:
            with self.image_acquirer.fetch() as buffer: # type: ignore
                if buffer.payload is None:
                    raise CameraError("Fetched buffer has no payload.")
                
                # List of components from buffer payload
                components = list(buffer.payload.components)                
                return components
        except Exception as e:
            logger.exception("Failed to fetch frame from device.")
            raise CameraError(f"Failed to fetch frame: {e}")
