#--------------------------------------------------------------------------
# System Configuration
#--------------------------------------------------------------------------
import platform
import sys
import os

import time
start_total = time.perf_counter()

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

print("=" * 70)
print("DUAL-SENSOR ACQUISITION EXAMPLE (AT Sensors 3D)")
print("=" * 70)

# Change to True to save a frame dump from the camera
SAVE_FRAME = True

# Change to True to save a point cloud
SAVE_CLOUD = True

# Change to True to visualize the point cloud with Open3D
VISUALIZATION = True

# Paths configuration
save_suffix = "part1_scan0"
frame_dump_primary = f"./_frame_dumps/example_saves/frame_dump_primary_{save_suffix}.pkl"
frame_dump_secondary = f"./_frame_dumps/example_saves/frame_dump_secondary_{save_suffix}.pkl"
pcd_primary_out = f"./_point_clouds/example_saves/point_cloud_primary_{save_suffix}.xyz"
pcd_secondary_out = f"./_point_clouds/example_saves/point_cloud_secondary_{save_suffix}.xyz"


#--------------------------------------------------------------------------
# Device Discovery and Configuration
#--------------------------------------------------------------------------
print("Supported cameras:", list_supported_cameras())

# Discover available devices
# print("\nDiscovering devices...")
# devices = discover_devices(CTI_PATH)
# if len(devices) < 2:
#     print(f"Error: Need at least 2 devices for dual-sensor mode. Found: {len(devices)}")
#     sys.exit(1)

primary_name = '21815765M'
secondary_name = '21815765S'
# print(f"Found {len(devices)} device(s):")
print(f"  Primary:   {primary_name}")
print(f"  Secondary: {secondary_name}")

# Configuration dictionary
config = {
    "cti_path": CTI_PATH,
    "timeout_ms": 5000,
}

# C6-4090-MCS-420-530-D2-1G calibration dictionary (same for both sensors)
camera_calibration = {
    "scale_z": 0.0625,         # Sensor C-scaler
    "pixel_to_mm_x": 0.0875,   # X scaling calibration
    "pixel_to_mm_z": 0.1955,   # Z scaling calibration
    "stretch_y": 1.0,          # Y distance scaling
}


#--------------------------------------------------------------------------
# AT Sensors 3D Acquisition Example
#--------------------------------------------------------------------------
print("\nCreating camera instance...")
start_connect = time.perf_counter()

camera = create_camera("at_sensors_3d", config_dict=config)

# print("Setting up dual-sensor mode...")
camera.setup(
    dual_configuration=True,
    device_selectors=[
        {'user_defined_name': primary_name},
        {'user_defined_name': secondary_name}
    ]
)
end_connect = time.perf_counter()

print("\nAcquiring dual frames with automatic lifecycle management...")
print("  (start_dual_acquisition -> get_frames_dual -> stop_dual_acquisition)")
try:
    # Use acquire_frames_dual() with automatic lifecycle
    start_acquire = time.perf_counter()
    frames = camera.acquire_frames_dual(timeout_ms=5000)
    end_acquire = time.perf_counter()
    
    primary_frame = frames['primary']
    secondary_frame = frames['secondary']
    
    print(f"\n✓ Dual frames acquired successfully!")
    print(f"\n  Primary sensor:")
    print(f"    Components: {len(primary_frame)}")
    if primary_frame:
        print(f"    Resolution: {primary_frame[0]['width']} x {primary_frame[0]['height']}")
        print(f"    Data format: {primary_frame[0]['data_format']}")
        print(primary_frame[0])
    
    print(f"\n  Secondary sensor:")
    print(f"    Components: {len(secondary_frame)}")
    if secondary_frame:
        print(f"    Resolution: {secondary_frame[0]['width']} x {secondary_frame[0]['height']}")
        print(f"    Data format: {secondary_frame[0]['data_format']}")
        print(secondary_frame[0])
    
except Exception as e:
    print(f"\n✗ Acquisition failed: {e}")
    sys.exit(1)

# Cleanup
print("\nDisconnecting...")
camera.disconnect()
print("✓ Done!")


#--------------------------------------------------------------------------
# AT Sensors 3D Frame Manipulation Example
#--------------------------------------------------------------------------
print("\n" + "=" * 70)
print("POINT CLOUD PROCESSING")
print("=" * 70)

if SAVE_FRAME:
    print("\nSaving frame dumps...")
    save_frame_dump(primary_frame, frame_dump_primary)
    save_frame_dump(secondary_frame, frame_dump_secondary)
    print(f"  Primary:   {frame_dump_primary}")
    print(f"  Secondary: {frame_dump_secondary}")

print("\nBuilding point clouds from frames...")
start_process = time.perf_counter()

# Build point cloud from primary sensor
pcd_primary = build_point_cloud_from_frame(
    primary_frame,
    flip_yx=False,
    camera_calibration=camera_calibration
)
print(f"  Primary:   {pcd_primary_out} ({pcd_primary.shape[0]} points)")

# Build point cloud from secondary sensor (flip_yx=True for 180° rotation)
pcd_secondary = build_point_cloud_from_frame(
    secondary_frame,
    flip_yx=True,  # Mirror for dual-sensor alignment
    camera_calibration=camera_calibration
)
print(f"  Secondary: {pcd_secondary_out} ({pcd_secondary.shape[0]} points)")

end_process = time.perf_counter()

if SAVE_CLOUD:
    save_point_cloud_data(pcd_primary, pcd_primary_out)
    save_point_cloud_data(pcd_secondary, pcd_secondary_out)

end_total = time.perf_counter()

#--------------------------------------------------------------------------
# Open3D Visualization (optional)
#--------------------------------------------------------------------------
if VISUALIZATION:
    pcd_master_o3d = o3d.geometry.PointCloud()
    pcd_master_o3d.points = o3d.utility.Vector3dVector(pcd_primary)
    visualize_point_cloud([pcd_master_o3d], "AT Sensors Example: Master Point Cloud")

    pcd_slave_o3d = o3d.geometry.PointCloud()
    pcd_slave_o3d.points = o3d.utility.Vector3dVector(pcd_secondary)
    visualize_point_cloud([pcd_slave_o3d], "AT Sensors Example: Slave Point Cloud")
    
#---------------------------------------------------------------------------
# Time Statistics
#---------------------------------------------------------------------------
print("\n" + "=" * 70)
print("TIME STATISTICS")
print("=" * 70)
print(f"Camera connection:      {end_connect - start_connect:.4f} s")
print(f"Frame acquisition:      {end_acquire - start_acquire:.4f} s")
print(f"Point cloud processing: {end_process - start_process:.4f} s")
print("-" * 70)
print(f"Total time:             {end_total - start_total:.4f} s")
