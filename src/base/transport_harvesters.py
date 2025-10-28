"""
Transport layer using Harvesters SDK
------------------------------------
Provides device discovery, connection, and image acquisition via the GenTL interface.
"""

from typing import Optional, List, Dict, Any
from harvesters.core import Harvester, ImageAcquirer
from contextlib import contextmanager

from src.utils.error_handling import CameraError
from src.utils.logging_utils import get_logger

# Logging configuration
logger = get_logger("TransportHarvesters")


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
        self.harvester: Optional[Harvester] = None
        self.image_acquirer: Optional[ImageAcquirer] = None
        self.devices_list = []
        self._is_connected = False
        self._is_acquiring = False
        logger.debug(f"{self.__class__.__name__} initialized with CTI: {cti_path}")

    @property
    def is_connected(self) -> bool:
        """Check if device is connected."""
        return self._is_connected

    @property
    def is_acquiring(self) -> bool:
        """Check if acquisition is active."""
        return self._is_acquiring

    def initialize(self) -> None:
        """Initialize Harvester and load CTI file."""
        if self.harvester is not None:
            logger.error("Harvester already initialized.")
            return

        try:
            logger.debug(f"Loading CTI file: {self.cti_path}")
            self.harvester = Harvester()
            self.harvester.add_file(self.cti_path)
            self.harvester.update()
            logger.debug("Harvester initialized successfully.")
        except Exception as e:
            logger.exception("Failed to initialize Harvester.")
            raise CameraError(f"Failed to initialize Harvester: {e}")

    def list_devices(self) -> List[Dict[str, Any]]:
        """
        Return a list of available devices with their info.
        
        Returns:
            List of device info dictionaries
        """
        if not self.harvester:
            self.initialize()
            assert self.harvester is not None

        # Update list of devices
        self.harvester.update()
        
        if not self.harvester or not self.harvester.device_info_list:
            logger.error("No devices found.")
            self.devices_list = []
            return self.devices_list
        
        if self.devices_list:
            self.devices_list = []

        for idx, device_info in enumerate(self.harvester.device_info_list):
            self.devices_list.append({
                'index': idx,
                'id': device_info.id_,
                'vendor': device_info.vendor,
                'model': device_info.model,
                'serial_number': device_info.serial_number,
                'user_defined_name': device_info.user_defined_name
            })
            logger.debug(f"Found device {idx}: {device_info.model} (S/N: {device_info.serial_number})")
        
        logger.info(f"Total found devices: {len(self.harvester.device_info_list)}")
        logger.info(self.devices_list)
        
        return self.devices_list


    # -------------------------------
    # Connection methods
    # -------------------------------
    def connect_device(self, device_config: Optional[Dict[str, str]] = None) -> ImageAcquirer:
        """
        Connect to a device based on configuration dictionary.

        Priority order:
        1. user_defined_name (device_name)
        2. serial_number (device_serial)
        3. id defined as MAC::IP (device_id)
        4. index (if no other criteria matches or none specified)

        Args:
            device_config (Dict[str, str], optional): Dictionary with device identifiers:
                {
                    'user_defined_name': str,    # Device name
                    'serial_number': str,        # Device serial number
                    'id': str,                   # Device ID (MAC::IP format)
                }
                If None, connects to first available device.
        
        Returns:
            ImageAcquirer: Connected image acquirer object
        
        Raises:
            CameraError: If device cannot be found or connection fails
        """
        if self.is_connected:
            logger.warning("Device already connected. Disconnect first to execute this action.")
            return self.image_acquirer  # type: ignore

        try:
            if self.harvester is None:
                logger.warning("Harvester instance not found. Initializing...")
                self.initialize()
            assert self.harvester is not None

            # Update device list
            self.harvester.update()
            if not self.harvester.device_info_list:
                raise CameraError("No devices found by Harvester.")

            # If no config provided, connect to first device
            if not device_config:
                logger.info("No device configuration provided. Connecting to first available device.")
                self.image_acquirer = self.harvester.create(0)
                logger.info("Connected to first available device (index 0).")
                return self.image_acquirer

            # Get list of all devices
            devices = self.list_devices()
            
            # Find matching device
            for idx, device in enumerate(devices):
                # Check if any provided criteria matches the device
                if (('user_defined_name' in device_config and 
                    device_config['user_defined_name'] == device['user_defined_name']) or
                    ('serial_number' in device_config and 
                    device_config['serial_number'] == device['serial_number']) or
                    ('id' in device_config and 
                    device_config['id'] == device['id'])):
                    
                    self.image_acquirer = self.harvester.create(idx)
                    logger.info(f"Connected to device at index {idx}")
                    self._is_acquiring = True
                    return self.image_acquirer

            # If no device found
            raise CameraError(f"Could not find device with provided criteria: {device_config}")

        except Exception as e:
            logger.exception("Failed to connect device via Harvesters.")
            raise CameraError(f"Failed to connect device: {e}")

    def disconnect_device(self) -> None:
        """Disconnect from device and release resources."""
        try:
            if self._is_acquiring:
                logger.warning("Stopping acquisition before disconnect.")
                self.stop_acquisition()
            
            if self.image_acquirer:
                self.image_acquirer.destroy()
                self.image_acquirer = None
                logger.info("Image acquirer destroyed.")
            
            if self.harvester:
                self.harvester.reset()
                self.harvester = None
                logger.info("Harvester reset.")
            
            logger.info(f"{self.__class__.__name__} disconnected successfully.")
            self._is_acquiring = False
        except Exception as e:
            logger.exception("Error during transport disconnect.")
            raise CameraError(f"Failed to disconnect transport: {e}")


    # -------------------------------
    # Acquisition methods
    # -------------------------------
    def start_acquisition(self) -> None:
        """Start acquisition."""
        if not self.is_connected:
            raise CameraError("No device connected. Call connect_device() first.")
        
        if self._is_acquiring:
            logger.warning("Acquisition already started.")
            return
        
        try:
            assert self.image_acquirer is not None
            self.image_acquirer.start()
            self._is_acquiring = True
            logger.info("Acquisition started.")
        except Exception as e:
            raise CameraError(f"Failed to start acquisition: {e}")

    def stop_acquisition(self) -> None:
        """Stop acquisition."""
        if not self.is_connected:
            raise CameraError("No device connected.")
        
        if not self._is_acquiring:
            logger.warning("Acquisition not active.")
            return
        
        try:
            assert self.image_acquirer is not None
            self.image_acquirer.stop()
            self._is_acquiring = False
            logger.info("Acquisition stopped.")
        except Exception as e:
            raise CameraError(f"Failed to stop acquisition: {e}")

    def get_frame(self, timeout_ms: int = 5000):
        """
        Fetch a single frame and return the list of components from the buffer.
        
        Args:
            timeout_ms (int): Timeout in milliseconds for frame fetch
        
        Returns:
            List of buffer payload components
        """
        if not self.is_connected:
            raise CameraError("No device connected.")
        
        if not self._is_acquiring:
            raise CameraError("Acquisition not started. Call start_acquisition() first.")

        try:
            assert self.image_acquirer is not None
            with self.image_acquirer.fetch(timeout=timeout_ms / 1000.0) as buffer: # type: ignore
                if buffer.payload is None:
                    raise CameraError("Fetched buffer has no payload.")
                
                # Return list of components from buffer payload
                components = list(buffer.payload.components)
                logger.debug(f"Fetched frame with {len(components)} component(s).")
                return components
                
        except Exception as e:
            logger.exception("Failed to fetch frame from device.")
            raise CameraError(f"Failed to fetch frame: {e}")


    # -------------------------------
    # GenICam node values handling
    # -------------------------------    
    def set_node_value(self, node_name: str, value: Any) -> None:
        """
        Set a GenICam node value.

        Args:
            node_name (str): Name of the GenICam node
            value: Value to set
        """
        if not self.image_acquirer:
            raise CameraError("Device not connected")
            
        try:
            node = self.image_acquirer.remote_device.node_map.get_node(node_name)
            if node and node.is_writable:
                node.value = value
                logger.debug(f"Node {node_name} set to {value}")
            else:
                raise CameraError(f"Node {node_name} is not writable")
        except Exception as e:
            raise CameraError(f"Failed to set node {node_name}: {e}")

    def get_node_value(self, node_name: str) -> Any:
        """
        Get a GenICam node value.

        Args:
            node_name (str): Name of the GenICam node

        Returns:
            Any: Value of the node
        """
        if not self.image_acquirer:
            raise CameraError("Device not connected")
            
        try:
            node = self.image_acquirer.remote_device.node_map.get_node(node_name)
            if node and node.is_readable:
                return node.value
            else:
                raise CameraError(f"Node {node_name} is not readable")
        except Exception as e:
            raise CameraError(f"Failed to get node {node_name}: {e}")


    # -------------------------------
    # Context manager support
    # -------------------------------
    @contextmanager
    def acquisition_context(self):
        """
        Context manager for automatic acquisition start/stop.
        
        Usage:
            with transport.acquisition_context():
                frame = transport.get_frame()
        """
        self.start_acquisition()
        try:
            yield
        finally:
            self.stop_acquisition()

    def __enter__(self):
        """Support for 'with' statement."""
        if not self.is_connected:
            self.connect_device()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Cleanup when exiting 'with' block."""
        self.disconnect_device()
        return False  # Don't suppress exceptions