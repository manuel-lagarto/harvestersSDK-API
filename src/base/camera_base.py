from abc import ABC, abstractmethod
from typing import Any, Optional, Dict

from src.base.transport_harvesters import TransportHarvesters
from src.utils.error_handling import CameraError
from src.utils.logging_utils import get_logger

# Logging configuration
logger = get_logger("CameraBase")


class CameraBase(ABC):
    """
    Abstract base class for all camera types.
    Defines the common interface for connection, acquisition, and parameter management.
    """

    def __init__(self, config: dict):
        """
        Initialize the camera with a configuration dictionary.

        Args:
            config (dict): Camera configuration with keys:
                - cti_path (str): Path to GenTL Producer .cti file
                - user_defined_name (str, optional): Device user defined name
                - serial_number (str, optional): Device serial number
                - id (str, optional): Device ID (MAC::IP format)
                - timeout_ms (int, optional): Frame timeout in milliseconds
        """
        self.config = config
        self.timeout_ms = config.get("timeout_ms", 5000)

        # Extract device configuration
        self.device_config: Dict[str, str] = {
            'user_defined_name': config.get('device_name', ''),
            'serial_number': config.get('device_serial', ''),
            'id': config.get('device_id', ''),
        }
        # Remove empty values
        self.device_config = {k: v for k, v in self.device_config.items() if v}

        # Initialize transport layer
        try:
            cti_path = config.get("cti_path")
            if not cti_path:
                raise CameraError("CTI path not provided in configuration")
            
            self._transport = TransportHarvesters(cti_path)
            logger.info(f"{self.__class__.__name__} initialized with transport layer")
            logger.debug(f"Configuration: CTI={cti_path}, Device={self.device_config}")        
        except Exception as e:
            logger.error(f"Failed to initialize transport layer: {e}")
            self._transport = None
            raise CameraError(f"Transport layer initialization failed: {e}")


    # -------------------------------
    # Properties for state checking
    # -------------------------------
    @property
    def connected(self) -> bool:
        """Check if camera is connected (delegates to transport layer)."""
        return self._transport is not None and self._transport.is_connected
    
    @property
    def acquiring(self) -> bool:
        """Check if camera is acquiring (delegates to transport layer)."""
        return self._transport is not None and self._transport.is_acquiring


    # -------------------------------
    # Connection methods
    # -------------------------------
    def connect(self) -> None:
        """
        Connect to the camera using the transport layer.
        Uses device configuration from initialization if provided.
        
        Raises:
            CameraError: If transport is not set or connection fails
        """
        if self._transport is None:
            raise CameraError("Transport layer not initialized")
        
        try:
            self._transport.initialize()

            # Pass device configuration if available, otherwise None
            config_to_use = self.device_config if self.device_config else None
            self._transport.connect_device(config_to_use)
        except Exception as e:
            raise CameraError(f"Failed to connect camera: {e}")

    def disconnect(self) -> None:
        """
        Disconnect from the camera using the transport layer.
        Raises CameraError if transport is not set or disconnection fails.
        """
        if self._transport is None:
            raise CameraError("Transport layer not initialized")
        
        try:
            if self.acquiring:
                self.stop_acquisition()
            self._transport.disconnect_device()
            logger.info(f"{self.__class__.__name__} disconnected successfully")
        except Exception as e:
            raise CameraError(f"Failed to disconnect camera: {e}")

    # -------------------------------
    # Acquisition methods
    # -------------------------------
    def start_acquisition(self) -> None:
        """
        Start image acquisition using the transport layer.
        Raises CameraError if camera is not connected or start fails.
        """
        if not self.connected:
            raise CameraError("Camera not connected")
        
        try:
            self._transport.start_acquisition() # type: ignore
            logger.info(f"{self.__class__.__name__} started acquisition")
        except Exception as e:
            raise CameraError(f"Failed to start acquisition: {e}")

    def stop_acquisition(self) -> None:
        """
        Stop image acquisition using the transport layer.
        Raises CameraError if camera is not connected or stop fails.
        """
        if not self.connected:
            raise CameraError("Camera not connected")
        
        try:
            self._transport.stop_acquisition() # type: ignore
            logger.info(f"{self.__class__.__name__} stopped acquisition")
        except Exception as e:
            raise CameraError(f"Failed to stop acquisition: {e}")

    def get_frame(self, timeout_ms: Optional[int] = None) -> Any:
        """
        Capture a single frame from the camera using the transport layer.
        
        Args:
            timeout_ms (int, optional): Timeout in milliseconds. Uses transport default if None.
            
        Returns:
            Any: Frame data from the transport layer
            
        Raises:
            CameraError: If camera is not connected/acquiring or frame capture fails
        """
        if not self.connected:
            raise CameraError("Camera not connected")
        
        if not self.acquiring:
            raise CameraError("Acquisition not started")
            
        try:
            frame = self._transport.get_frame(timeout_ms=timeout_ms) # type: ignore
            return frame
        except Exception as e:
            raise CameraError(f"Failed to get frame: {e}")


    # -------------------------------
    # Generic parameter handling
    # -------------------------------
    def set_parameter(self, param_name: str, value: Any) -> None:
        """
        Set a camera parameter via GenICam node.

        Args:
            param_name (str): Parameter name (GenICam node name)
            value: Parameter value to set
        """
        if not self.connected:
            raise CameraError("Camera not connected")
        
        try:
            self._transport.set_node_value(param_name, value) # type: ignore
            logger.debug(f"Parameter {param_name} set to {value}")
        except Exception as e:
            raise CameraError(f"Failed to set parameter {param_name}: {e}")

    def get_parameter(self, param_name: str) -> Any:
        """
        Get a camera parameter via GenICam node.

        Args:
            param_name (str): Parameter name (GenICam node name)

        Returns:
            Any: Parameter value
        """
        if not self.connected:
            raise CameraError("Camera not connected")
        
        try:
            value = self._transport.get_node_value(param_name) # type: ignore
            logger.debug(f"Parameter {param_name} read: {value}")
            return value
        except Exception as e:
            raise CameraError(f"Failed to get parameter {param_name}: {e}")


    # -------------------------------
    # Context manager support
    # -------------------------------
    def __enter__(self):
        """Support for 'with' statement."""
        if not self.connected:
            self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Cleanup when exiting 'with' block."""
        if self.acquiring:
            self.stop_acquisition()
        if self.connected:
            self.disconnect()
        return False  # Don't suppress exceptions

    def __del__(self):
        """Destructor to ensure cleanup."""
        try:
            if self.acquiring:
                self.stop_acquisition()
            if self.connected:
                self.disconnect()
        except:
            pass  # Avoid exceptions in destructor