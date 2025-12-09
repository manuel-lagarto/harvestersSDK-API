"""
Vendor-specific implementation: AT Sensors 3D Cameras
---------------------------------------------
Implements camera-specific logic using the Harvesters transport layer.
Supports single-sensor and dual-sensor configurations.
"""

from typing import Optional, Dict, Any, List

from src.base.camera_base import CameraBase
from src.utils.error_handling import (
    CameraError,
    ConnectionError,
    AcquisitionError,
    ParameterError,
)
from src.utils.logging_utils import get_logger

# Logging configuration
logger = get_logger("CameraATSensors3D")


class CameraATSensors3D(CameraBase):
    """
    AT Sensors 3D camera with support for single or dual-sensor configurations.
    Inherits generic multi-acquirer support from CameraBase.
    """    

    # GenICam node names specific to AT Sensors cameras
    NODES = {
        "exposure": "ExposureTime",
        "gain": "Gain",
        "pixel_format": "PixelFormat",
        "width": "Width",
        "height": "Height",
        "offset_x": "OffsetX",
        "offset_y": "OffsetY"
    }

    def __init__(self, config: dict):
        """
        Initialize AT Sensors 3D camera.
        
        Args:
            config (dict): Configuration dictionary passed to CameraBase
        """
        super().__init__(config=config)
        logger.debug(f"CameraATSensors3D initialized.")


    # -------------------------------
    # Camera setup
    # -------------------------------
    def setup(self, dual_configuration: bool = False, device_selectors: Optional[List[Any]] = None) -> None:
        """
        Setup camera configuration (single or dual sensors).

        Args:
            dual_configuration (bool): If True, setup dual-sensor mode; else single.
            device_selectors (List[Any], optional): List of selectors (index or dict).
                - Single: [primary_selector] or None (uses config["device_name"]).
                - Dual: [primary_selector, secondary_selector].
        """
        try:
            # Clear any previous acquirers
            if self._acquirers:
                self.disconnect()

            if not dual_configuration:
                # Single-sensor mode: use base connect()
                selector = (device_selectors[0] if device_selectors 
                           else self.device_config or 0)
                self.connect(device_selector=selector)
                logger.info("Configured single-sensor mode (acquirer 0).")
                return

            # Dual-sensor: create two acquirers (indices 0 and 1)
            if not device_selectors or len(device_selectors) < 2:
                raise CameraError("Dual configuration requires 2 device selectors.")
            
            self.connect(device_selector=device_selectors[0])  # index 0 (primary)
            self.connect(device_selector=device_selectors[1])  # index 1 (secondary)
            logger.info("Configured dual-sensor mode (acquirers 0 and 1).")
        except Exception as e:
            logger.exception("setup failed.")
            raise CameraError(f"setup failed: {e}")


    # -------------------------------
    # Dual-sensor acquisition overrides
    # -------------------------------
    def start_dual_acquisition(self) -> None:
        """Start acquisition on both sensors (dual-sensor mode)."""
        if len(self._acquirers) < 2:
            raise CameraError("Dual-sensor mode not configured.")
        self.start_acquisition(acquirer_index=0)
        self.start_acquisition(acquirer_index=1)
        logger.info("Started dual-sensor acquisition.")

    def stop_dual_acquisition(self) -> None:
        """Stop acquisition on both sensors (dual-sensor mode)."""
        if len(self._acquirers) < 2:
            raise CameraError("Dual-sensor mode not configured.")
        self.stop_acquisition(acquirer_index=0)
        self.stop_acquisition(acquirer_index=1)
        logger.info("Stopped dual-sensor acquisition.")
    
    def get_frames_dual(self, timeout_ms: Optional[int] = None) -> Dict[str, Any]:
        """
        Fetch frames from both sensors.

        Args:
            timeout_ms (int, optional): Timeout in milliseconds.
        
        Returns:
            {'primary': frame0, 'secondary': frame1}
        """
        if len(self._acquirers) < 2:
            raise CameraError("Dual-sensor mode not configured.")
        try:
            primary = self.get_frame(acquirer_index=0, timeout_ms=timeout_ms)
            secondary = self.get_frame(acquirer_index=1, timeout_ms=timeout_ms)
            return {"primary": primary, "secondary": secondary}
        except Exception as e:
            logger.exception("Failed to fetch dual frames.")
            raise AcquisitionError(f"Failed to fetch dual frames: {e}")


    # -------------------------------
    # Acquisition lifecycle
    # -------------------------------
    def acquire_frames_dual(self, timeout_ms: Optional[int] = None) -> Dict[str, Any]:
        """
        Acquire frames from both sensors (dual-sensor mode) with automatic lifecycle.
        
        Lifecycle: start_dual_acquisition() -> get_frames_dual() -> stop_dual_acquisition()

        Args:
            timeout_ms (int, optional): Frame timeout in milliseconds per sensor.

        Returns:
            Dict with keys "primary" and "secondary", each containing frame data.

        Raises:
            CameraError: If not in dual-sensor mode or acquisition fails.

        Example:
            >>> camera.setup(dual_configuration=True, device_selectors=[0, 1])
            >>> frames = camera.acquire_frames_dual()
            >>> primary = frames['primary']
            >>> secondary = frames['secondary']
        """
        logger.info("Acquiring dual frames...")
        try:
            if len(self._acquirers) < 2:
                raise CameraError("Dual-sensor mode not configured (need 2 acquirers).")
            
            self.start_dual_acquisition()
            primary = self.get_frame(acquirer_index=0, timeout_ms=timeout_ms)
            secondary = self.get_frame(acquirer_index=1, timeout_ms=timeout_ms)
            self.stop_dual_acquisition()
            
            logger.info("Dual frames acquired successfully.")
            return {"primary": primary, "secondary": secondary}
        except Exception as e:
            logger.exception("Dual frame acquisition failed.")
            try:
                self.stop_dual_acquisition()
            except Exception:
                pass
            raise CameraError(f"Failed to acquire dual frames: {e}")


    # -------------------------------
    # Vendor specific parameter handling
    # -------------------------------
    def set_exposure_time(self, exposure_us: float, acquirer_index: int = 0) -> None:
        """
        Set exposure time in microseconds [us].
        
        Args:
            exposure_us (float): Exposure time in microseconds [us]
            acquirer_index (int): Index in self._acquirers (default 0)
        """
        self.set_parameter(self.NODES["exposure"], exposure_us, acquirer_index=acquirer_index)

    def get_exposure_time(self, acquirer_index: int = 0) -> float:
        """
        Get current exposure time in microseconds [us].
        
        Args:
            acquirer_index (int): Index in self._acquirers (default 0)
        
        Returns:
            float: Current exposure time in microseconds [us]
        """
        return self.get_parameter(self.NODES["exposure"], acquirer_index=acquirer_index)

    def set_gain(self, gain: float, acquirer_index: int = 0) -> None:
        """
        Set sensor gain value.
        
        Args:
            gain (float): Gain value
            acquirer_index (int): Index in self._acquirers (default 0)
        """
        self.set_parameter(self.NODES["gain"], gain, acquirer_index=acquirer_index)

    def get_gain(self, acquirer_index: int = 0) -> float:
        """
        Get current sensor gain value.
        
        Args:
            acquirer_index (int): Index in self._acquirers (default 0)
        
        Returns:
            float: Current gain value
        """
        return self.get_parameter(self.NODES["gain"], acquirer_index=acquirer_index)

    def set_pixel_format(self, format_name: str, acquirer_index: int = 0) -> None:
        """
        Set pixel format.
        
        Args:
            format_name (str): Name of the pixel format
            acquirer_index (int): Index in self._acquirers (default 0)
        """
        self.set_parameter(self.NODES["pixel_format"], format_name, acquirer_index=acquirer_index)

    def get_pixel_format(self, acquirer_index: int = 0) -> str:
        """
        Get current pixel format.
        
        Args:
            acquirer_index (int): Index in self._acquirers (default 0)
        
        Returns:
            str: Current pixel format name
        """
        return self.get_parameter(self.NODES["pixel_format"], acquirer_index=acquirer_index)

    def set_roi(self, width: int, height: int, offset_x: int = 0, offset_y: int = 0, acquirer_index: int = 0) -> None:
        """
        Set Region of Interest (ROI).
        
        Args:
            width (int): ROI width in pixels
            height (int): ROI height in pixels
            offset_x (int): X offset in pixels
            offset_y (int): Y offset in pixels
            acquirer_index (int): Index in self._acquirers (default 0)
        """
        self.set_parameter(self.NODES["width"], width, acquirer_index=acquirer_index)
        self.set_parameter(self.NODES["height"], height, acquirer_index=acquirer_index)
        self.set_parameter(self.NODES["offset_x"], offset_x, acquirer_index=acquirer_index)
        self.set_parameter(self.NODES["offset_y"], offset_y, acquirer_index=acquirer_index)

    def get_roi(self, acquirer_index: int = 0) -> Dict[str, int]:
        """
        Get current ROI settings.
        
        Args:
            acquirer_index (int): Index in self._acquirers (default 0)
        
        Returns:
            Dict[str, int]: Dictionary with current ROI settings
        """
        return {
            "width": self.get_parameter(self.NODES["width"], acquirer_index=acquirer_index),
            "height": self.get_parameter(self.NODES["height"], acquirer_index=acquirer_index),
            "offset_x": self.get_parameter(self.NODES["offset_x"], acquirer_index=acquirer_index),
            "offset_y": self.get_parameter(self.NODES["offset_y"], acquirer_index=acquirer_index)
        }