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
# Imports & path configuration
#--------------------------------------------------------------------------
import numpy as np
import pickle
import open3d as o3d

from harvestersSDK_api import create_camera, list_supported_cameras
from src.utils.point_cloud_processing import *

# Change to True to save a frame dump from the camera
SAVE_FRAME = False

# Paths configuration
save_suffix = "scan0"

frame_dump = f"./_frame_dumps/example_saves/frame_dump_{save_suffix}.pkl"
pcd_out = f"./_point_clouds/example_saves/point_cloud_{save_suffix}.xyz"


#--------------------------------------------------------------------------
# Camera configuration
#--------------------------------------------------------------------------
# Configuration dictionary
config = {
    "cti_path": CTI_PATH,
    "device_name": '21815765M',
    # "device_serial" "target_serial_number_here",
    # "device_id" "target_id_here",
}

# C6-4090-MCS-420-530-D2-1G calibration dictionary
camera_calibration = {
    "scale_z": 0.0625,         # Sensor C-scaler
    "pixel_to_mm_x": 0.0875,   # X scaling calibration
    "pixel_to_mm_z": 0.1955,   # Z scaling calibration
    "stretch_y": 0.8,          # Y distance scaling
}


#--------------------------------------------------------------------------
# AT Sensors 3D Acquisition Example
#--------------------------------------------------------------------------
print("Supported cameras:", list_supported_cameras())
camera = create_camera("at_sensors_3d", config_dict=config)

camera.connect()

# Start acquisition and get a frame from camera buffer
camera.start_acquisition()
frame = camera.get_frame(timeout_ms=10000)
camera.stop_acquisition()

# Work with captured frame
print(frame)

camera.disconnect()


#--------------------------------------------------------------------------
# AT Sensors 3D Frame Manipulation Example
#--------------------------------------------------------------------------
# Work with captured frame
print(frame)

if SAVE_FRAME == True:
    save_frame_dump(frame, frame_dump)
    frame = open_frame_dump(frame_dump)

# Build point cloud
pcd = build_point_cloud_from_frame(
    frame,
    flip_yx=False
)
save_point_cloud_data(pcd, pcd_out)


#--------------------------------------------------------------------------
# Open3D Visualization (optional)
#--------------------------------------------------------------------------
pcd_master_o3d = o3d.geometry.PointCloud()
pcd_master_o3d.points = o3d.utility.Vector3dVector(pcd)
visualize_point_cloud([pcd_master_o3d], "AT Sensors Example Point Cloud")
