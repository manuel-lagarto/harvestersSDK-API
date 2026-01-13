#--------------------------------------------------------------------------
# System Configuration
#--------------------------------------------------------------------------
import platform
import sys
import os

# Change CTI_PATH as needed for the target GenTL producer
if platform.system() == "Windows":
    CTI_PATH = r"C:/Program Files/Balluff/ImpactAcquire/bin/x64/mvGenTLProducer.cti"
elif platform.system() == "Linux":
    CTI_PATH = r"/opt/cvb-14.01.008/drivers/genicam/libGevTL.cti"
else:
    raise OSError("Operating system not supported!")

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


#--------------------------------------------------------------------------
# Imports and configuration
#--------------------------------------------------------------------------
from harvestersSDK_api import create_camera, list_supported_cameras

print("Supported cameras:", list_supported_cameras())

# device_name = devices[0]['user_defined_name']
device_name = '21815765S'
print(f"Using device: {device_name}")

# Configuration dictionary
config = {
    "cti_path": CTI_PATH,
    "device_name": device_name,
    # "device_serial" "target_serial_number_here",
    # "device_id" "target_id_here",
    "timeout_ms": 5000,
}


#--------------------------------------------------------------------------
# Basic Connection Handling Example
#--------------------------------------------------------------------------
camera = create_camera("21815765", config_path="./src/configs/config.json")

camera.connect()
camera.disconnect()