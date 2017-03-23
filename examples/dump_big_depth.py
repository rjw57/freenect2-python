import json
from freenect2 import Device, FrameType
import numpy as np

def main():
    device = Device()
    frames = {}
    with device.running():
        for type_, frame in device:
            frames[type_] = frame
            if FrameType.Color in frames and FrameType.Depth in frames:
                break

    rgb, depth = frames[FrameType.Color], frames[FrameType.Depth]
    undistorted, registered, big_depth = device.registration.apply(
        rgb, depth, with_big_depth=True)

    rgb.to_image().save('output_rgb.png')
    big_depth.to_image().save('output_depth.tiff')

    with open('output_calib.json', 'w') as fobj:
        json.dump({
            'color': dict(
                (k, getattr(device.color_camera_params, k))
                for k in 'fx fy cx cy'.split()),
            'ir': dict(
                (k, getattr(device.ir_camera_params, k))
                for k in 'fx fy cx cy k1 k2 k3 p1 p2'.split()),
        }, fobj)

if __name__ == '__main__':
    main()
