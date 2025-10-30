from harvestersSDK_api import create_camera, list_supported_cameras

print("Supported cameras:", list_supported_cameras())

# Option 1: Config via YAML file
# camera = create_camera("at_sensors_3d")

# Option 2: Config via dictionary
config = {
    #"cti_path": "C:/Program Files/Balluff/ImpactAcquire/bin/x64/mvGenTLProducer.cti",
    # "cti_path": "/opt/MVS/lib/aarch64/MvProducerGEV.cti",
    "cti_path": "/opt/cvb-14.01.008/drivers/genicam/libGevTL.cti",
    "device_name": 'C6-21815221'
    # "device_serial": "DA6865197"
}
camera = create_camera("at_sensors_3d", config_dict=config)

camera.connect()

exposure_time = camera.get_exposure_time()
print(f"Exposure time: {exposure_time}")

camera.set_exposure_time(2000)
exposure_time = camera.get_exposure_time()
print(f"Exposure time: {exposure_time}")

camera.set_exposure_time(3500)
exposure_time = camera.get_exposure_time()
print(f"Exposure time: {exposure_time}")

camera.start_acquisition()
frame = camera.get_frame(timeout_ms=10000)
print(frame)
camera.stop_acquisition()

camera.disconnect()
