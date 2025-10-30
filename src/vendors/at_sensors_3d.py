"""
Vendor-specific implementation: AT Sensors 3D
---------------------------------------------
Implements camera-specific logic using the Harvesters transport layer.
"""

from typing import Optional, Dict, Any, List

from src.base.camera_base import CameraBase
from src.utils.logging_utils import get_logger

# Logging configuration
logger = get_logger("CameraATSensors3D")


class CameraATSensors3D(CameraBase):
    """
    AT Sensors 3D GenICam interface with Harvesters SDK.

    Inherits from CameraBase and implements vendor-specific methods.
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
        logger.debug(f"{self.__class__.__name__} initialized.")


    # -------------------------------
    # Vendor specific parameter handling
    # -------------------------------
    def set_exposure_time(self, exposure_us: float) -> None:
        """
        Set exposure time in microseconds [us].
        
        Args:
            exposure_us (float): Exposure time in microseconds [us]
        """
        self.set_parameter(self.NODES["exposure"], exposure_us)

    def get_exposure_time(self) -> float:
        """
        Get current exposure time in microseconds [us].
        
        Returns:
            float: Current exposure time in microseconds [us]
        """
        return self.get_parameter(self.NODES["exposure"])

    def set_gain(self, gain: float) -> None:
        """
        Set sensor gain value.
        
        Args:
            gain (float): Gain value
        """
        self.set_parameter(self.NODES["gain"], gain)

    def get_gain(self) -> float:
        """
        Get current sensor gain value.
        
        Returns:
            float: Current gain value
        """
        return self.get_parameter(self.NODES["gain"])

    def set_pixel_format(self, format_name: str) -> None:
        """
        Set pixel format.
        
        Args:
            format_name (str): Name of the pixel format
        """
        self.set_parameter(self.NODES["pixel_format"], format_name)

    def get_pixel_format(self) -> str:
        """
        Get current pixel format.
        
        Returns:
            str: Current pixel format name
        """
        return self.get_parameter(self.NODES["pixel_format"])

    def set_roi(self, width: int, height: int, offset_x: int = 0, offset_y: int = 0) -> None:
        """
        Set Region of Interest (ROI).
        
        Args:
            width (int): ROI width in pixels
            height (int): ROI height in pixels
            offset_x (int): X offset in pixels
            offset_y (int): Y offset in pixels
        """
        self.set_parameter(self.NODES["width"], width)
        self.set_parameter(self.NODES["height"], height)
        self.set_parameter(self.NODES["offset_x"], offset_x)
        self.set_parameter(self.NODES["offset_y"], offset_y)

    def get_roi(self) -> Dict[str, int]:
        """
        Get current ROI settings.
        
        Returns:
            Dict[str, int]: Dictionary with current ROI settings
        """
        return {
            "width": self.get_parameter(self.NODES["width"]),
            "height": self.get_parameter(self.NODES["height"]),
            "offset_x": self.get_parameter(self.NODES["offset_x"]),
            "offset_y": self.get_parameter(self.NODES["offset_y"])
        }