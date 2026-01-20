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


    @classmethod
    def from_config(cls, api_config_dict: dict, device_data_dict: dict, device_genicam_dict: dict) -> "CameraATSensors3D":
        return cls(api_config_dict, device_data_dict, device_genicam_dict)

    
    def __init__(self, api_config_dict: dict, device_data_dict: dict, device_genicam_dict: dict):
        """
        Initialize AT Sensors 3D camera.
        
        Args:
            config (dict): Configuration dictionary passed to CameraBase
        """
        super().__init__(
            api_config_dict=api_config_dict,
            device_data_dict=device_data_dict,
            device_genicam_dict=device_genicam_dict
            )
        
        self.vendor_str = device_data_dict.get("vendor", "").strip()
        self.scan_type = device_data_dict.get("scanType")
        self.topology  = (device_data_dict.get("topology") or "single_sensor").lower()
        self.id_sensor1   = device_data_dict.get("sensor_1", {}).get("user_defined_name")
        self.id_sensor2 = device_data_dict.get("sensor_2", {}).get("user_defined_name")

        logger.debug(f"CameraATSensors3D initialized.")

    
    # -------------------------------
    # Search key helper
    # -------------------------------
    def _get_search_key(self, vendor_str, sensor_id) -> Dict[str, Any]:
        if not sensor_id:
            raise CameraError("user_defined_name not defined!")
        return {"vendor": vendor_str, "user_defined_name": sensor_id}


    # -------------------------------
    # Camera setup
    # -------------------------------    
    def connect(self) -> None:
        # Clear any previous acquirers
        if self._acquirers:
            super().disconnect()

        if self.topology == "single_sensor":
            super().connect(device_selector=self._get_search_key(self.vendor_str, self.id_sensor1))
            logger.info("Configured single-sensor mode (acquirer 0).")
            return
        if self.topology == "dual_sensor":
            super().connect(device_selector=self._get_search_key(self.vendor_str, self.id_sensor2)) # index 0 (slave)
            super().connect(device_selector=self._get_search_key(self.vendor_str, self.id_sensor1)) # index 1 (master)
            logger.info("Configured dual-sensor mode (acquirers 0 and 1).")
            return
        raise CameraError(f"Invalid topology '{self.topology}'!")


    # -------------------------------
    # Dual-sensor acquisition overrides
    # -------------------------------    
    def start_acquisition(self, acquirer_index: int = 0) -> None:
        if self.topology == "single_sensor":
            return super().start_acquisition(acquirer_index)

        # Dual sensor acquisition
        if len(self._acquirers) < 2:
            raise CameraError("Image acquirers for dual-sensor not configured!")
        super().start_acquisition(acquirer_index=0)
        super().start_acquisition(acquirer_index=1)
        logger.info("Started dual-sensor acquisition.")

    
    def stop_acquisition(self, acquirer_index: int = 0) -> None:
        if self.topology == "single_sensor":
            return super().stop_acquisition(acquirer_index)

        # Dual sensor acquisition
        if len(self._acquirers) < 2:
            raise CameraError("Image acquirers for dual-sensor not configured!")
        super().stop_acquisition(acquirer_index=0)
        super().stop_acquisition(acquirer_index=1)
        logger.info("Stopped dual-sensor acquisition.")
    

    def get_frames(self, timeout_ms: Optional[int] = None) -> Dict[str, Any]:
        """
        Fetch frames from both sensors.

        Args:
            timeout_ms (int, optional): Timeout in milliseconds.
        
        Returns:
            {'primary': frame0, 'secondary': frame1}
        """
        if self.topology == "dual_sensor":
            if len(self._acquirers) < 2:
                raise CameraError("Image acquirers for dual-sensor not configured!")
            primary_frame   = super().get_frame(acquirer_index=0, timeout_ms=timeout_ms)
            secondary_frame = super().get_frame(acquirer_index=1, timeout_ms=timeout_ms)
            return {"primary_frame": primary_frame, "secondary_frame": secondary_frame}

        # Fallback for wrong topology usage
        primary_frame = super().get_frame(acquirer_index=0, timeout_ms=timeout_ms)
        return {"primary_frame": primary_frame}


    # -------------------------------
    # Acquisition lifecycle
    # -------------------------------
    def capture_frames(self, timeout_ms: Optional[int] = None) -> Dict[str, Any]:
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
                raise CameraError("Image acquirers for dual-sensor not configured!")
            
            self.start_acquisition()
            frames = self.get_frames(timeout_ms=timeout_ms)
            self.stop_acquisition()
            
            logger.info("Dual frames acquired successfully!")
            return frames.copy()
        
        except Exception as e:
            logger.exception("Dual frame acquisition failed!")
            try:
                self.stop_acquisition()
            except Exception:
                pass
            raise CameraError(f"Failed to acquire dual frames: {e}")


    # -------------------------------
    # Genicam parameter handling
    # -------------------------------
    def apply_genicam_parameters(self, genicam_dict: Dict[str, Any], acquirer_index: int = 0) -> None:
        if not self.connected:
            raise CameraError("Camera must be connected before applying parameters!")
        
        if not genicam_dict:
            logger.debug("No GenICam parameters to apply.")
            return
        
        # Apply sensor_1 parameters
        if "sensor_1" in genicam_dict:
            sensor1_params = genicam_dict.get("sensor_1", {}) or {}
            if sensor1_params:
                logger.info(f"Applying GenICam parameters to {self.id_sensor1} (acquirer 1): {len(sensor1_params)} parameters")
                try:
                    super().apply_genicam_parameters(sensor1_params, acquirer_index=0)
                except ParameterError as e:
                    logger.exception(f"Failed to configure {self.id_sensor1}.")
                    if self.strict:
                        raise CameraError(f"Failed to configure {self.id_sensor1}: {e}")
        
        # Apply sensor_2 parameters
        elif "sensor_2" in genicam_dict:
            sensor2_params = genicam_dict.get("sensor_2", {}) or {}
            if sensor2_params:
                if len(self._acquirers) < 2:
                    logger.warning(f"{self.id_sensor2} parameters specified but only 1 acquirer available. Skipping...")
                    return
                
                logger.info(f"Applying GenICam parameters to {self.id_sensor2} (acquirer 0): {len(sensor2_params)} parameters")
                try:
                    super().apply_genicam_parameters(sensor2_params, acquirer_index=1)
                except ParameterError as e:
                    logger.exception(f"Failed to configure {self.id_sensor2}.")
                    if self.strict:
                        raise CameraError(f"Failed to configure {self.id_sensor2}: {e}")

        # Fallback
        else:
            logger.info(f"Applying GenICam parameters to acquirer {acquirer_index}...")
            super().apply_genicam_parameters(genicam_dict, acquirer_index=acquirer_index)


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