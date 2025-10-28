from harvestersSDK_api import create_camera, list_supported_cameras

print("Supported cameras:", list_supported_cameras())

# Option 1: Config via YAML file
# camera = create_camera("at_sensors_3d")

# Option 2: Config via dictionary
config = {
    "cti_path": "C:/Program Files/Balluff/ImpactAcquire/bin/x64/mvGenTLProducer.cti",
    "device_name": 'C6-21815221'
}
camera = create_camera("at_sensors_3d", config_dict=config)

camera.connect()
# camera.start_acquisition()
# frame = camera.get_frame()
# camera.stop_acquisition()
camera.disconnect()
