#--------------------------------------------------------------------------
# Imports and configuration
#--------------------------------------------------------------------------
from harvestersSDK_api import create_camera, list_supported_cameras

print("Supported cameras:", list_supported_cameras())
device_name = '21815765'


#--------------------------------------------------------------------------
# Basic Connection Handling Example
#--------------------------------------------------------------------------
camera = create_camera(device_name_base=device_name, config_path="./src/configs/config.json")
camera.connect()
camera.disconnect()
