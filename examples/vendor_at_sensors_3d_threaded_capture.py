#--------------------------------------------------------------------------
# Imports & path configuration
#--------------------------------------------------------------------------
import platform
import sys
import os
import threading, queue

import numpy as np
import pickle
import open3d as o3d

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from harvestersSDK_api import create_camera, list_supported_cameras
from src.utils.point_cloud_processing import *

# Example configuration flags
SAVE_FRAMES = False
SAVE_CLOUDS = False
O3D_VISUALIZATION = True

print("Supported cameras:", list_supported_cameras())
device_name = '21815765'

# C6-4090-MCS-420-530-D2-1G calibration dictionary (same for both sensors)
CAMERA_CALIBRATION = {
    "scale_z": 0.0625,         # Sensor C-scaler
    "pixel_to_mm_x": 0.0875,   # X scaling calibration
    "pixel_to_mm_z": 0.1955,   # Z scaling calibration
    "stretch_y": 1.0,          # Y distance scaling
}

# Paths configuration
camera_config_path = "./src/configs/config.json"
# camera_config_path = "./CaptureModule_3D/harvestersSDK-API/src/configs/config.json"

capture_suffix = "example_scan"
capture_count = 0
save_paths = {
    "frame_dump_primary": f"./_saves/frame_dump_primary_{capture_suffix}{capture_count}.pkl",
    "frame_dump_secondary": f"./_saves/frame_dump_secondary_{capture_suffix}{capture_count}.pkl",
    "pcd_primary_out": f"./_saves/pcd_primary_out_{capture_suffix}{capture_count}.pkl",
    "pcd_secondary_out": f"./_saves/pcd_secondary_out_{capture_suffix}{capture_count}.pkl",
    "pcd_combined_out": f"./_saves/pcd_combined_out_{capture_suffix}{capture_count}.pkl",
}


#--------------------------------------------------------------------------
# Timer configuration
#--------------------------------------------------------------------------
import time

timers = {
    "start_total": 0.0,
    "elapsed_total": 0.0,
    "start_connect": 0.0,
    "elapsed_connect": 0.0,
    "start_acquire": 0.0,
    "elapsed_acquire": 0.0,
    "start_processing": 0.0,
    "elapsed_processing": 0.0,
}
start_total = time.perf_counter()


#--------------------------------------------------------------------------
# AT Sensors 3D Acquisition Example (dual-head configuration)
#--------------------------------------------------------------------------
def connect():
    print("\n" + "=" * 70)
    print("DUAL-HEAD ACQUISITION EXAMPLE (AT Sensors 3D Camera)")
    print("=" * 70)

    timers["start_connect"] = time.perf_counter()
    camera = create_camera(device_name_base=device_name, config_path=camera_config_path)
    camera.connect()
    timers["elapsed_total"] = time.perf_counter() - timers["start_connect"]    
    return camera


def capture(camera):
    try:
        timers["start_acquire"] = time.perf_counter()
        frames = camera.capture_frames(timeout_ms=5000)
        timers["elapsed_acquire"] = time.perf_counter() - timers["start_acquire"]
    except Exception as e:
        print(f"\n✗ Acquisition failed: {e}")
        sys.exit(1)
    return frames


#--------------------------------------------------------------------------
# Save frames & display results
#--------------------------------------------------------------------------
def show_acquisition_results(frames, capture_suffix="example", capture_count=0):
    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)
    
    # Save separate frames for later processing
    primary_frame = frames['primary_frame']
    secondary_frame = frames['secondary_frame']

    # Display results for primary sensor (master)
    print(f"\nPrimary frame components: {len(primary_frame)}")
    if primary_frame:
        print(f"    Resolution:  {primary_frame[0]['width']} x {primary_frame[0]['height']}")
        print(f"    Data format: {primary_frame[0]['data_format']}")
        print(f"    Frame data:  {primary_frame[0]}")

    # Display results for secondary sensor (slave)
    print(f"\nSecondary frame components: {len(secondary_frame)}")
    if secondary_frame:
        print(f"    Resolution:  {secondary_frame[0]['width']} x {secondary_frame[0]['height']}")
        print(f"    Data format: {secondary_frame[0]['data_format']}")
        print(f"    Frame data:  {secondary_frame[0]}")
    
    # Save frames
    if SAVE_FRAMES:
        print("\nSaving frame dumps...")
        save_paths["frame_dump_primary"] = f"./_saves/frame_dump_primary_{capture_suffix}{capture_count}.pkl"
        save_paths["frame_dump_secondary"] = f"./_saves/frame_dump_secondary_{capture_suffix}{capture_count}.pkl"
        save_frame_dump(primary_frame, save_paths["frame_dump_primary"])
        save_frame_dump(secondary_frame, save_paths["frame_dump_secondary"])
        print(f"    Primary frame:   {save_paths['frame_dump_primary']}")
        print(f"    Secondary frame: {save_paths['frame_dump_secondary']}")


#--------------------------------------------------------------------------
# Frame manipulation example
#--------------------------------------------------------------------------
def process_point_clouds(frames, capture_suffix="example", capture_count=0):
    print("\n" + "=" * 70)
    print("POINT CLOUD PROCESSING")
    print("=" * 70)

    # Save separate frames for later processing
    primary_frame = frames['primary_frame']
    secondary_frame = frames['secondary_frame']

    timers["start_processing"] = time.perf_counter()
    
    # Build point cloud from primary sensor
    pcd_primary = build_point_cloud_from_frame(
        primary_frame,
        flip_yx=False,
        camera_calibration=CAMERA_CALIBRATION
    )
    print(f"\nPrimary point cloud: {pcd_primary.shape[0]} points")

    print()
    # Build point cloud from secondary sensor (flip_yx=True for 180° rotation)
    pcd_secondary = build_point_cloud_from_frame(
        secondary_frame,
        flip_yx=True,  # Mirror for dual-sensor alignment
        camera_calibration=CAMERA_CALIBRATION
    )
    print(f"\nSecondary point cloud: {pcd_secondary.shape[0]} points")
    
    # Combine point clouds
    pcd_combined = np.vstack([pcd_primary, pcd_secondary])
    print(f"\nCombined point cloud: {pcd_combined.shape[0]} points")
    
    timers["elapsed_processing"] = time.perf_counter() - timers["start_processing"]

    # Save point clouds
    if SAVE_CLOUDS:
        print("\nSaving point clouds...")
        save_paths["pcd_primary_out"] = f"./_saves/pcd_primary_out_{capture_suffix}{capture_count}.pkl"
        save_paths["pcd_secondary_out"] = f"./_saves/pcd_secondary_out_{capture_suffix}{capture_count}.pkl"
        save_paths["pcd_combined_out"] = f"./_saves/pcd_combined_out_{capture_suffix}{capture_count}.pkl"
        save_point_cloud_data(pcd_primary, save_paths["pcd_primary_out"])
        save_point_cloud_data(pcd_secondary, save_paths["pcd_secondary_out"])
        save_point_cloud_data(pcd_combined, save_paths["pcd_combined_out"])
        print(f"    Primary point cloud:   {save_paths['pcd_primary_out']}")
        print(f"    Secondary point cloud: {save_paths['pcd_secondary_out']}")
        print(f"    Combined point cloud:  {save_paths['pcd_combined_out']}")
    
    # Visualize
    if O3D_VISUALIZATION:
        print("\n" + "=" * 70)
        print("POINT CLOUD VISUALIZATION")
        print("=" * 70)

        pcd_master_o3d = o3d.geometry.PointCloud()
        pcd_master_o3d.points = o3d.utility.Vector3dVector(pcd_primary)
        visualize_point_cloud([pcd_master_o3d], "AT Sensors Example: Master Point Cloud")

        pcd_slave_o3d = o3d.geometry.PointCloud()
        pcd_slave_o3d.points = o3d.utility.Vector3dVector(pcd_secondary)
        visualize_point_cloud([pcd_slave_o3d], "AT Sensors Example: Slave Point Cloud")

        pcd_combined_o3d = o3d.geometry.PointCloud()
        pcd_combined_o3d.points = o3d.utility.Vector3dVector(pcd_combined)
        visualize_point_cloud([pcd_combined_o3d], "AT Sensors Example: Combined Point Cloud")


def show_time_statistics():
    print("\n" + "=" * 70)
    print("TIME STATISTICS")
    print("=" * 70)

    print(f"Camera connection:      {timers['elapsed_connect']:.4f} s")
    print(f"Frame acquisition:      {timers['elapsed_acquire']:.4f} s")
    print(f"Point cloud processing: {timers['elapsed_processing']:.4f} s")
    print("-" * 70)
    print(f"Total time:             {timers['elapsed_total']:.4f} s")


#--------------------------------------------------------------------------
# Main inspection function
#--------------------------------------------------------------------------
def inspect(camera, capture_count):
    frames = capture(camera)
    if frames:
        show_acquisition_results(frames, capture_suffix, capture_count)
        process_point_clouds(frames, capture_suffix, capture_count)

    # continue use case inspection here...


#--------------------------------------------------------------------------
# Main
#--------------------------------------------------------------------------
if __name__ == "__main__":
    camera = connect()

    try:
        capture_count = 0
        print("\nPress 'c' to capture frame, 'q' to quit.")
        while True:
            key = input().lower()
            
            if key == 'c':
                print("\nAcquiring dual frames...")

                # Create and start capture thread
                capture_thread = threading.Thread(
                    target=inspect,
                    args=(camera, capture_count,),
                    name=f"CaptureThread {capture_count}"
                )
                capture_thread.start()
                capture_thread.join()

                capture_count += 1
                print("\n✓ Done!")
                print("\nPress 'c' to capture frame, 'q' to quit.")
                
            elif key == 'q':
                print("\nDisconnecting...")
                break
    except KeyboardInterrupt:
        print("\n\nInterrupted")
    finally:
        camera.disconnect()
        show_time_statistics()
