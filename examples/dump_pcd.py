"""
Capture a single RGB and depth frame and save them to output.pcd in
the libpcl PCD format. View the resulting cloud with:

    pcl_viewer output.pcd

"""
from freenect2 import Device, FrameType
import numpy as np

# Open the default device and capture a color and depth frame.
device = Device()
frames = {}
with device.running():
    for type_, frame in device:
        frames[type_] = frame
        if FrameType.Color in frames and FrameType.Depth in frames:
            break

# Use the factory calibration to undistort the depth frame and register the RGB
# frame onto it.
rgb, depth = frames[FrameType.Color], frames[FrameType.Depth]
undistorted, registered = device.registration.apply(rgb, depth)

# Combine the depth and RGB data together into a single point cloud.
with open('output.pcd', 'w') as fobj:
    device.registration.write_pcd(fobj, undistorted, registered)
