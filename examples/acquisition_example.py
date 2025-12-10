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
from harvestersSDK_api import create_camera, discover_devices, list_supported_cameras

print("=" * 70)
print("SINGLE-SENSOR ACQUISITION EXAMPLE")
print("=" * 70)

print("\nSupported cameras:", list_supported_cameras())

# Discover available devices
# print("\nDiscovering devices...")
# devices = discover_devices(CTI_PATH)
# if not devices:
#     print("No devices found!")
#     sys.exit(1)

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
# Single-Sensor Acquisition with Lifecycle
#--------------------------------------------------------------------------
print("\nCreating camera instance...")
camera = create_camera("at_sensors_3d", config_dict=config)

print("\nSetting up single-sensor mode...")
camera.setup(dual_configuration=False)

print("\nAcquiring frame with automatic lifecycle...")
try:
    frame = camera.acquire_frame(acquirer_index=0, timeout_ms=5000)
    print(f"\n✓ Frame acquired successfully!")
    print(frame)
    print(f"  Components: {len(frame)}")
    if frame:
        print(f"  Component 0 - Width: {frame[0]['width']}, Height: {frame[0]['height']}")
        print(f"  Data type: {frame[0]['data_format']}")
except Exception as e:
    print(f"\n✗ Acquisition failed: {e}")

print("\nDisconnecting...")
camera.disconnect()
print("Done!")