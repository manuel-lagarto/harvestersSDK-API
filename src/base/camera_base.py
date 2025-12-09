"""
Abstract base class for camera types
------------------------------------
Manages ImageAcquirers with selective control per acquirer.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List

from src.base.transport_harvesters import TransportHarvesters, ImageAcquirer
from src.utils.error_handling import (
    CameraError,
    ConnectionError,
    AcquisitionError,
    ParameterError,
)
from src.utils.logging_utils import get_logger

# Logging configuration
logger = get_logger("CameraBase")


class CameraBase(ABC):
    """
    Abstract base class for all camera types.
    Manages single-sensor connection, acquisition, and parameter access via TransportHarvesters.
    """

    def __init__(self, config: dict):
        """
        Initialize camera with configuration.

        Args:
            config (dict): Configuration dictionary with keys:
                - cti_path (str): Path to GenTL Producer .cti file
                - device_name (str, optional): Device user_defined_name
                - device_serial (str, optional): Device serial_number
                - device_id (str, optional): Device id (MAC::IP format)
                - timeout_ms (int, optional): Frame timeout in milliseconds
        """
        self.config = config
        self.timeout_ms = config.get("timeout_ms", 5000)
        self.strict = True # If True, raise exceptions; if False, return fallback

        # Map user-friendly config keys to Harvester keys
        # TODO: add index option
        self.device_config = {}
        if "device_name" in config:
            self.device_config["user_defined_name"] = config["device_name"]
        if "device_serial" in config:
            self.device_config["serial_number"] = config["device_serial"]
        if "device_id" in config:
            self.device_config["id"] = config["device_id"]

        # Initialize transport layer
        cti_path = config.get("cti_path", "/opt/cvb/drivers/genicam/libGevTL.cti")
        if not cti_path:
            raise CameraError("cti_path is required in config")
        self._transport = TransportHarvesters(cti_path)

        # Generic multi-acquirer state
        self._acquirers: List[ImageAcquirer] = []  # List of all managed acquirers
        self._acquiring_states: Dict[int, bool] = {}  # Track acquiring state per acquirer
        self._initialized = False  # Track if transport has been initialized

        logger.debug(f"CameraBase initialized with config: {self.device_config}.")


    # -------------------------------
    # Properties for state checking
    # -------------------------------
    @property
    def connected(self) -> bool:
        return len(self._acquirers) > 0

    @property
    def acquiring(self) -> bool:
        """True if any acquirer is acquiring."""
        return any(self._acquiring_states.values())

    def _ensure_transport_initialized(self) -> None:
        """Initialize transport layer if not already initialized."""
        if not self._initialized:
            try:
                self._transport.initialize()
                self._initialized = True
                logger.debug("Transport layer initialized.")
            except Exception as e:
                logger.exception("Failed to initialize transport.")
                raise ConnectionError(f"Failed to initialize transport: {e}")


    # -------------------------------
    # Connection methods
    # -------------------------------
    def connect(self, device_selector: Optional[Any] = None) -> ImageAcquirer:
        """
        Create and return an ImageAcquirer for the given device selector.
        Initializes transport on first call.
        Caller is responsible for storing the returned acquirer.

        Args:
            device_selector: Device selector (int index or dict with keys like 'user_defined_name').
                           If None, uses self.device_config.

        Returns:
            ImageAcquirer: The created acquirer handle.
        """
        try:
            # Ensure transport initialized (only happens once)
            self._ensure_transport_initialized()

            # Use provided selector or fall back to device_config
            selector = device_selector or self.device_config or 0

            # Create acquirer via transport
            ia = self._transport.create_image_acquirer(selector)
            
            # Track acquirer and its state
            self._acquirers.append(ia)
            self._acquiring_states[id(ia)] = False
            
            logger.info(f"Created ImageAcquirer {id(ia)} (selector={selector}). Total acquirers: {len(self._acquirers)}")
            return ia
        except Exception as e:
            logger.exception("Failed to connect/create acquirer.")
            raise ConnectionError(f"Failed to connect: {e}")

    def disconnect(self) -> None:
        """Disconnect and cleanup all acquirers."""
        try:
            # Stop any active acquisitions
            for ia in list(self._acquirers):
                if self._acquiring_states.get(id(ia), False):
                    try:
                        self._transport.stop_image_acquirer(ia)
                    except Exception:
                        pass
            
            # Destroy all acquirers
            for ia in list(self._acquirers):
                try:
                    self._transport.destroy_image_acquirer(ia)
                except Exception:
                    logger.debug("Error destroying acquirer during disconnect.")
            
            self._acquirers = []
            self._acquiring_states = {}
            self._transport.reset()
            self._initialized = False
            logger.info("Camera disconnected successfully.")
        except Exception as e:
            logger.exception("Failed to disconnect camera.")
            raise ConnectionError(f"Failed to disconnect camera: {e}")

    # -------------------------------
    # Acquisition methods
    # -------------------------------
    def start_acquisition(self, acquirer_index: int = 0) -> None:
        """
        Start acquisition on a specific acquirer.

        Args:
            acquirer_index (int): Index in self._acquirers (default 0).
        """
        if not self._acquirers:
            raise CameraError("No acquirers configured.")
        if acquirer_index >= len(self._acquirers):
            raise AcquisitionError(f"Acquirer index {acquirer_index} out of range.")
        
        ia = self._acquirers[acquirer_index]
        if self._acquiring_states.get(id(ia), False):
            logger.warning(f"Acquirer {acquirer_index} already acquiring.")
            return
        
        try:
            self._transport.start_image_acquirer(ia)
            self._acquiring_states[id(ia)] = True
            logger.info(f"Started acquisition on acquirer {acquirer_index}.")
        except Exception as e:
            logger.exception("Failed to start acquisition.")
            raise AcquisitionError(f"Failed to start acquisition on acquirer {acquirer_index}: {e}")

    def stop_acquisition(self, acquirer_index: int = 0) -> None:
        """
        Stop acquisition on a specific acquirer.

        Args:
            acquirer_index (int): Index in self._acquirers (default 0).
        """
        if not self._acquirers:
            raise CameraError("No acquirers configured.")
        if acquirer_index >= len(self._acquirers):
            raise AcquisitionError(f"Acquirer index {acquirer_index} out of range.")
        
        ia = self._acquirers[acquirer_index]
        if not self._acquiring_states.get(id(ia), False):
            logger.warning(f"Acquirer {acquirer_index} not acquiring.")
            return
        
        try:
            self._transport.stop_image_acquirer(ia)
            self._acquiring_states[id(ia)] = False
            logger.info(f"Stopped acquisition on acquirer {acquirer_index}.")
        except Exception as e:
            logger.exception("Failed to stop acquisition.")
            raise AcquisitionError(f"Failed to stop acquisition on acquirer {acquirer_index}: {e}")

    def get_frame(self, acquirer_index: int = 0, timeout_ms: Optional[int] = None) -> Any:
        """
        Fetch frame from a specific acquirer.

        Args:
            acquirer_index (int): Index in self._acquirers (default 0).
            timeout_ms (int, optional): Timeout in milliseconds.

        Returns:
            Frame data from the specified acquirer.
        """
        if not self._acquirers:
            raise CameraError("No acquirers configured.")
        if acquirer_index >= len(self._acquirers):
            raise AcquisitionError(f"Acquirer index {acquirer_index} out of range.")
        if not self._acquiring_states.get(id(self._acquirers[acquirer_index]), False):
            raise CameraError(f"Acquirer {acquirer_index} not acquiring.")
        
        try:
            ia = self._acquirers[acquirer_index]
            return self._transport.fetch_from_acquirer(ia, timeout_ms=timeout_ms or self.timeout_ms)
        except Exception as e:
            logger.exception("Failed to fetch frame.")
            if self.strict:
                raise AcquisitionError(f"Failed to fetch frame from acquirer {acquirer_index}: {e}")
            return None


    # -------------------------------
    # Acquisition lifecycle
    # -------------------------------
    def acquire_frame(self, acquirer_index: int = 0, timeout_ms: Optional[int] = None) -> Any:
        """
        Acquire a single frame with automatic lifecycle management.
        
        Lifecycle: start_acquisition() -> get_frame() -> stop_acquisition()

        Args:
            acquirer_index (int): Index in self._acquirers (default 0).
            timeout_ms (int, optional): Timeout in milliseconds.

        Returns:
            Frame data from the specified acquirer.

        Raises:
            CameraError: If acquisition fails at any stage.

        Example:
            >>> frame = camera.acquire_frame(acquirer_index=0)
        """
        logger.info(f"Acquiring frame from acquirer {acquirer_index}...")
        try:
            self.start_acquisition(acquirer_index=acquirer_index)
            frame = self.get_frame(acquirer_index=acquirer_index, timeout_ms=timeout_ms)
            self.stop_acquisition(acquirer_index=acquirer_index)
            logger.info("Frame acquired successfully.")
            return frame
        except Exception as e:
            logger.exception("Frame acquisition failed.")
            try:
                if acquirer_index < len(self._acquirers):
                    if self._acquiring_states.get(id(self._acquirers[acquirer_index]), False):
                        self.stop_acquisition(acquirer_index=acquirer_index)
            except Exception:
                pass
            raise CameraError(f"Failed to acquire frame: {e}")


    # -------------------------------
    # Generic parameter handling
    # -------------------------------
    def set_parameter(self, param_name: str, value: Any, acquirer_index: int = 0) -> None:
        """
        Set GenICam parameter on a specific acquirer.

        Args:
            param_name (str): Parameter name (GenICam node name)
            value (Any): Parameter value to set
            acquirer_index (int): Index in self._acquirers (default 0)
        """
        if not self._acquirers:
            raise CameraError("No acquirers configured.")
        if acquirer_index >= len(self._acquirers):
            raise ParameterError(f"Acquirer index {acquirer_index} out of range.")
        try:
            ia = self._acquirers[acquirer_index]
            self._transport.set_node_value(ia, param_name, value)
            logger.debug(f"Set {param_name}={value} on acquirer {acquirer_index}.")
        except Exception as e:
            logger.exception(f"Failed to set parameter {param_name}.")
            if self.strict:
                raise ParameterError(f"Failed to set parameter {param_name}: {e}")

    def get_parameter(self, param_name: str, acquirer_index: int = 0) -> Any:
        """
        Get GenICam parameter from a specific acquirer.

        Args:
            param_name (str): Parameter name (GenICam node name)
            acquirer_index (int): Index in self._acquirers (default 0)

        Returns:
            Any: Parameter value
        """
        if not self._acquirers:
            raise CameraError("No acquirers configured.")
        if acquirer_index >= len(self._acquirers):
            raise ParameterError(f"Acquirer index {acquirer_index} out of range.")
        try:
            ia = self._acquirers[acquirer_index]
            return self._transport.get_node_value(ia, param_name)
        except Exception as e:
            logger.exception(f"Failed to get parameter {param_name}.")
            if self.strict:
                raise ParameterError(f"Failed to get parameter {param_name}: {e}")
            return None


    # -------------------------------
    # Context manager support
    # -------------------------------
    # def __enter__(self):
    #     """Support for 'with' statement."""
    #     if not self.connected:
    #         self.connect()
    #     return self

    # def __exit__(self, exc_type, exc_val, exc_tb):
    #     """Cleanup when exiting 'with' block."""
    #     if self.acquiring:
    #         self.stop_acquisition()
    #     if self.connected:
    #         self.disconnect()
    #     return False  # Don't suppress exceptions

    # def __del__(self):
    #     """Destructor to ensure cleanup."""
    #     try:
    #         if self.acquiring:
    #             self.stop_acquisition()
    #         if self.connected:
    #             self.disconnect()
    #     except:
    #         pass  # Avoid exceptions in destructor