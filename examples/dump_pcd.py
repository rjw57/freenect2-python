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
        while len(frames) < 3:
            sleep(0.1)

    rgb, depth = frames[FrameType.Color], frames[FrameType.Depth]
    undistorted, registered = device.registration.apply(rgb, depth)
    with open('output.pcd', 'w') as fobj:
        device.registration.write_pcd(fobj, undistorted, registered)

if __name__ == '__main__':
    main()
