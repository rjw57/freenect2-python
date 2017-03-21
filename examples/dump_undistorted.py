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
    undistorted, registered = device.registration.apply(rgb, depth)
    points_array = device.registration.get_points_xyz_array(undistorted)

    undistorted.to_image().save('undistorted_depth.tiff')
    registered.to_image().save('registered_rgb.png')
    np.savez('points.npz', points=points_array)

if __name__ == '__main__':
    main()
