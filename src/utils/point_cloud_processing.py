import platform
import sys
import os

import numpy as np
import pickle
import open3d as o3d
from src.utils.logging_utils import get_logger

# Logging configuration
logger = get_logger("PointCloudProcessing")


# =========================
# SAVE & OPEN FRAMES
# =========================
def save_frame_dump(frame, frame_path="frame_dump.pkl"):
    # Save a frame dump with "wb"
    with open(frame_path, "wb") as f:
        pickle.dump(frame, f)
    logger.info(f"Saved frame to: {frame_path}")
    logger.debug(f"Frame data: {frame}")

def open_frame_dump(frame_path):
    # Open a frame dump with "rb"
    with open(frame_path, "rb") as f:
        frame = pickle.load(f)
    logger.info(f"Loaded frame from: {frame_path}")
    logger.debug(f"Frame data: {frame}")
    return frame


# =========================
# SAVE & OPEN POINT CLOUDS
# =========================
def save_point_cloud_data(pcd_xyz, pcd_path="point_cloud.xyz"):
    np.savetxt(pcd_path, pcd_xyz, fmt="%.6f")
    logger.info(f"Saved point cloud to: {pcd_path}")
    logger.debug(f"Point cloud data: {pcd_xyz.shape[0]} points")

def open_point_cloud_data(pcd_path="point_cloud.xyz"):
    pcd_xyz = np.loadtxt(pcd_path)
    logger.info(f"Loaded point cloud from: {pcd_path}")
    logger.debug(f"Point cloud data: {pcd_xyz.shape[0]} points")
    return pcd_xyz


# =========================
# POINT CLOUD MANIPULATION FUCTIONS
# =========================
def get_bbox_center(pcd):
    xmin, ymin, zmin = pcd.min(axis=0)
    xmax, ymax, zmax = pcd.max(axis=0)
    return np.array([(xmin + xmax)/2.0,
                     (ymin + ymax)/2.0,
                     (zmin + zmax)/2.0])
    
def remove_duplicate_points(pcd):
    pcd_unique = np.unique(pcd, axis=0)
    logger.debug(f"Removed {pcd.shape[0] - pcd_unique.shape[0]} exact duplicates.")
    return pcd_unique


# =========================
# BUILD A POINT CLOUD
# =========================
def build_point_cloud_from_frame(frame, flip_yx=False, camera_calibration=None):
    if not camera_calibration:
        camera_calibration = {
            "scale_z": 0.0625,         # Sensor C-scaler
            "pixel_to_mm_x": 0.0875,   # X scaling calibration
            "pixel_to_mm_z": 0.1955,   # Z scaling calibration
            "stretch_y": 0.8,          # Y distance scaling
        }

    range_component = frame[0]
    w = range_component["width"]
    h = range_component["height"]
    data = range_component["data"]
    logger.info(f"Building point cloud from frame (width; height; size): {w}; {h}; {data.size} entries")

    # Depth conversion
    range_image = data.reshape(h, w)

    # Pixel coordinate grid
    xs, ys = np.meshgrid(np.arange(w), np.arange(h))

    # Image center
    cx, cy = (w-1)/2.0, (h-1)/2.0
    
    # Convert to metric
    X_mm = (xs - cx) * camera_calibration.get('pixel_to_mm_x', 0.0875)
    Y_mm = (ys - cy) * camera_calibration.get('stretch_y', 0.8)

    Z_raw = range_image.astype(np.float32) * camera_calibration.get('scale_z', 0.0625)
    Z_mm = Z_raw * camera_calibration.get('pixel_to_mm_z', 0.1955)
    logger.debug(f"Z[mm] (min; max; mean; std):  {Z_mm.min()}; {Z_mm.max()}; {Z_mm.mean()}; {Z_mm.std()}")

    # Valid mask
    mask_valid = Z_mm > 0.0

    # Apply mask
    Xv = X_mm[mask_valid]
    Yv = Y_mm[mask_valid]
    Zv = Z_mm[mask_valid]
    
    # Fix Z direction (convert negative depth to positive)
    Zv = -Zv

    # APPLY 180° ROTATION IF SLAVE SENSOR
    if flip_yx:
        logger.debug("Applying horizontal flip (mirror along Y axis)...")
        Xv = -Xv

    # Stack cloud
    xyz = np.column_stack((Xv, Yv, Zv))
    return xyz


# =========================
# POINT CLOUD VISUALIZATION FUCTIONS
# =========================
def visualize_point_cloud(pcd_list, title="Point Cloud"):
    mesh_axis = o3d.geometry.TriangleMesh.create_coordinate_frame(
        size=20.0,
        origin=[0, 0, 0]
    )
    logger.info(f"Loaded {title} for visualization with {len(pcd_list)} objects.")
    for idx, pcd in enumerate(pcd_list):
        logger.debug(f"{title} object {idx}:  {len(pcd.points)} points")
        
    o3d.visualization.draw_geometries(pcd_list, # type: ignore
                                      window_name=title,
                                      width=1280,
                                      height=720,
                                      left=200,
                                      top=200,
                                      point_show_normal=False)
    