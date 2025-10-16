from abc import ABC, abstractmethod
from typing import Any
import logging

logger = logging.getLogger("harvestersSDK.CameraBase")

class CameraBase(ABC):
    """
    Abstract base class for all camera types.
    Defines the common interface for connection, acquisition, and parameter management.
    """

    def __init__(self, config: dict):
        """
        Initialize the camera with a configuration dictionary.

        Args:
            config (dict): Camera-specific configuration parameters
        """
        self.config = config
        self.connected = False
        self.acquiring = False
        logger.info(f"{self.__class__.__name__} initialized with config: {config}")

    # -------------------------------
    # Abstract methods
    # -------------------------------

    @abstractmethod
    def connect(self) -> None:
        """Connect to the camera."""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Disconnect from the camera."""
        pass

    @abstractmethod
    def start_acquisition(self) -> None:
        """Start image acquisition."""
        pass

    @abstractmethod
    def stop_acquisition(self) -> None:
        """Stop image acquisition."""
        pass

    @abstractmethod
    def get_frame(self) -> Any:
        """
        Capture a single frame from the camera.

        Returns:
            Any: Image data or frame object (depends on implementation)
        """
        pass

    # -------------------------------
    # Optional generic parameter handling
    # -------------------------------
    def set_parameter(self, name: str, value: Any) -> None:
        """
        Set a generic camera parameter.

        Args:
            name (str): Parameter name
            value (Any): Parameter value
        """
        if not self.connected:
            logger.warning("Camera not connected. Parameter will be stored but not applied yet.")
        self.config[name] = value
        logger.info(f"Parameter set: {name} = {value}")

    def get_parameter(self, name: str) -> Any:
        """
        Get a generic camera parameter.

        Args:
            name (str): Parameter name

        Returns:
            Any: Parameter value
        """
        return self.config.get(name, None)
