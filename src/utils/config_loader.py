"""
Config Loader Utility
---------------------
Loads and merges configuration files (base + camera-specific).
"""
from __future__ import annotations
import sys
import json
from pathlib import Path
from typing import Dict, Any, Tuple, List, Optional

from src.utils.error_handling import CameraError
from src.utils.logging_utils import get_logger

# Logging configuration
logger = get_logger("ConfigLoader")


class ConfigLoader:
    """
    Loads configuration from base and camera-specific JSON files.
    """
    def __init__(self, config_path: str):        
        self.config_path = Path(config_path)
        self.config: Dict[str, Any] = {}

    
    def load(self) -> Dict[str, Any]:
        if not self.config_path.exists() or not self.config_path.is_file():
            raise CameraError(f"Configuration file not found: {self.config_path}")
        with open(self.config_path, "r", encoding="utf-8") as f:
            self.config = json.load(f)
        logger.info(f"Config JSON carregado: {self.config_path}")
        return self.config


    # -------------------------------
    # Helpers
    # -------------------------------    
    def _os_cti_path(self) -> Optional[str]:
        tr = self.config.get("transport", {}) or {}
        if sys.platform.startswith("win"):
            return tr.get("windows_cti_path")
        return tr.get("linux_cti_path")
    

    def _get_camera_entry(self, device_name_base: str) -> Dict[str, Any]:
        cams = self.config.get("cameras", {}) or {}
        if device_name_base not in cams:
            raise CameraError(f"Camera '{device_name_base}' not found in configuration file.")
        return cams[device_name_base] or {}
    

    # ---------------------------
    # GETTERS solicitados
    # ---------------------------
    def get_api_config(self, device_name_base: str) -> Dict[str, Any]:
        cti_path = self._os_cti_path()
        if not cti_path:
            raise CameraError("cti_path não encontrado em transport.{linux_cti_path|windows_cti_path}.")

        api_config_dict: Dict[str, Any] = {
            "cti_path": cti_path,
            "library": self.config.get("library", {}) or {},
        }
        return api_config_dict


    def get_device_data(self, device_name_base: str) -> Dict[str, Any]:
        camera_entry = self._get_camera_entry(device_name_base)
        vendor   = camera_entry.get("vendor")
        scanType = camera_entry.get("scanType")
        topology = camera_entry.get("topology", "single_sensor").lower()
        sensor_1 = (camera_entry.get("sensor_1") or {})
        sensor_2 = (camera_entry.get("sensor_2") or {})

        device_data_gui: Dict[str, Any] = {
            "device_id": device_name_base,
            "vendor": vendor,
            "scanType": scanType,
            "topology": topology,
            "sensor_1": sensor_1,
            "sensor_2": sensor_2,
        }
        return device_data_gui


    def get_device_genicam(self, device_name_base: str) -> Dict[str, Any]:
        camera_entry = self._get_camera_entry(device_name_base)

        sensor_1 = (camera_entry.get("sensor_1") or {})
        sensor_2 = (camera_entry.get("sensor_2") or {})

        sensor1_genicam_nodes = sensor_1.get("genicam_nodes", {}) or {}
        sensor2_genicam_nodes = sensor_2.get("genicam_nodes", {}) or {}

        device_genicam_dict: Dict[str, Any] = {"sensor_1": sensor1_genicam_nodes}
        if camera_entry.get("topology", "single_sensor").lower() == "dual_sensor":
            device_genicam_dict["sensor_2"] = sensor2_genicam_nodes
        return device_genicam_dict
