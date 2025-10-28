"""
error_handling.py
-----------------
Centralized error and exception classes for the Harvesters-based Camera SDK.
"""

class CameraError(Exception):
    """Generic error for camera-related operations."""
    pass

class ConnectionError(CameraError):
    """Exception raised for connection issues."""
    pass

class AcquisitionError(CameraError):
    """Exception raised for acquisition issues."""
    pass

class ParameterError(CameraError):
    """Exception raised for parameter handling issues."""
    pass