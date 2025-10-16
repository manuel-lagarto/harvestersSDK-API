"""
Config Loader Utility
---------------------
Loads and merges configuration files (base + camera-specific).
"""

import yaml
import logging
from pathlib import Path
from src.utils.error_handling import CameraError

logger = logging.getLogger("harvestersSDK.ConfigLoader")


class ConfigLoader:
    """
    Loads configuration from base and camera-specific YAML files.
    """

    def __init__(self, base_config_path: str, camera_config_path: str):
        self.base_config_path = Path(base_config_path)
        self.camera_config_path = Path(camera_config_path)
        self.config = {}

    def load(self):
        """Load and merge base + camera-specific configs."""
        self.config = {}
        self._load_yaml(self.base_config_path)
        self._load_yaml(self.camera_config_path)
        logger.info(f"Configurations loaded: {self.config.keys()}")
        return self.config

    def _load_yaml(self, path: Path):
        if not path.exists():
            raise CameraError(f"Configuration file not found: {path}")
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
                self.config.update(data)
        except Exception as e:
            logger.exception(f"Failed to load YAML file: {path}")
            raise CameraError(f"Failed to load configuration file {path}: {e}")
