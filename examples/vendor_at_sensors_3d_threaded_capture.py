#--------------------------------------------------------------------------
# System Configuration
#--------------------------------------------------------------------------
import platform
import sys
import os
import time
import threading

# Setup paths
if platform.system() == "Windows":
    CTI_PATH = r"C:/Program Files/Balluff/ImpactAcquire/bin/x64/mvGenTLProducer.cti"
elif platform.system() == "Linux":
    CTI_PATH = r"/opt/cvb-14.01.008/drivers/genicam/libGevTL.cti"
else:
    raise OSError("Operating system not supported!")

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


#--------------------------------------------------------------------------
# Imports & path configuration
#--------------------------------------------------------------------------
import numpy as np
import open3d as o3d

from harvestersSDK_api import create_camera, list_supported_cameras
from src.utils.point_cloud_processing import *

# Example settings
SAVE_FRAME = False
SAVE_CLOUD = False
VISUALIZATION = True


#--------------------------------------------------------------------------
# Device Discovery and Configuration
#--------------------------------------------------------------------------
print("\n" + "=" * 70)
print("DUAL-HEAD ACQUISITION EXAMPLE (AT Sensors 3D Camera)")
print("=" * 70)

# List supported vendors
print("Supported cameras:", list_supported_cameras())

# Define device names
device_name_primary = '21815765M'
device_name_secondary = '21815765S'

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
# Capture Thread
#--------------------------------------------------------------------------
class CaptureThread(threading.Thread):
    def __init__(self, camera):
        super().__init__(daemon=False)
        self.camera = camera
        self.frames = None
        
    def run(self):
        print("\nStarting frame capture...")
        try:
            start = time.perf_counter()
            
            # 3. Use acquire_frames_dual() for automatic lifecycle
            self.frames = self.camera.acquire_frames_dual(timeout_ms=5000)

            elapsed = time.perf_counter() - start
            print(f"✓ Success! ({elapsed:.3f}s)")
        except Exception as e:
            print(f"✗ Error: {e}\n")


#--------------------------------------------------------------------------
# Process frames & visualize point clouds
#--------------------------------------------------------------------------
def process_frames(frames, scan_suffix="scan0"):
    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)

    # Configure paths
    frame_dump_primary = f"./_frame_dumps/frame_dump_primary_{scan_suffix}.pkl"
    frame_dump_secondary = f"./_frame_dumps/frame_dump_secondary_{scan_suffix}.pkl"
    
    # Save separate frames for later processing
    primary_frame = frames['primary']
    secondary_frame = frames['secondary']

    # Display results for primary sensor (master)
    print(f"\n   Primary frame:")
    print(f"      Components:  {len(primary_frame)}")
    if primary_frame:
        print(f"      Resolution:  {primary_frame[0]['width']} x {primary_frame[0]['height']}")
        print(f"      Data format: {primary_frame[0]['data_format']}")
        print(f"      Frame data:  {primary_frame[0]}")

    # Display results for secondary sensor (slave)
    print(f"\n   Secondary frame:")
    print(f"      Components:  {len(secondary_frame)}")
    if secondary_frame:
        print(f"      Resolution:  {secondary_frame[0]['width']} x {secondary_frame[0]['height']}")
        print(f"      Data format: {secondary_frame[0]['data_format']}")
        print(f"      Frame data:  {secondary_frame[0]}")
    
    # Save frames
    if SAVE_FRAME:
        print("\nSaving frame dumps...")
        save_frame_dump(primary_frame, frame_dump_primary)
        save_frame_dump(secondary_frame, frame_dump_secondary)
        print(f"   Primary frame:   {frame_dump_primary}")
        print(f"   Secondary frame: {frame_dump_secondary}")


def process_point_clouds(frames, scan_suffix="scan0"):    
    print("\n" + "=" * 70)
    print("POINT CLOUD PROCESSING")
    print("=" * 70)

    # Configure paths
    pcd_primary_out = f"./_point_clouds/point_cloud_primary_{scan_suffix}.xyz"
    pcd_secondary_out = f"./_point_clouds/point_cloud_secondary_{scan_suffix}.xyz"
    pcd_combined_out = f"./_point_clouds/point_cloud_combined_{scan_suffix}.xyz"

    # Save separate frames for later processing
    primary_frame = frames['primary']
    secondary_frame = frames['secondary']

    start_process = time.perf_counter()
    
    # Build point cloud from primary sensor
    pcd_primary = build_point_cloud_from_frame(
        primary_frame,
        flip_yx=False,
        camera_calibration=camera_calibration
    )
    print(f"  Primary point cloud: {pcd_primary_out} ({pcd_primary.shape[0]} points)")

    print()
    # Build point cloud from secondary sensor (flip_yx=True for 180° rotation)
    pcd_secondary = build_point_cloud_from_frame(
        secondary_frame,
        flip_yx=True,  # Mirror for dual-sensor alignment
        camera_calibration=camera_calibration
    )
    print(f"  Secondary point cloud: {pcd_secondary_out} ({pcd_secondary.shape[0]} points)")
    
    # Combine point clouds
    pcd_combined = np.vstack([pcd_primary, pcd_secondary])
    
    elapsed_process = time.perf_counter() - start_process

    # Save point clouds
    if SAVE_CLOUD:
        print("\nSaving point clouds...")
        save_point_cloud_data(pcd_primary, pcd_primary_out)
        save_point_cloud_data(pcd_secondary, pcd_secondary_out)
        save_point_cloud_data(pcd_combined, pcd_combined_out)
        print(f"  Primary point cloud:   {pcd_primary_out}")
        print(f"  Secondary point cloud: {pcd_secondary_out}")
        print(f"  Combined point cloud:  {pcd_combined_out}")
    
    # Visualize
    if VISUALIZATION:
        print("\n" + "=" * 70)
        print("POINT CLOUD VISUALIZATION")
        print("=" * 70)

        # pcd_master_o3d = o3d.geometry.PointCloud()
        # pcd_master_o3d.points = o3d.utility.Vector3dVector(pcd_primary)
        # visualize_point_cloud([pcd_master_o3d], "AT Sensors Example: Master Point Cloud")

        # pcd_slave_o3d = o3d.geometry.PointCloud()
        # pcd_slave_o3d.points = o3d.utility.Vector3dVector(pcd_secondary)
        # visualize_point_cloud([pcd_slave_o3d], "AT Sensors Example: Slave Point Cloud")

        pcd_combined_o3d = o3d.geometry.PointCloud()
        pcd_combined_o3d.points = o3d.utility.Vector3dVector(pcd_combined)
        visualize_point_cloud([pcd_combined_o3d], "AT Sensors Example: Combined Point Cloud")


    print("\n" + "=" * 70)
    print("TIME STATISTICS")
    print("=" * 70)

    print(f"Camera connection:      {elapsed_connect:.4f} s")
    print(f"Frame acquisition:      {elapsed_acquire:.4f} s")
    print(f"Point cloud processing: {elapsed_process:.4f} s")
    print("-" * 70)
    print(f"Total time:             {elapsed_connect+elapsed_acquire+elapsed_process:.4f} s")


#--------------------------------------------------------------------------
# Main
#--------------------------------------------------------------------------
if __name__ == "__main__":
    print("\nCreating camera instance...")
    start_connect = time.perf_counter()

    # 1. Create a camera instance
    camera = create_camera("at_sensors_3d", config_dict=config)

    # 2. Setup a dual-head configuration
    camera.setup(
        dual_configuration=True,
        device_selectors=[
            {'user_defined_name': device_name_primary},
            {'user_defined_name': device_name_secondary}
        ]
    )
    elapsed_connect = time.perf_counter() - start_connect
    
    print("\nPress 'c' to capture frame, 'q' to quit...")
    try:
        capture_count = 0
        while True:
            key = input().lower()
            
            if key == 'c':
                start_acquire = time.perf_counter()
                print("\nAcquiring dual frames...")
                # Create and start capture thread
                capture_thread = CaptureThread(camera)
                capture_thread.start()
                capture_thread.join() # Wait for thread to finish
                elapsed_acquire = time.perf_counter() - start_acquire

                # Process frames & build point clouds if capture was successful
                if capture_thread.frames:
                    capture_count += 1
                    process_frames(capture_thread.frames, scan_suffix=f"scan{capture_count}")
                    process_point_clouds(capture_thread.frames, scan_suffix=f"scan{capture_count}")
                    print("\nPress 'c' to capture frame, 'q' to quit...")
                
            elif key == 'q':
                print("\nDisconnecting...")
                break    
    except KeyboardInterrupt:
        print("\n\nInterrupted")
    
    camera.disconnect()
    print("✓ Done!")
