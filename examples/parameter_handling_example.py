#--------------------------------------------------------------------------
# Imports and configuration
#--------------------------------------------------------------------------
from harvestersSDK_api import create_camera, list_supported_cameras

print("Supported cameras:", list_supported_cameras())
device_name = '21815765'


#--------------------------------------------------------------------------
# Example 1: Apply GenICam parameters from JSON config (via API)
#--------------------------------------------------------------------------
print("\n" + "="*70)
print("EXAMPLE 1: Apply GenICam parameters from JSON config")
print("="*70)

camera = create_camera(device_name_base=device_name, config_path="./src/configs/config.json")
camera.connect()

# Apply all parameters from JSON to respective sensors
print(f"\nApplying GenICam parameters from config.json...")
camera.apply_genicam_parameters(camera.device_genicam_dict)

# Verify applied parameters for sensor_1
print(f"\nVerifying sensor_1 parameters:")
sensor1_params = camera.device_genicam_dict.get("sensor_1", {})
for param_name in sensor1_params.keys():
    try:
        value = camera.get_parameter(param_name, acquirer_index=0)
        print(f"    {param_name}: {value}")
    except Exception as e:
        print(f"    {param_name}: Error reading - {e}")

# Verify applied parameters for sensor_2 (if dual-sensor)
if len(camera._acquirers) >= 2:
    print(f"\nVerifying sensor_2 parameters:")
    sensor2_params = camera.device_genicam_dict.get("sensor_2", {})
    for param_name in sensor2_params.keys():
        try:
            value = camera.get_parameter(param_name, acquirer_index=1)
            print(f"  {param_name}: {value}")
        except Exception as e:
            print(f"  {param_name}: Error reading - {e}")

camera.disconnect()


#--------------------------------------------------------------------------
# Example 2: Vendor-specific parameter handling methods
#--------------------------------------------------------------------------
print("\n" + "="*70)
print("EXAMPLE 2: Vendor-specific parameter handling methods")
print("="*70)

camera = create_camera(device_name_base=device_name, config_path="./src/configs/config.json")
camera.connect()

# Get original values
print(f"\nOriginal values (sensor_1 - acquirer 0):")
original_exposure_time = camera.get_exposure_time(acquirer_index=0)
print(f"    Exposure time: {original_exposure_time}")

original_gain = camera.get_gain(acquirer_index=0)
print(f"    Gain: {original_gain}")

# Modify parameters using vendor-specific methods
print(f"\nModifying parameters...")
camera.set_exposure_time(2000, acquirer_index=0)
camera.set_gain(2.5, acquirer_index=0)

# Verify modifications
print(f"\nVerifying modified values:")
new_exposure_time = camera.get_exposure_time(acquirer_index=0)
print(f"    Exposure time: {new_exposure_time}")

new_gain = camera.get_gain(acquirer_index=0)
print(f"    Gain: {new_gain}")

# Restore original values
print(f"\nRestoring original values...")
camera.set_exposure_time(original_exposure_time, acquirer_index=0)
camera.set_gain(original_gain, acquirer_index=0)

# Verify restoration
print(f"\nVerifying restored values:")
restored_exposure_time = camera.get_exposure_time(acquirer_index=0)
print(f"    Exposure time: {restored_exposure_time}")

restored_gain = camera.get_gain(acquirer_index=0)
print(f"    Gain: {restored_gain}")

camera.disconnect()
