#--------------------------------------------------------------------------
# Imports and configuration
#--------------------------------------------------------------------------
from harvestersSDK_api import create_camera, list_supported_cameras

print("Supported cameras:", list_supported_cameras())
device_name = '21815765'


#--------------------------------------------------------------------------
# Basic Acquisition Example
#--------------------------------------------------------------------------
print("=" * 70)
print("BASIC ACQUISITION EXAMPLE")
print("=" * 70)

camera = create_camera(device_name_base=device_name, config_path="./src/configs/config.json")
camera.connect()

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
