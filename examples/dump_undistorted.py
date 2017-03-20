from time import sleep
from freenect2 import Device, FrameType
import numpy as np

def main():
    device = Device()
    frames = {}
    def frame_listener(type_, frame):
        frames[type_] = frame

    device.color_frame_listener = frame_listener
    device.ir_and_depth_frame_listener = frame_listener
    with device.running():
        while FrameType.Color not in frames or FrameType.Depth not in frames:
            sleep(0.1)

    rgb, depth = frames[FrameType.Color], frames[FrameType.Depth]
    undistorted, registered = device.registration.apply(rgb, depth)
    points_array = device.registration.get_points_xyz_array(undistorted)

    undistorted.to_image().save('undistorted_depth.tiff')
    registered.to_image().save('registered_rgb.png')
    np.savez('points.npz', points=points_array)

if __name__ == '__main__':
    main()
