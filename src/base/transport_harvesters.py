"""
Transport layer using Harvesters SDK
------------------------------------
Provides device discovery, connection, and image acquisition via the GenTL interface.
"""

from typing import Optional, List, Dict, Any, Union
from harvesters.core import Harvester, ImageAcquirer
from contextlib import contextmanager

from src.utils.error_handling import (
    CameraError,
    ConnectionError,
    AcquisitionError,
    ParameterError,
)
from src.utils.logging_utils import get_logger

# Logging configuration
logger = get_logger("TransportHarvesters")


class TransportHarvesters:
    """
    Transport layer for Harvesters SDK interaction.
    - Initializes Harvester and loads CTI file
    - Discovers devices
    - Creates/destroys ImageAcquirers (caller manages lifetime)
    - Fetch frames, read/write GenICam nodes
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
        self.devices_list: List[Dict[str, Any]] = []
        self._is_connected = False
        self._is_acquiring = False
        logger.debug(f"TransportHarvesters initialized with CTI: {cti_path}")

    @property
    def is_connected(self) -> bool:
        """Check if device is connected."""
        return self._is_connected

    @property
    def is_acquiring(self) -> bool:
        """Check if acquisition is active."""
        return self._is_acquiring


    # -------------------------------
    # Initialization & Device Discovery
    # -------------------------------
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
            raise ConnectionError(f"Failed to initialize Harvester: {e}")

    def list_devices(self, raise_on_error: bool = True) -> List[Dict[str, Any]]:
        """
        Return a list of available devices with their info.
        If raise_on_error is False, returns [] on initialization failure.
        
        Returns:
            List of device info dictionaries
        """
        if not self.harvester:
            try:
                self.initialize()
            except CameraError:
                logger.exception("Failed to initialize Harvester while listing devices.")
                if raise_on_error:
                    raise
                return []
        assert self.harvester is not None

        # Update list of devices
        try:
            self.harvester.update()
        except Exception as e:
            logger.exception("Failed to update Harvester device list.")
            if raise_on_error:
                raise ConnectionError(f"Failed to update device info: {e}")
            return []

        # Get list of devices from Harvesters
        device_info_list = getattr(self.harvester, "device_info_list", []) or []
        if not device_info_list:
            logger.info("No devices found.")
            return []        
        
        # Reset cached devices
        self.devices_list = []

        for idx, device_info in enumerate(self.harvester.device_info_list):
            self.devices_list.append({
                'index': idx,
                'id': device_info.id_, # getattr(device_info, "id_", None),
                'vendor': device_info.vendor,
                'model': device_info.model,
                'serial_number': device_info.serial_number,
                'user_defined_name': device_info.user_defined_name
            })
            logger.debug(f"Found device {idx}: Name = {device_info.user_defined_name}; "
                         f"Model = {device_info.model}; S/N = {device_info.serial_number}")
        
        logger.info(f"Total found devices: {len(self.harvester.device_info_list)}")
        logger.debug(f"Complete device list: {self.devices_list}")        
        return self.devices_list


    # -------------------------------
    # Image acquirer lifecycle
    # -------------------------------
    def create_image_acquirer(self, selector: Union[int, Dict[str, Any]]) -> ImageAcquirer:
        """
        Create and return an ImageAcquirer.
        Selector can be an index (int) or dict (e.g. {'user_defined_name': '...'}).
        Caller is responsible for managing lifetime (start/stop/destroy).
        """
        if self.harvester is None:
            self.initialize()
        assert self.harvester is not None
        
        try:
            ia = self.harvester.create(selector)
            logger.debug(f"Created ImageAcquirer (selector={selector})")
            return ia
        except Exception as e:
            logger.exception("Failed to create ImageAcquirer.")
            raise ConnectionError(f"Failed to create ImageAcquirer: {e}")

    def start_image_acquirer(self, ia: ImageAcquirer) -> None:
        """Start the provided ImageAcquirer."""
        try:
            ia.start()
            logger.debug("Started ImageAcquirer.")
        except Exception as e:
            logger.exception("Failed to start ImageAcquirer.")
            raise AcquisitionError(f"Failed to start ImageAcquirer: {e}")

    def stop_image_acquirer(self, ia: ImageAcquirer) -> None:
        """Stop the provided ImageAcquirer."""
        try:
            ia.stop()
            logger.debug("Stopped ImageAcquirer.")
        except Exception as e:
            logger.exception("Failed to stop ImageAcquirer.")
            raise AcquisitionError(f"Failed to stop ImageAcquirer: {e}")

    def destroy_image_acquirer(self, ia: ImageAcquirer) -> None:
        """Destroy the provided ImageAcquirer."""
        try:
            ia.destroy()
            logger.debug("Destroyed ImageAcquirer.")
        except Exception as e:
            logger.exception("Failed to destroy ImageAcquirer.")
            raise ConnectionError(f"Failed to destroy ImageAcquirer: {e}")


    # -------------------------------
    # Fetch image acquirer
    # -------------------------------
    def fetch_from_acquirer(self, ia: ImageAcquirer, timeout_ms: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Fetch one buffer from the provided ImageAcquirer and return components list.
        Raises AcquisitionError on failure.
        """
        try:
            if timeout_ms is not None:
                ctx = ia.fetch(timeout=int(timeout_ms / 1000.0))
            else:
                ctx = ia.fetch()
            with ctx as buffer:  # type: ignore
                payload = getattr(buffer, "payload", None)
                if payload is None:
                    raise AcquisitionError("Fetched buffer has no payload.")
                comps_out = []
                for comp in payload.components:
                    comps_out.append({
                        "width": getattr(comp, "width", None),
                        "height": getattr(comp, "height", None),
                        "data": getattr(comp, "data", None),
                        "dtype": getattr(getattr(comp, "data", None), "dtype", None),
                        "data_format": getattr(comp, "data_format", None),
                        "component_type": type(comp).__name__,
                    })
                logger.debug(f"Fetched {len(comps_out)} component(s) from acquirer.")
                return comps_out
        except AcquisitionError:
            raise
        except Exception as e:
            logger.exception("Failed to fetch from ImageAcquirer.")
            raise AcquisitionError(f"Failed to fetch from ImageAcquirer: {e}")


    # -------------------------------
    # GenICam node values handling
    # -------------------------------    
    def set_node_value(self, ia: ImageAcquirer, node_name: str, value: Any) -> None:
        """
        Set GenICam node value on the remote_device of the provided acquirer.
        """
        try:
            node_map = ia.remote_device.node_map
            node = node_map.get_node(node_name)
            if node is None:
                raise ParameterError(f"Node {node_name} not found.")
            if not getattr(node, "is_writable", True):
                raise ParameterError(f"Node {node_name} is not writable.")
            node.value = value
            logger.debug(f"Set node {node_name} = {value}")
        except ParameterError:
            raise
        except Exception as e:
            logger.exception("Failed to set node value.")
            raise ParameterError(f"Failed to set node {node_name}: {e}")

    def get_node_value(self, ia: ImageAcquirer, node_name: str) -> Any:
        """
        Get GenICam node value from the provided acquirer.
        """
        try:
            node_map = ia.remote_device.node_map
            node = node_map.get_node(node_name)
            if node is None:
                raise ParameterError(f"Node {node_name} not found.")
            if not getattr(node, "is_readable", True):
                raise ParameterError(f"Node {node_name} is not readable.")
            val = node.value
            logger.debug(f"Got node {node_name} = {val}")
            return val
        except ParameterError:
            raise
        except Exception as e:
            logger.exception("Failed to get node value.")
            raise ParameterError(f"Failed to get node {node_name}: {e}")


    # -------------------------------
    # Cleanup & Reset
    # -------------------------------
    def reset(self) -> None:
        """Reset and cleanup Harvester (does NOT destroy acquirers — caller responsibility)."""
        try:
            if self.harvester:
                try:
                    self.harvester.reset()
                except Exception:
                    logger.debug("harvester.reset() failed.")
                self.harvester = None
            logger.info("Transport reset.")
        except Exception as e:
            logger.exception("Error during transport reset.")
            raise ConnectionError(f"Failed to reset transport: {e}")

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Cleanup when exiting 'with' block."""
        self.reset()
        return False  # Don't suppress exceptions