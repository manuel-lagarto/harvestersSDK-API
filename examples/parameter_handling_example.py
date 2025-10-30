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

# Configuration dictionary
config = {
    "cti_path": CTI_PATH,
    "device_name": 'C6-21815221',
    # "device_serial" "target_serial_number_here",
    # "device_id" "target_id_here",
}


#--------------------------------------------------------------------------
# Parameter Handling Example
#--------------------------------------------------------------------------
camera = create_camera("at_sensors_3d", config_dict=config)

camera.connect()

# Get exposure time node value
original_exposure_time = camera.get_exposure_time()
print(f"Exposure time: {original_exposure_time}")

# Set and verify new exposure time node value
camera.set_exposure_time(2000)
exposure_time = camera.get_exposure_time()
print(f"Exposure time: {exposure_time}")

# Set original exposure time node value
camera.set_exposure_time(original_exposure_time)
exposure_time = camera.get_exposure_time()
print(f"Exposure time: {exposure_time}")

camera.disconnect()